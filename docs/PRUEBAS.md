# Pruebas y evidencia ejecutada

Fecha: 2026-11-07. Todas las pruebas Python normales usan mocks para IA y bases SQLite temporales.

| Comprobación | Resultado |
|---|---|
| Línea base `python -m pytest tests -q` | 72 aprobadas antes de V2. |
| Duplicados SHA-256, negocio y concurrencia | 8 pruebas nuevas aprobadas. |
| Catálogo, equivalencias, cinco sucursales, pedidos y política vigente | 11 pruebas nuevas aprobadas. |
| Asistente con selector Azure OpenAI simulado y respuestas fundamentadas | 5 pruebas nuevas aprobadas. |
| Quejas y reportes calculados | 4 pruebas nuevas aprobadas. |
| Rutas V2: estadísticas, reportes y validación de quejas | 3 pruebas nuevas aprobadas. |
| Suite final `python -m pytest tests -q` | **110 aprobadas**. |
| Suite completa `python -m pytest -q` (incluye `scripts/`) | **113 aprobadas**. |
| Frontend `npm test` | **8 aprobadas en 4 archivos**: formato, listado, carga de factura y chat. |
| `npm run build` y `npm run lint` | Correctos tras integrar las nuevas pantallas. |
| Host Azure Functions local en puerto 7072 | Inició con entorno virtual; rutas registradas. GET `/business/options`: 200, 5 sucursales y 3 pedidos. GET `/business/reports`: 200, 5 sucursales. GET `/invoices`: 200, 5 facturas. |
| GET `/invoices/stats` en host real | Inicialmente 404 por colisión con ruta parametrizada; corregido y repetido: 200, total 5, pendientes 2, validadas 3. |
| `npm audit --omit=dev --json` | 0 vulnerabilidades de dependencias de producción; 10 moderadas en herramientas de desarrollo al incluir devDependencies. |
| `npm audit fix` | No encontró corrección compatible; propone `--force` con cambio mayor de ESLint. No se forzó la actualización. |
| Emulación móvil con Chrome DevTools Protocol | Asistente y quejas a 390 px: `viewport=390`, `scrollWidth=390`, sin desbordamiento horizontal; capturas locales guardadas. |

Los números de facturas y ventas pertenecen solo a la base ficticia local. Ninguna prueba automatizada consumió Azure OpenAI ni Document Intelligence. No se probó una factura real con los recursos Azure en esta iteración. No se probó persistencia en una Function App publicada.

El host local en 7072 informó `azure.functions.webjobs.storage: Unhealthy` porque no había Azurite para `AzureWebJobsStorage=UseDevelopmentStorage=true`; las rutas HTTP probadas sí respondieron. El primer intento de `func start` fuera del entorno virtual falló por falta de `azure.core` y el puerto 7071 ya estaba ocupado. El segundo intento activó `.venv` y usó el puerto 7072.

## Casos todavía pendientes

- Prueba con teléfono físico, lector de pantalla y teclado completo.
- Documento borroso/incompleto con respuesta real de Document Intelligence y almacenamiento parcial.
- Reintentos y fallo temporal real de Azure.
- Pruebas de integración contra Azure con consumo autorizado.
- Concurrencia y cuotas en almacenamiento Azure compartido.
- Respuesta de voz Azure Speech.
- Comprobación externa desde URL pública y reinicio del servicio.
