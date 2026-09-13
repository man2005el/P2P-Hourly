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

# Configuración de montos y tipos de operaciones
CONFIG = {
    "VENTA": {
        "operacion": "VENTA_48K",
        "trade_type": "BUY",      # El usuario compra USDT (tú vendes)
        "amount": 48000,
        "filename": "ventas_48k.csv",
        "worksheet_name": "historico_p2p",
        "pay_types": ["Banesco"]
    },
    "RECOMPRA": {
        "operacion": "RECOMPRA_10K",
        "trade_type": "SELL",     # El usuario vende USDT (tú recompras)
        "amount": 10000,
        "filename": "recompras_10k.csv",
        "worksheet_name": "historico_p2p",
        "pay_types": ["Banesco"]
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

def consultar_anuncios(trade_type: str, amount_ves: float, rows: int = 5, pay_types: list = None):
    """Consulta la API de Binance P2P para un tipo de operación, monto y métodos de pago específicos."""
    if pay_types is None:
        pay_types = ["Banesco"]

    payload = {
        "asset": "USDT",
        "fiat": "VES",
        "tradeType": trade_type,
        "transAmount": amount_ves,
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
        print(f"[{datetime.now(ZoneInfo('America/Caracas'))}] Error consultando {trade_type} ({amount_ves} VES): {e}")
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
    Ejecuta las consultas P2P para VENTA y RECOMPRA y retorna un diccionario con las filas capturadas.
    """
    if not timestamp_actual:
        timestamp_actual = datetime.now(ZoneInfo("America/Caracas")).strftime("%Y-%m-%d %H:%M:%S")

    resultados = {
        "timestamp": timestamp_actual,
        "datos": {},
        "resumen": {}
    }

    # Captura VENTA (48k)
    anuncios_venta = consultar_anuncios(
        CONFIG["VENTA"]["trade_type"],
        CONFIG["VENTA"]["amount"],
        rows=5,
        pay_types=CONFIG["VENTA"]["pay_types"]
    )
    filas_venta = extraer_filas_anuncios(
        anuncios_venta,
        timestamp_actual,
        CONFIG["VENTA"]["operacion"],
        CONFIG["VENTA"]["trade_type"]
    )
    resultados["datos"]["VENTA"] = filas_venta
    resultados["resumen"]["VENTA_count"] = len(filas_venta)

    # Captura RECOMPRA (10k)
    anuncios_recompra = consultar_anuncios(
        CONFIG["RECOMPRA"]["trade_type"],
        CONFIG["RECOMPRA"]["amount"],
        rows=5,
        pay_types=CONFIG["RECOMPRA"]["pay_types"]
    )
    filas_recompra = extraer_filas_anuncios(
        anuncios_recompra,
        timestamp_actual,
        CONFIG["RECOMPRA"]["operacion"],
        CONFIG["RECOMPRA"]["trade_type"]
    )
    resultados["datos"]["RECOMPRA"] = filas_recompra
    resultados["resumen"]["RECOMPRA_count"] = len(filas_recompra)

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
    
    guardar_csv_local(CONFIG["VENTA"]["filename"], res["datos"]["VENTA"])
    print(f"[{ts}] Guardados {len(res['datos']['VENTA'])} anuncios en {CONFIG['VENTA']['filename']}")
    
    guardar_csv_local(CONFIG["RECOMPRA"]["filename"], res["datos"]["RECOMPRA"])
    print(f"[{ts}] Guardados {len(res['datos']['RECOMPRA'])} anuncios en {CONFIG['RECOMPRA']['filename']}")

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
