# Binance P2P Hourly Monitor (Vercel Serverless Function)

Sistema de monitoreo automático para el mercado P2P de Binance (VES/USDT), diseñado para ejecutarse como una función **Serverless en Vercel** y almacenar datos de precios directamente en **Google Sheets**.

---

## 🚀 Características
- **FastAPI / Serverless**: Desplegado en Vercel y listo para recibir llamadas HTTP desde [cron-job.org](https://cron-job.org/).
- **Seguridad**: Autenticación mediante token exigido por parámetro de consulta (`?token=...`) o cabeceras HTTP (`Authorization: Bearer ...` / `X-Cron-Secret`).
- **Almacenamiento Persistente**: Inserción de filas capturadas en **Google Sheets** (`gspread` / `google-auth`).
- **Filtros Personalizados**: Registra el Top 5 de anuncios para **Venta (48.000 VES)** y **Recompra (10.000 VES)** en Banesco / Pago Móvil.

---

## 🛠️ Configuración en Vercel

1. Importa este repositorio en **Vercel**.
2. En **Project Settings > Environment Variables**, agrega las siguientes variables de entorno:
   - `CRON_SECRET`: Tu contraseña/token secreto de autorización.
   - `SPREADSHEET_ID`: El ID de tu hoja de cálculo en Google Sheets.
   - `GOOGLE_SERVICE_ACCOUNT_JSON`: El contenido completo de tu archivo de credenciales de Google Service Account en formato JSON (una sola línea).

---

## ⏰ Configuración en cron-job.org

1. Crea una nueva tarea programada (ejemplo: cada 1 hora).
2. URL del webhook:
   ```text
   https://tu-proyecto.vercel.app/api/monitoreo?token=TU_CRON_SECRET
   ```
3. Método HTTP: `GET`.

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
