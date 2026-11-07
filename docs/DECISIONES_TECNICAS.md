# Decisiones técnicas

1. **Conservar SQLite local.** Evita reconstruir los repositorios ya funcionales. No se considera opción de persistencia en Functions desplegada.
2. **No activar `DEMO_MODE` en Azure.** El middleware lo rechaza cuando detecta entorno desplegado. No se deshabilita el JWT de Entra.
3. **Duplicados en dos momentos.** SHA-256 antes de IA evita reprocesar archivos idénticos; tras la extracción se comparan campos de negocio. Coincidencias aproximadas se marcan para revisión humana.
4. **IA acotada.** GPT-5 mini selecciona una consulta de un conjunto fijo. La respuesta empresarial se construye desde SQLite, con ID y fecha de la fuente. Una selección inválida falla de forma cerrada.
5. **Cuota consumida antes de IA.** Una llamada fallida cuenta porque el proveedor pudo haberla procesado. SQLite serializa incrementos locales; falta equivalente compartido para nube.
6. **Datos ficticios visibles.** Seed idempotente y etiquetas en interfaz; no se confunden métricas de ejemplo con datos reales.
7. **Voz pendiente.** No se simulan transcripciones mientras no exista Azure AI Speech configurado y aprobado para consumo.
8. **Publicación diferida.** No hay almacenamiento cloud, Function App ni Static Web App; tampoco autorización para crear recursos de pago o publicar. Se prepara documentación sin afirmar URL pública.
