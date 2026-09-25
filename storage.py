import os
import json
import base64
import time
from typing import Dict, Any, List
from p2p_hourly import COLUMNAS

# Intentar importar gspread y google-auth de forma opcional/defensiva
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def obtener_cliente_gspread():
    """
    Obtiene un cliente autenticado de gspread basado en variables de entorno:
    1. GOOGLE_SERVICE_ACCOUNT_FILE (ruta a archivo .json)
    2. GOOGLE_SERVICE_ACCOUNT_JSON (string JSON completo de la Service Account)
    3. GOOGLE_CREDENTIALS_BASE64 (string JSON codificado en Base64)
    """
    if not GSPREAD_AVAILABLE:
        raise RuntimeError("Las librerías 'gspread' y 'google-auth' no están instaladas.")

    sa_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    sa_json_str = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    sa_b64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64")

    creds = None

    if sa_file and os.path.exists(sa_file):
        creds = Credentials.from_service_account_file(sa_file, scopes=SCOPES)
    elif sa_json_str:
        info = json.loads(sa_json_str)
        if "private_key" in info and isinstance(info["private_key"], str):
            info["private_key"] = info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    elif sa_b64:
        decoded_json = base64.b64decode(sa_b64).decode("utf-8")
        info = json.loads(decoded_json)
        if "private_key" in info and isinstance(info["private_key"], str):
            info["private_key"] = info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        raise ValueError(
            "No se encontraron credenciales de Google Service Account. "
            "Configura 'GOOGLE_SERVICE_ACCOUNT_FILE', 'GOOGLE_SERVICE_ACCOUNT_JSON' o 'GOOGLE_CREDENTIALS_BASE64'."
        )

    return gspread.authorize(creds)

def guardar_filas_en_hoja(sh, ws_name: str, filas: list) -> dict:
    """
    Verifica la existencia de la pestaña ws_name en la hoja de cálculo sh.
    Si no existe, la crea dinámicamente con las cabeceras de COLUMNAS.
    Inserta las filas recibidas.
    """
    if not filas:
        return {
            "status": "skipped",
            "message": f"No hay filas para guardar en {ws_name}.",
            "worksheet": ws_name,
            "filas_insertadas": 0
        }

    try:
        try:
            worksheet = sh.worksheet(ws_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=ws_name, rows=1000, cols=len(COLUMNAS))
            worksheet.append_row(COLUMNAS)  # Cabeceras si se crea dinámicamente

        try:
            primera_celda = worksheet.acell("A1").value
            if not primera_celda:
                worksheet.append_row(COLUMNAS)
        except Exception:
            pass

        worksheet.append_rows(filas)

        return {
            "status": "success",
            "worksheet": ws_name,
            "filas_insertadas": len(filas)
        }
    except Exception as e:
        return {
            "status": "error",
            "worksheet": ws_name,
            "message": str(e)
        }

def guardar_en_google_sheets(datos_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Guarda las filas capturadas en Google Sheets en dos pestañas separadas:
    - 'historico_p2p' para el mercado VES.
    - 'historico_p2p_zinli' para el mercado Zinli (USD).
    """
    if not GSPREAD_AVAILABLE:
        return {
            "status": "skipped",
            "message": "gspread no está instalado. Omitiendo guardado en Google Sheets."
        }

    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    spreadsheet_name = os.environ.get("SPREADSHEET_NAME")

    if not spreadsheet_id and not spreadsheet_name:
        return {
            "status": "skipped",
            "message": "No se ha configurado SPREADSHEET_ID ni SPREADSHEET_NAME en las variables de entorno."
        }

    # Organizar filas por mercado
    filas_ves = []
    filas_zinli = []

    if isinstance(datos_dict, dict):
        if "ves" in datos_dict and isinstance(datos_dict["ves"], dict):
            filas_ves.extend(datos_dict["ves"].get("VENTA", []))
            filas_ves.extend(datos_dict["ves"].get("RECOMPRA", []))
        
        if "zinli" in datos_dict and isinstance(datos_dict["zinli"], dict):
            filas_zinli.extend(datos_dict["zinli"].get("VENTA", []))
            filas_zinli.extend(datos_dict["zinli"].get("RECOMPRA", []))

        # Fallback si se pasa formato antiguo {"VENTA": [...], "RECOMPRA": [...]}
        if not filas_ves and not filas_zinli and ("VENTA" in datos_dict or "RECOMPRA" in datos_dict):
            filas_ves.extend(datos_dict.get("VENTA", []))
            filas_ves.extend(datos_dict.get("RECOMPRA", []))

    try:
        client = obtener_cliente_gspread()
        if spreadsheet_id:
            sh = client.open_by_key(spreadsheet_id)
        else:
            sh = client.open(spreadsheet_name)

        res_ves = guardar_filas_en_hoja(sh, "historico_p2p", filas_ves)
        
        # Pausa entre operaciones en Google Sheets para prevenir rate limit
        time.sleep(1.5)

        res_zinli = guardar_filas_en_hoja(sh, "historico_p2p_zinli", filas_zinli)

        return {
            "status": "success",
            "message": "Datos guardados exitosamente en Google Sheets.",
            "detalles": {
                "historico_p2p": res_ves,
                "historico_p2p_zinli": res_zinli
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al guardar en Google Sheets: {str(e)}"
        }
