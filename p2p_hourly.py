import os
import csv
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

URL_API = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "*/*"
}

# Configuración de mercados, montos y tipos de operaciones
CONFIG = {
    "VES": {
        "worksheet_name": "historico_p2p",
        "filename": "historico_p2p.csv",
        "VENTA": {
            "operacion": "VENTA",
            "fiat": "VES",
            "trade_type": "BUY",      # El usuario compra USDT (tú vendes)
            "amount": 285000,          # 30% de 950.000 VES
            "pay_types": [],
            "rows": 5
        },
        "RECOMPRA": {
            "operacion": "RECOMPRA",
            "fiat": "VES",
            "trade_type": "SELL",     # El usuario vende USDT (tú recompras)
            "amount": 142500,          # 15% de 950.000 VES
            "pay_types": [],
            "rows": 5
        }
    },
    "ZINLI": {
        "worksheet_name": "historico_p2p_zinli",
        "filename": "historico_p2p_zinli.csv",
        "VENTA": {
            "operacion": "VENTA",
            "fiat": "USD",
            "trade_type": "BUY",      # El usuario compra USDT (tú vendes)
            "amount": 300,             # 30% de 1.000 USD
            "pay_types": ["Zinli"],
            "rows": 5
        },
        "RECOMPRA": {
            "operacion": "RECOMPRA",
            "fiat": "USD",
            "trade_type": "SELL",     # El usuario vende USDT (tú recompras)
            "amount": 150,             # 15% de 1.000 USD
            "pay_types": ["Zinli"],
            "rows": 5
        }
    }
}

COLUMNAS = [
    "timestamp",
    "operacion",
    "trade_type",
    "posicion",
    "comerciante",
    "precio_ves",
    "disponible_usdt",
    "limite_min_ves",
    "limite_max_ves",
    "metodos_pago",
    "ordenes_mes",
    "tasa_finalizacion_pct"
]

def consultar_anuncios(fiat: str, trade_type: str, amount: float, rows: int = 5, pay_types: list = None):
    """Consulta la API de Binance P2P para un mercado (fiat), tipo de operación, monto y métodos de pago específicos."""
    if pay_types is None:
        pay_types = []

    payload = {
        "asset": "USDT",
        "fiat": fiat,
        "tradeType": trade_type,
        "transAmount": amount,
        "page": 1,
        "rows": rows,
        "payTypes": pay_types,
        "publisherType": None
    }
    
    try:
        response = requests.post(URL_API, json=payload, headers=HEADERS, timeout=12)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"[{datetime.now(ZoneInfo('America/Caracas'))}] Error consultando {fiat} {trade_type} ({amount}): {e}")
        return []

def extraer_filas_anuncios(anuncios: list, timestamp_actual: str, tipo_operacion: str, trade_type: str) -> list:
    """Transforma la respuesta cruda de Binance en una lista de filas estructuradas según COLUMNAS."""
    filas = []
    for idx, item in enumerate(anuncios, start=1):
        adv = item.get("adv", {})
        user = item.get("advertiser", {})
        
        metodos = [m.get("tradeMethodName", "") for m in adv.get("tradeMethods", [])]
        metodos_str = " | ".join(filter(None, metodos))
        
        precio = float(adv.get("price", 0)) if adv.get("price") is not None else 0.0
        disponible = float(adv.get("surplusAmount", 0)) if adv.get("surplusAmount") is not None else 0.0
        lim_min = float(adv.get("minSingleTransAmount", 0)) if adv.get("minSingleTransAmount") is not None else 0.0
        lim_max = float(adv.get("maxSingleTransAmount", 0)) if adv.get("maxSingleTransAmount") is not None else 0.0
        
        tasa_fin = round(float(user.get("monthFinishRate", 0)) * 100, 2)
        
        fila = [
            timestamp_actual,
            tipo_operacion,
            trade_type,
            idx,
            user.get("nickName", "Desconocido"),
            precio,
            disponible,
            lim_min,
            lim_max,
            metodos_str,
            int(user.get("monthOrderCount", 0)),
            tasa_fin
        ]
        filas.append(fila)
    return filas

