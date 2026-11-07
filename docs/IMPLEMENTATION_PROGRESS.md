# Progreso de implementación

Actualizado: 2026-11-07. Estados: Completada, En desarrollo, Pendiente, Bloqueada.

| Épica | Estado | Evidencia y próximo paso |
|---|---|---|
| E00 Auditoría | Completada | Línea base, rama, secretos ignorados, rutas y pruebas en `AUDITORIA_TECNICA.md`. |
| E01 Infraestructura pública | En desarrollo | Adaptador Azure Tables y scripts listos; sin recursos creados ni verificación real de persistencia. |
| E02 Facturas y duplicados | En desarrollo | SHA-256, conflicto 409, coincidencia de negocio y posible coincidencia, pruebas concurrentes. Falta OCR parcial, recuperación de reservas y equivalencia visual robusta PDF/imagen. |
| E03 Datos empresariales | En desarrollo | Semilla idempotente y migración SQLite a Tables preparadas; falta prueba real de Azure. |
| E04 Asistente | En desarrollo | Selección acotada por Azure OpenAI; consulta local real del 7-11-2026 devolvió HTTP 200 con fuente. Cuota visible en React. Falta ampliar diálogo contextual. |
| E05 Voz, quejas, reportes | En desarrollo | Quejas con folio y reportes calculados. Voz bloqueada por ausencia de Azure AI Speech. |
| E06 IA responsable y consumo | En desarrollo | Cuotas por entorno y contador compartido sobre Azure Tables probados con cliente falso; falta prueba real y modalidad pública segura. |
| E07 UX | En desarrollo | Pantallas responsivas; emulación CDP a 390 px sin desbordamiento en asistente y quejas. Faltan pruebas físicas y de accesibilidad completas. |
| E08 Pruebas | En desarrollo | 123 pruebas Python y 8 frontend pasaron; `npm run build` correcto. Falta integración Azure real. |
| E09 Publicación | Bloqueada | Scripts preparados; faltan autorización de recursos, prueba real de Storage y modalidad pública segura. No hay URL. |
| E10 Documentación | En desarrollo | Auditoría, arquitectura, decisiones, pruebas, despliegue y entrega Markdown. Faltan capturas reales de URL pública. |

## Cambios principales

- Backend: esquema, repositorios empresariales y quejas, seed, detector de duplicados, cuota, asistente y rutas nuevas.
- Frontend: asistente, pedidos/quejas, reportes, avisos de duplicados y URL de API por entorno.
- Documentación: ejemplos de configuración, auditoría, decisiones y guía de despliegue.

## Validación

Al cierre de esta etapa pasaron 123 pruebas Python, 8 pruebas frontend y `npm run build`. Azure Table Storage sigue sin prueba real.


## Ajuste de cuota del asistente (2026-11-07)

- Completada: separar límites de desarrollo/producción, preservar contadores previos, consultar cuota restante y mostrarla en React.
- Completada: respuesta 429 con `Retry-After` y reinicio UTC; reinicio local de solo cuotas mediante script, probado con base temporal.
- Completada: aislar todas las pruebas Python de la base de la aplicación. 123 pruebas Python y 8 frontend pasaron; `npm run build` pasó.
- Verificación local: la ruta directa y el host HTTP respondieron 200 a preguntas ficticias con una fuente; quedaron 92 de 100 consultas después. Detalle en `docs/CUOTAS.md`.

## Preparación de Azure Tables (2026-11-07)

- Completada en código: proveedor configurable SQLite/Table Storage, ETags y transacciones de una partición para facturas, análisis, revisiones, duplicados, catálogo, pedidos, políticas, quejas y cuotas.
- Completada en código: migración segura de SQLite y semillas idempotentes; scripts PowerShell de preflight, provisión, seed y preview autenticado. No se ejecutaron los scripts de creación.
- Completada: frontend acepta URL de API HTTPS y conserva proxy local.
- Completada: 123 pruebas Python y 8 frontend pasaron; `npm run build` pasó. Ocho pruebas del adaptador usan cliente falso, sin Azure real.
- Bloqueada: prueba real de Azure Tables, persistencia tras reinicio, disponibilidad efectiva del SKU y publicación. Requiere autorización de recursos y una modalidad pública segura sin login.
