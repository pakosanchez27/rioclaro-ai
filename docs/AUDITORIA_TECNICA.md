# Auditoría técnica — Río Claro AI V2

Fecha: 2026-11-07. Rama: `feature/rioclaro-v2`.

## Línea base verificada

- Git partía de `main` con dos cambios previos sin guardar: `backend/scripts/test_azure_openai.py` y `backend/tests/test_auth_middleware_demo.py`. Se conservaron al crear la rama.
- `python -m pytest tests -q` desde `backend`: **72 pruebas aprobadas** al inicio.
- `npm run build` desde `frontend`: correcto al inicio.
- Los archivos `local.settings.json`, bases `.db`, entornos virtuales y `node_modules` están ignorados. `git ls-files` no mostró estos archivos.
- El `.gitignore` raíz y el `README.md` contenían texto de comandos PowerShell en lugar de contenido Markdown/Gitignore limpio; se repararon.

## Arquitectura encontrada

- Azure Functions Python v2 con rutas de salud, facturas, estadísticas, análisis, revisión e historial.
- Persistencia SQLite con repositorios para facturas, análisis y revisiones. `invoice_analyses` guarda JSON de extracción y análisis. El documento original no se conserva.
- React con Vite, TanStack Query, Axios y rutas para dashboard, facturas, detalle y análisis.
- JWT de Entra valida firma RS256, audiencia, emisor, tenant, versión, vencimiento y roles. El modo local `DEMO_MODE` se limita a Development sin `WEBSITE_INSTANCE_ID`.
- El backend usa Document Intelligence `prebuilt-invoice` y Azure OpenAI con despliegue configurable.

## Recursos de Azure comprobados sin crear ni modificar recursos

- Suscripción activa: Azure for Students.
- Grupo `rg-rioclaro-ai-dev`: `openai-rioclaro-dev` (OpenAI, S0, Central US, estado Succeeded) y `docint-rioclaro-dev` (FormRecognizer, F0, Central US, estado Succeeded).
- Despliegue `gpt-rioclaro`: `gpt-5-mini`, versión `2025-08-07`, capacidad 1.
- No se encontró Storage Account, Function App, Static Web App ni recurso Speech en ese grupo.
- Proveedores `Microsoft.Web` y `Microsoft.Storage`: estado inicial `NotRegistered`. Actualización 2026-11-07: figuran `Registered`; el registro de actividad muestra acciones de registro a las 08:04 UTC, sin identificar el comando que las inició.
- `az consumption budget list` no mostró presupuestos en la suscripción consultada; el comando está en vista previa. No se confirmó un límite de gasto efectivo.

## Hallazgos y decisiones

1. **Persistencia en nube:** SQLite local no es una base compartida ni durable entre instancias de Azure Functions. Se conserva para desarrollo; el despliegue queda bloqueado hasta implementar y verificar una capa persistente Azure para todos los repositorios y cuotas.
2. **Demo pública:** el bypass local no se publica. La cuota SQLite es atómica para la instancia/base local, pero no satisface por sí sola el requisito de cuota compartida en Azure. No hay URL pública.
3. **Documentos duplicados:** antes no había hash ni clasificación de duplicados de negocio. Se añadió reserva SHA-256 atómica, detección determinista y aviso de posibles duplicados. La reserva de un proceso interrumpido puede quedar en `processing`; requiere recuperación supervisada antes de uso público.
4. **OCR incompleto:** el pipeline rechaza importes o proveedor ausentes en vez de inventarlos. Todavía no conserva extracción parcial para revisión manual.
5. **Asistente:** se añadió selección de consulta por Azure OpenAI y respuesta construida solo desde filas ficticias verificables. No se devuelven afirmaciones empresariales generadas libremente por el modelo. El historial visual es de sesión; referencias conversacionales complejas aún no se resuelven.
6. **Tiempo de análisis:** el endpoint es síncrono y Axios espera 180 segundos. [Microsoft documenta un máximo de 230 segundos para respuestas HTTP de Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale); un procesamiento prolongado requerirá cola y estado antes de publicación.
7. **Voz:** no existe recurso Azure AI Speech en el grupo. El botón muestra indisponibilidad y no simula voz.
8. **Frontend:** rutas vacías de revisiones, historial y configuración dejaron de aparecer en navegación; las acciones de revisión y el historial reales están en el detalle de factura.
9. **Secretos:** no se encontraron archivos de claves rastreados en Git. Los valores locales se conservaron en archivos ignorados. Se añadieron ejemplos sin secretos.
10. **Host local:** iniciar `func start` fuera de `.venv` falló por `azure.core` ausente; con `.venv` inició en 7072. Sin Azurite, `AzureWebJobsStorage` informó estado no saludable aunque las rutas HTTP respondieron.
11. **Rutas:** el host resolvió `/invoices/stats` mediante la ruta de detalle parametrizada y devolvió 404. Se añadió una derivación explícita a `invoices_stats`; la verificación HTTP posterior devolvió 200.

## Resultado tras cambios

Ver `PRUEBAS.md` para comandos y resultados finales. No se ejecutaron llamadas reales a Document Intelligence ni Azure OpenAI durante las pruebas automatizadas.
