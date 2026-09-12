import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Security, Depends, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

from p2p_hourly import capturar_datos_p2p
from storage import guardar_en_google_sheets

app = FastAPI(
    title="Binance P2P Hourly Monitor API",
    description="API Serverless para monitoreo de arbitraje P2P Binance y persistencia en Google Sheets",
    version="1.0.0"
)

security_bearer = HTTPBearer(auto_error=False)

def verificar_cron_secret(
    request: Request,
    token: Optional[str] = Query(None, description="Token de autenticación de cron-job.org"),
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
):
    cron_secret = os.environ.get("CRON_SECRET")
    
    if not cron_secret:
        raise HTTPException(
            status_code=500,
            detail="La variable de entorno CRON_SECRET no ha sido configurada en el servidor."
        )

    provided_token = None

    if token:
        provided_token = token
    elif auth and auth.credentials:
        provided_token = auth.credentials
    elif "x-cron-secret" in request.headers:
        provided_token = request.headers.get("x-cron-secret")
    elif "authorization" in request.headers:
        raw_auth = request.headers.get("authorization", "")
        if raw_auth.startswith("Bearer "):
            provided_token = raw_auth[7:]
        else:
            provided_token = raw_auth

    if not provided_token or provided_token != cron_secret:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Token de seguridad no válido o ausente."
        )

    return True

@app.get("/")
@app.get("/api")
@app.get("/api/monitoreo")
@app.get("/monitoreo")
@app.get("/api/index")
@app.get("/api/index.py")
def ejecutar_monitoreo(request: Request, authorized: bool = Depends(verificar_cron_secret)):
    """
    Endpoint principal disparado por cron-job.org.
    Requiere autenticación mediante token.
    Captura precios de Venta (48k) y Recompra (10k) en Binance P2P y los almacena en Google Sheets.
    """
    try:
        captura = capturar_datos_p2p()
        sheets_res = guardar_en_google_sheets(captura["datos"])

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "path_received": request.url.path,
                "timestamp": captura["timestamp"],
                "resumen": captura["resumen"],
                "almacenamiento": sheets_res,
                "datos": captura["datos"]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error durante la ejecución del monitoreo: {str(e)}"
        )
