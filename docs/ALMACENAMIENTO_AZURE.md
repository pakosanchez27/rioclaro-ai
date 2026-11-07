# Preparación de almacenamiento persistente

Estado al 7 de noviembre de 2026: **implementado en código y probado con cliente Azure Tables falso; no verificado contra Azure real**. No se crearon recursos ni se publicó la aplicación.

## Auditoría del código existente

No había `TableServiceClient`, `BlobServiceClient` ni proveedor alternativo. `backend/database/connection.py` abría un archivo SQLite y `schema.sql` definía todas las tablas. Todas las rutas de Azure Functions llegan a los repositorios y servicios siguientes:

| Datos | Escritura y lectura | Dependencia SQL |
|---|---|---|
| Facturas | `repositories/invoices.py`, `services/invoice_pipeline.py`, `seed_demo.py` | Orden por fecha, paginación `LIMIT/OFFSET`, conteos y sumas |
| Análisis | `repositories/invoice_analyses.py`, `services/invoice_pipeline.py` | Inserción conjunta con factura, JSON almacenado |
| Revisiones | `repositories/invoice_reviews.py`, `services/invoice_review.py` | `AUTOINCREMENT`, transición condicional, historial paginado |
| Duplicados | `services/invoice_duplicates.py` | Reserva de SHA-256, coincidencia por campos, eliminación de reservas fallidas |
| Catálogo y sucursales | `repositories/business_data.py`, `seed_business_demo.py` | Alias, búsqueda normalizada, joins |
| Inventario y pedidos | `repositories/business_data.py`, `seed_business_demo.py` | Joins, filtrado, orden, existencias bajas |
| Políticas | `repositories/business_data.py`, `seed_business_demo.py` | Versión vigente |
| Quejas | `repositories/complaints.py` | Validación contra pedido y sucursal, folio único |
| Cuotas | `services/ai_quota.py` | `BEGIN IMMEDIATE`, contador diario y reinicio UTC |

El esquema incluye también `order_items`, `product_aliases`, `invoice_document_claims` e `invoice_business_claims`. El adaptador incluye todas las tablas; no cambió los contratos JSON de la API.

## Decisión de diseño para una demo pequeña

`STORAGE_BACKEND=sqlite` conserva el comportamiento local. `STORAGE_BACKEND=table` usa `DefaultAzureCredential` y la URL HTTPS `AZURE_TABLE_ACCOUNT_URL` desde el backend. La identidad administrada de la Function App recibe `Storage Table Data Contributor`. No se guarda una clave de Storage en React.

Azure Tables no ofrece joins ni transacciones entre particiones. El adaptador `backend/database/table_storage.py` lee la partición `demo` de una tabla, reconstruye el esquema en SQLite **en memoria**, ejecuta el SQL existente y confirma solo las filas modificadas en una [transacción de grupo de entidades](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/service/table-storage). La memoria no es el almacenamiento persistente. Se conservan filtrado, paginación, joins, estadísticas y los mismos objetos de respuesta.

