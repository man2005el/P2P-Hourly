import os
import json
import base64
from typing import Dict, Any, List
from p2p_hourly import COLUMNAS, CONFIG

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

def guardar_en_google_sheets(datos_dict: Dict[str, List[List[Any]]]) -> Dict[str, Any]:
    """
    Guarda las filas capturadas en Google Sheets en una sola pestaña unificada ("historico_p2p").
    `datos_dict` contiene las claves 'VENTA' y 'RECOMPRA' con listas de filas.
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

    # Concatenar todas las filas de VENTA y RECOMPRA en una sola lista plana
    filas_totales = []
    if isinstance(datos_dict, dict):
        for tipo in ["VENTA", "RECOMPRA"]:
            filas_totales.extend(datos_dict.get(tipo, []))
    elif isinstance(datos_dict, list):
        filas_totales = datos_dict

    if not filas_totales:
        return {
            "status": "skipped",
            "message": "No hay filas para guardar en Google Sheets."
        }

    ws_name = "historico_p2p"

    try:
        client = obtener_cliente_gspread()
        if spreadsheet_id:
            sh = client.open_by_key(spreadsheet_id)
        else:
            sh = client.open(spreadsheet_name)

        # Intentar obtener la pestaña o crearla si no existe
        try:
            worksheet = sh.worksheet(ws_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=ws_name, rows=1000, cols=len(COLUMNAS))
            worksheet.append_row(COLUMNAS)  # Escribir cabeceras si se crea desde cero

        # Lectura ligera de la celda A1 para verificar cabecera sin traer miles de filas
        try:
            primera_celda = worksheet.acell("A1").value
            if not primera_celda:
                worksheet.append_row(COLUMNAS)
        except Exception:
            pass

        # Inserción eficiente en bloque (una sola llamada HTTP a Google Sheets API)
        worksheet.append_rows(filas_totales)

        return {
            "status": "success",
            "message": "Datos guardados exitosamente en Google Sheets.",
            "detalles": {
                "worksheet": ws_name,
                "filas_insertadas": len(filas_totales),
                "status": "success"
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al guardar en Google Sheets: {str(e)}"
        }
