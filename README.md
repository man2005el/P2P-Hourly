# Binance P2P Hourly Monitor (Vercel Serverless Function)

Sistema de monitoreo automático para el mercado P2P de Binance (**VES/USDT** y **USD/Zinli**), diseñado para ejecutarse como una función **Serverless en Vercel** y almacenar datos de precios directamente en **Google Sheets**.

---

## 🚀 Características
- **FastAPI / Serverless**: Desplegado en Vercel y listo para recibir llamadas HTTP desde [cron-job.org](https://cron-job.org/).
- **Doble Mercado en Paralelo**:
  - **Mercado VES**: Hoja `historico_p2p` (Venta: 285.000 VES / Recompra: 142.500 VES).
  - **Mercado Zinli (USD)**: Hoja `historico_p2p_zinli` (Venta: 300 USD / Recompra: 150 USD).
- **Gestión Dinámica de Pestañas**: Si la hoja `historico_p2p_zinli` no existe en el libro de Google Sheets, se crea dinámicamente con la misma estructura de cabeceras.
- **Control de Rate-Limits**: Pausas controladas (`time.sleep(1.5)`) entre peticiones a Binance P2P y escrituras en Google Sheets API.
- **Seguridad**: Autenticación mediante token exigido por parámetro de consulta (`?token=...`) o cabeceras HTTP (`Authorization: Bearer ...` / `X-Cron-Secret`).
- **Almacenamiento Persistente**: Inserción de filas capturadas en **Google Sheets** (`gspread` / `google-auth`).

---

## 🛠️ Configuración en Vercel

1. Importa este repositorio en **Vercel**.
2. En **Project Settings > Environment Variables**, agrega las siguientes variables de entorno:
   - `CRON_SECRET`: Tu contraseña/token secreto de autorización.
   - `SPREADSHEET_ID`: El ID de tu hoja de cálculo en Google Sheets.
   - `GOOGLE_SERVICE_ACCOUNT_JSON`: El contenido completo de tu archivo de credenciales de Google Service Account en formato JSON (una sola línea).

*Nota: No se requieren variables de entorno adicionales para incorporar Zinli; ambos mercados comparten el mismo ID de libro en Google Sheets.*

---

## ⏰ Configuración en cron-job.org

1. Crea una nueva tarea programada (ejemplo: cada 1 hora).
2. URL del webhook:
   ```text
   https://tu-proyecto.vercel.app/api/monitoreo?token=TU_CRON_SECRET
   ```
3. Método HTTP: `GET`.
4. Respuesta esperada del JSON:
   ```json
   {
     "status": "success",
     "timestamp": "YYYY-MM-DD HH:MM:SS",
     "ves": {"ventas": 5, "recompras": 5},
     "zinli": {"ventas": 5, "recompras": 5}
   }
   ```

---

## 🧪 Pruebas Locales

1. Copia `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```
2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta el servidor local:
   ```bash
   uvicorn api.index:app --reload
   ```
4. Realiza una petición de prueba:
   ```bash
   curl "http://127.0.0.1:8000/api/monitoreo?token=TU_CRON_SECRET"
   ```