Cada fila se guarda como entidad con clave única derivada de su clave primaria. Las creaciones usan `create`; actualizaciones y borrados usan ETag con `IfNotModified`. Todas las filas están en la misma partición para confirmar juntas factura, análisis, revisión y claves de duplicado. Las cuotas reintentan conflictos ETag y nunca superan el límite por carreras concurrentes. El hash de archivo y la clave normalizada de factura evitan duplicados simultáneos. Los [lotes de Azure Tables se limitan a 100 operaciones y 4 MiB](https://learn.microsoft.com/en-us/rest/api/storageservices/performing-entity-group-transactions); el adaptador rechaza transacciones mayores. También limita la demo a 1000 filas y 60 KiB UTF-16 por propiedad JSON, por debajo del [límite de cadenas de Azure Tables](https://learn.microsoft.com/en-us/rest/api/storageservices/understanding-the-table-service-data-model). Una ampliación del volumen requerirá repositorios específicos o un almacén relacional Azure; este adaptador no pretende escalar indefinidamente.

La reserva de cuota se confirma antes de llamar a IA. Un fallo posterior sigue consumiendo una unidad. La lectura de la partición completa tiene costo y latencia proporcionales al tamaño del conjunto; medirlos en Azure antes de habilitar operaciones costosas. El SDK `azure-data-tables==12.7.0` y `azure-identity==1.25.1` se añadieron a `requirements.txt`.

## Conservación de datos

`backend/scripts/migrate_sqlite_to_tables.py` toma una instantánea SQLite y copia todas sus tablas en una sola transacción si hay hasta 100 filas nuevas. No sobrescribe entidades remotas distintas y puede ejecutarse de nuevo si ya son idénticas. Para un conjunto mayor, se detiene antes de escribir; requiere un plan de lotes. Ejecutar la migración **antes** de las semillas de Azure evita conflictos con facturas locales ya revisadas. Después se pueden ejecutar `seed_demo` y `seed_business_demo`, que insertan solo filas faltantes. Se incluyen facturas, análisis, revisiones, datos empresariales, quejas y contadores históricos de cuotas; las cuotas de desarrollo tienen prefijo `development:` y no cuentan para producción.

La base local observada contiene 46 filas en 14 tablas, por debajo del límite de un lote. Esa medición solo verifica el origen local; no implica que se haya migrado a Azure.

La persistencia tras reiniciar Functions depende de que `STORAGE_BACKEND=table` y la identidad pueda acceder a Storage. El código no escribe el archivo `.db` en Azure. La prueba con cliente falso recrea conexiones y recupera los datos, pero **no verifica todavía** una Function App real ni un reinicio en Azure.

## Verificación de suscripción y región

La CLI devolvió suscripción `aa8016bc-c254-4cc9-8a5e-f97ee87cb4cc` (`Azure for Students`, Enabled), grupo `rg-rioclaro-ai-dev` en `eastus2`, roles heredados `Owner` y `User Access Administrator`, y solo `openai-rioclaro-dev` y `docint-rioclaro-dev` en `centralus`. Al inicio `Microsoft.Storage` y `Microsoft.Web` estaban `NotRegistered`; al cierre figuran `Registered`. El registro de actividad muestra `register/action` para ambos a las 08:04 UTC con la cuenta conectada, pero no permite atribuir el comando exacto. No se crearon recursos. La lista de ubicaciones de la CLI incluye `eastus2` para Storage, `sites`, `staticSites` y Functions Flex. Esto no confirma disponibilidad efectiva de SKU, cuota o costo para Azure for Students; la creación puede ser rechazada por la oferta o una política. Consultar [Azure for Students](https://learn.microsoft.com/en-us/azure/education-hub/faq) y la [guía de Flex Consumption](https://learn.microsoft.com/en-us/azure/azure-functions/flex-consumption-how-to) antes de autorizar gastos.

## Pruebas pendientes en Azure

1. Crear recursos tras autorización y comprobar que `DefaultAzureCredential` obtiene acceso a la tabla con la identidad de Functions.
2. Migrar/sembrar datos ficticios y comparar conteos de cada entidad.
3. Reiniciar Functions y repetir lecturas de facturas, análisis, historial, catálogo, pedidos, políticas, quejas y cuotas.
4. Medir latencia y operaciones de Storage con el conjunto real; validar ETags y lotes contra el SDK y servicio reales.
5. Implementar una modalidad pública sin login y con control de abuso adicional antes de activar IA. Actualmente `DEMO_MODE` solo sirve localmente y la Function publicada exige Entra; el frontend ya no ofrece login.

## Resultados locales de esta etapa

- `backend\.venv\Scripts\python.exe -m pytest tests -q`: **123 passed**. Ocho pruebas adicionales cubren el adaptador con cliente falso; no consumieron Azure.
- `npm test`: **8 passed**.
- `npm run build`: correcto.
- Los cuatro scripts PowerShell bajo `scripts/azure` pasaron el parser de PowerShell sin errores. No se ejecutaron las operaciones de creación, semilla ni despliegue.
- `Preflight-RioClaro.ps1` se ejecutó en modo de inspección: confirmó `eastus2`, `Owner`, ambos proveedores `Registered` y solo los dos recursos cognitivos existentes.
