@echo off
cd /d "%~dp0"
echo Monitor P2P Binance - Ejecucion continua cada 5 minutos...
.venv\Scripts\python.exe p2p_hourly.py --loop
