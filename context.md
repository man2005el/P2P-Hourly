Contexto del Proyecto: Monitor de Arbitraje P2P (VES/USDT en Binance)
1. Resumen Ejecutivo y Objetivo
El objetivo de este proyecto es implementar un sistema de monitoreo y registro automatizado para el mercado Peer-to-Peer (P2P) de Binance en el par Bolívares venezolanos (VES) y Tether (USDT).
El fin último es capturar datos históricos de precios con frecuencia horaria para identificar patrones temporales, picos y valles de liquidez a lo largo del día y de la semana. Con esta información se busca optimizar una estrategia de arbitraje financiero como creador de mercado (maker).

2. Modelo de Negocio / Estrategia de Arbitraje (Maker vs. Taker)
En Binance P2P, quien publica anuncios actúa como maker (creador de liquidez) y quien toma las órdenes actúa como taker:
Venta de USDT (Salida a moneda fiat - VES):
El comerciante publica un anuncio de venta de USDT.
En la interfaz de Binance, los usuarios regulares (takers) ven este anuncio en la pestaña "Comprar" (Buy).
Monto objetivo de monitoreo: Transacciones medianas/grandes equivalentes a 48.000 VES (aprox. 50–100 USD según tasa de mercado).
Objetivo táctico: Vender USDT al precio más alto posible (e.g., 960 – 970 VES/USDT), típicamente aprovechando picos de demanda o escasez de oferta en horarios no bancarios / madrugada.
Recompra de USDT (Entrada de liquidez USDT con VES):
El comerciante publica un anuncio de compra de USDT.
En la interfaz de Binance, los usuarios regulares (takers) ven este anuncio en la pestaña "Vender" (Sell).
Monto objetivo de monitoreo: Transacciones al detal de 10.000 VES (aprox. 10 USD).
Objetivo táctico: Recomprar USDT al precio más bajo posible (e.g., 940 – 951 VES/USDT) absorbiendo órdenes pequeñas vía Pago Móvil.
Margen (Spread):
Margen Bruto = Precio Venta (48k VES) - Precio Recompra (10k VES)
Rendimiento porcentual neto descontando las comisiones de comerciante de Binance P2P (típicamente entre 0% y 0.35%).

3. Arquitectura y Funcionamiento del Script (monitor_p2p.py)
El script interactúa directamente con el endpoint interno de Binance P2P mediante solicitudes HTTP POST:
Endpoint: https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search
Filtros aplicados por petición:
asset: "USDT"
fiat: "VES"
page: 1
rows: 5 (extrae el Top 5 de anuncios más competitivos)
transAmount: 48.000 para tradeType="BUY" / 10.000 para tradeType="SELL"
payTypes: ["Banesco"] (filtra únicamente ofertas que acepten Banesco)
Almacenamiento y Salida de Datos:
Los datos se almacenan en dos archivos CSV independientes para facilitar el análisis comparativo:
ventas_48k.csv: Registra los 5 mejores anuncios para colocación de venta.
recompras_10k.csv: Registra los 5 mejores anuncios para recompra al detal.
Esquema de Datos Registrado:
timestamp: Fecha y hora de captura (YYYY-MM-DD HH:MM:SS).
posicion: Rango del anuncio en el libro de órdenes (1 al 5).
comerciante: Nickname del anunciante.
precio_ves: Tasa ofertada en VES por USDT.
disponible_usdt: Cantidad de USDT disponible en la orden.
limite_min_ves: Monto mínimo en bolívares aceptado por el comerciante.
limite_max_ves: Monto máximo en bolívares aceptado por el comerciante.
metodos_pago: Lista de métodos bancarios soportados (Pago Móvil, Banesco, Banco de Venezuela, etc.).
ordenes_mes: Número de órdenes completadas por el comerciante en los últimos 30 días.
tasa_finalizacion_pct: Porcentaje de órdenes exitosas del comerciante.

4. Ejecución y Automatización
Frecuencia esperada: Ejecución automática cada hora (ej. minuto 00: 0 * * * *).
Mecanismos soportados:
Crontab de Linux / VPS / WSL.
Windows Task Scheduler.
Demonio en segundo plano con bucle temporal (time.sleep(3600)).

5. Próximos Pasos para Antigravity
Validación y Resiliencia: Añadir manejo de reintentos con backoff exponencial y rotación de cabeceras/proxies si Binance limita la tasa de peticiones (rate limiting).
Dashboard / Análisis: Procesar los CSV generados con Pandas para calcular métricas como:
Media móvil horaria de la tasa de compra y venta.
Spread promedio por hora del día (mapa de calor de 00:00 a 23:00).
Detección automática de anomalías y alertas cuando el margen supere un umbral (e.g. > 1.5%).
