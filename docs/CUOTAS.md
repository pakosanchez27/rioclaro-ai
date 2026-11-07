# Cuotas de IA

## Diagnóstico local del 7 de noviembre de 2026

- Servicio: `backend/services/ai_quota.py`, función `reserve_ai_request`.
- Almacenamiento: `backend/data/rioclaro.db`, tabla SQLite `ai_usage_daily` con clave `(usage_date, operation)`.
- Antes del ajuste, `backend/local.settings.json` tenía 20 preguntas y 5 análisis por día. La base registraba 5 preguntas para `2026-11-07`. El servicio usaba un valor por defecto de 5 si el proceso no recibía la variable de entorno, lo que podía agotar la cuota aunque `local.settings.json` indicara 20.
- El día de cuota es UTC: desde `00:00:00Z` hasta el siguiente `00:00:00Z`. Para Ciudad de México en esta fecha, el reinicio corresponde a las 18:00 del 7 de noviembre.
- Tras dos verificaciones reales con preguntas ficticias, el contador local quedó en 8 de 100; el host HTTP en `127.0.0.1:7071` devolvió 200 con una fuente empresarial ficticia.

## Configuración

| Entorno | Asistente | Facturas | Almacenamiento |
|---|---|---|---|
| Desarrollo local | `DEV_MAX_DAILY_ASSISTANT_QUESTIONS=100` | `DEV_MAX_DAILY_INVOICE_ANALYSES=20` | SQLite local |
| Producción | `PROD_MAX_DAILY_ASSISTANT_QUESTIONS` | `PROD_MAX_DAILY_INVOICE_ANALYSES` | Azure Table Storage al seleccionar `STORAGE_BACKEND=table` |

`ENABLE_ASSISTANT` y `ENABLE_INVOICE_ANALYSIS` suspenden cada operación. En desarrollo se aceptan las variables antiguas `MAX_DAILY_*` solo como compatibilidad; los prefijos `DEV_` tienen prioridad. En producción las variables `PROD_` son obligatorias. Cuando existe `WEBSITE_INSTANCE_ID` (Azure Functions), SQLite se rechaza; con `STORAGE_BACKEND=table`, la reserva usa ETags y reintentos sobre una partición persistente compartida. Este proveedor solo se ha probado con un cliente falso; falta comprobarlo contra Azure real. No se ha publicado una demo ni creado recursos Azure en este cambio.

El contador se reserva antes de llamar a Azure. Una llamada fallida también consume una unidad: este criterio conservador evita reintentos ilimitados contra el servicio de pago. `BEGIN IMMEDIATE` serializa reservas concurrentes en SQLite. Las claves de contador llevan el prefijo `development:` o `production:`; el consumo anterior sin prefijo se migra al primero sin perderlo.

## Consulta y reinicio

`GET /api/assistant/quota` requiere el permiso `assistant:ask`. Solo devuelve límite, consultas restantes, estado y fecha de reinicio en UTC; no devuelve rutas, claves ni consumo de otros módulos. Al agotarse, `POST /api/assistant/ask` devuelve 429 con `Retry-After`, `resets_at` y un mensaje legible. La ruta de análisis de facturas sigue la misma pauta.

Para reiniciar solo los contadores de hoy en una instalación local de desarrollo:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\reset_local_quotas.py --confirm-local-reset --operation assistant
```

`--operation invoice_analysis` reinicia solo análisis; `--operation all` reinicia ambas. El comando lee `backend/local.settings.json` ignorado por Git, exige `DEMO_MODE=true`, entorno `Development`, ausencia de `WEBSITE_INSTANCE_ID` y una base SQLite dentro de `backend`. Solo elimina filas de cuota del día; no elimina facturas, análisis, pedidos ni datos empresariales. No hay endpoint HTTP de reinicio. El reinicio automático normal ocurre al cambiar el día UTC.

## Pruebas

`backend/tests/conftest.py` obliga a cada prueba a usar una base temporal, aun si omite su propia fixture. Las llamadas a Azure de las pruebas normales están simuladas. Se prueban límite, reserva concurrente, migración del contador antiguo, separación de entorno, reinicio manual, cambio de día, protección de Azure y cabecera 429. El reinicio real de la base de la aplicación no fue necesario para restablecer el servicio: la nueva cuota local deja margen y conserva el uso registrado.