def capturar_datos_p2p(timestamp_actual: str = None) -> dict:
    """
    Ejecuta las consultas P2P para VENTA y RECOMPRA en el mercado VES y el mercado Zinli (USD),
    con una pausa de 1.5s entre peticiones Binance para evitar rate-limits.
    """
    if not timestamp_actual:
        timestamp_actual = datetime.now(ZoneInfo("America/Caracas")).strftime("%Y-%m-%d %H:%M:%S")

    resultados = {
        "timestamp": timestamp_actual,
        "datos": {
            "ves": {
                "VENTA": [],
                "RECOMPRA": []
            },
            "zinli": {
                "VENTA": [],
                "RECOMPRA": []
            }
        },
        "resumen": {
            "ves": {"ventas": 0, "recompras": 0},
            "zinli": {"ventas": 0, "recompras": 0}
        }
    }

    # --- Mercado 1: VES ---
    # Venta VES
    cfg_ves_v = CONFIG["VES"]["VENTA"]
    anuncios_ves_v = consultar_anuncios(
        fiat=cfg_ves_v["fiat"],
        trade_type=cfg_ves_v["trade_type"],
        amount=cfg_ves_v["amount"],
        rows=cfg_ves_v["rows"],
        pay_types=cfg_ves_v["pay_types"]
    )
    filas_ves_v = extraer_filas_anuncios(anuncios_ves_v, timestamp_actual, cfg_ves_v["operacion"], cfg_ves_v["trade_type"])
    resultados["datos"]["ves"]["VENTA"] = filas_ves_v
    resultados["resumen"]["ves"]["ventas"] = len(filas_ves_v)

    time.sleep(1.5)

    # Recompra VES
    cfg_ves_r = CONFIG["VES"]["RECOMPRA"]
    anuncios_ves_r = consultar_anuncios(
        fiat=cfg_ves_r["fiat"],
        trade_type=cfg_ves_r["trade_type"],
        amount=cfg_ves_r["amount"],
        rows=cfg_ves_r["rows"],
        pay_types=cfg_ves_r["pay_types"]
    )
    filas_ves_r = extraer_filas_anuncios(anuncios_ves_r, timestamp_actual, cfg_ves_r["operacion"], cfg_ves_r["trade_type"])
    resultados["datos"]["ves"]["RECOMPRA"] = filas_ves_r
    resultados["resumen"]["ves"]["recompras"] = len(filas_ves_r)

    time.sleep(1.5)

    # --- Mercado 2: USD (Zinli) ---
    # Venta Zinli
    cfg_zin_v = CONFIG["ZINLI"]["VENTA"]
    anuncios_zin_v = consultar_anuncios(
        fiat=cfg_zin_v["fiat"],
        trade_type=cfg_zin_v["trade_type"],
        amount=cfg_zin_v["amount"],
        rows=cfg_zin_v["rows"],
        pay_types=cfg_zin_v["pay_types"]
    )
    filas_zin_v = extraer_filas_anuncios(anuncios_zin_v, timestamp_actual, cfg_zin_v["operacion"], cfg_zin_v["trade_type"])
    resultados["datos"]["zinli"]["VENTA"] = filas_zin_v
    resultados["resumen"]["zinli"]["ventas"] = len(filas_zin_v)

    time.sleep(1.5)

    # Recompra Zinli
    cfg_zin_r = CONFIG["ZINLI"]["RECOMPRA"]
    anuncios_zin_r = consultar_anuncios(
        fiat=cfg_zin_r["fiat"],
        trade_type=cfg_zin_r["trade_type"],
        amount=cfg_zin_r["amount"],
        rows=cfg_zin_r["rows"],
        pay_types=cfg_zin_r["pay_types"]
    )
    filas_zin_r = extraer_filas_anuncios(anuncios_zin_r, timestamp_actual, cfg_zin_r["operacion"], cfg_zin_r["trade_type"])
    resultados["datos"]["zinli"]["RECOMPRA"] = filas_zin_r
    resultados["resumen"]["zinli"]["recompras"] = len(filas_zin_r)

    return resultados

def inicializar_csv_local(filename: str):
    """Crea el archivo CSV local con cabeceras si aún no existe."""
    if not os.path.exists(filename):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNAS)

def guardar_csv_local(filename: str, filas: list):
    """Guarda las filas en un archivo CSV local."""
    if not filas:
        return
    inicializar_csv_local(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(filas)

def ejecutar_captura_local():
    """Ejecución local por línea de comandos (guarda en archivos CSV locales)."""
    ts = datetime.now(ZoneInfo("America/Caracas")).strftime("%Y-%m-%d %H:%M:%S")
    res = capturar_datos_p2p(ts)
    
    filas_ves = res["datos"]["ves"]["VENTA"] + res["datos"]["ves"]["RECOMPRA"]
    guardar_csv_local(CONFIG["VES"]["filename"], filas_ves)
    print(f"[{ts}] Guardados {len(filas_ves)} anuncios VES en {CONFIG['VES']['filename']}")
    
    filas_zinli = res["datos"]["zinli"]["VENTA"] + res["datos"]["zinli"]["RECOMPRA"]
    guardar_csv_local(CONFIG["ZINLI"]["filename"], filas_zinli)
    print(f"[{ts}] Guardados {len(filas_zinli)} anuncios Zinli en {CONFIG['ZINLI']['filename']}")

if __name__ == "__main__":
    import sys
    if "--loop" in sys.argv:
        intervalo = 300
        for i, arg in enumerate(sys.argv):
            if arg == "--loop" and i + 1 < len(sys.argv) and sys.argv[i + 1].isdigit():
                intervalo = int(sys.argv[i + 1])
        
        minutos = intervalo // 60 if intervalo >= 60 else round(intervalo / 60, 2)
        print(f"[{datetime.now(ZoneInfo('America/Caracas'))}] Iniciando ejecucion continua cada {minutos} min ({intervalo} s). Presiona Ctrl+C para salir.")
        while True:
            ejecutar_captura_local()
            print(f"[{datetime.now(ZoneInfo('America/Caracas'))}] Proxima captura en {minutos} min. Esperando...\n")
            time.sleep(intervalo)
    else:
        ejecutar_captura_local()
