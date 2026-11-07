# Despliegue Azure — estado y pasos pendientes

**Estado:** no desplegado. No existe URL pública. No ejecutar este procedimiento sin verificar presupuesto, cuotas y permisos del propietario.

## Recursos comprobados (2026-11-07)

`az resource list -g rg-rioclaro-ai-dev` mostró solo:

- `openai-rioclaro-dev` — OpenAI S0, Central US, Succeeded. Despliegue `gpt-rioclaro` / GPT-5 mini.
- `docint-rioclaro-dev` — Document Intelligence F0, Central US, Succeeded.

`Microsoft.Web` y `Microsoft.Storage` estaban `NotRegistered` al inicio y figuran `Registered` al cierre. El registro de actividad muestra acciones de registro a las 08:04 UTC con la cuenta conectada; no se identificó el comando que las inició. No se creó Storage Account, Function App ni Static Web App.
`az consumption budget list` no devolvió presupuestos; no se confirmó un límite de gasto efectivo.

## Bloqueos técnicos antes de publicar

1. **Persistencia:** el adaptador Azure Tables y la migración están implementados, pero solo probados con cliente falso. Comprobar acceso por identidad, lectura y escritura, cuotas y reinicio real de Functions.
2. **Demo pública:** `DEMO_MODE` actual se rechaza en Azure. Implementar una modalidad pública separada con permisos mínimos, cuotas globales persistentes, límite por origen/ventana y suspensión de análisis/chat. No exponer claves en Vite.
3. **Procesamiento largo:** el análisis es HTTP síncrono. [Functions limita la respuesta HTTP a 230 segundos](https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale). Medir con facturas ficticias y, si se acerca al límite, mover a cola con estado consultable.
4. **Costo y cuotas:** confirmar región, oferta de Azure for Students, precios efectivos, cuotas de GPT-5 mini, Document Intelligence, Functions, Storage y Static Web Apps. La [página oficial de precios de Static Web Apps](https://azure.microsoft.com/en-us/pricing/details/app-service/static/) y la [de Functions](https://azure.microsoft.com/en-us/pricing/details/functions/) muestran opciones y condiciones; no se calcula un importe real sin la configuración final. La cuota de la app debe detener gasto aun si se supera el presupuesto deseado.
5. **Voz:** no hay recurso Speech. La [tabla oficial de cuotas de Speech](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-services-quotas-and-limits) debe revisarse antes de decidir un SKU.

## Secuencia preparada, sin ejecutar

1. Confirmar con el propietario que se pueden registrar proveedores `Microsoft.Web` y `Microsoft.Storage` y crear recursos dentro de `rg-rioclaro-ai-dev`.
2. Elegir SKU/región tras revisar costos y disponibilidad. Registrar proveedores solo con autorización.
3. Crear Storage Account persistente y la implementación de repositorios Azure con pruebas de concurrencia y reinicio.
4. Crear Function App Python 3.11 y Static Web App. Configurar app settings de backend desde un almacén seguro; nunca incluir claves en el repositorio ni en `VITE_*`.
5. Configurar `VITE_API_BASE_URL` con URL de API o usar ruta integrada `/api`; restringir CORS al dominio real de SWA.
6. Mantener `DEMO_MODE=false` en Azure. Activar la modalidad pública limitada solo después de pruebas de abuso.
7. Configurar Application Insights con logs sin cuerpos de facturas, preguntas ni secretos. Definir alertas y límite de consumo.
8. Publicar desde la rama probada. Verificar GET, POST, persistencia tras reinicio, móvil, una factura ficticia, una pregunta real al asistente y ausencia de secretos en artefactos.
9. Registrar URL y capturas reales en `ENTREGA_RIO_CLARO_AI.md`.

## Configuración local disponible

- `backend/local.settings.example.json` y `backend/.env.example`: solo marcadores vacíos para credenciales.
- `frontend/.env.example`: `/api` y proxy configurable `VITE_DEV_PROXY_TARGET`.
- `backend/local.settings.json` real está ignorado; no trasladarlo a Azure ni subirlo a Git.

## Comandos de verificación previos

```powershell
az account show --query '{name:name,state:state}' -o json
az resource list -g rg-rioclaro-ai-dev --query '[].{name:name,type:type,location:location}' -o table
az provider show -n Microsoft.Web --query registrationState -o tsv
az provider show -n Microsoft.Storage --query registrationState -o tsv
```

## Preparación de persistencia (7 de noviembre de 2026)

Se implementó `STORAGE_BACKEND=table` mediante [el adaptador documentado](ALMACENAMIENTO_AZURE.md). `STORAGE_BACKEND=sqlite` sigue siendo el valor local. La persistencia Azure solo pasó pruebas con un cliente falso; no se ha probado contra un Storage Account ni tras reiniciar Functions. La configuración de React acepta `VITE_API_BASE_URL=https://<function>.azurewebsites.net/api`; el proxy `/api` de Vite permanece para desarrollo.

Los scripts bajo `scripts/azure/` están preparados y **no se ejecutaron**. `Preflight-RioClaro.ps1` solo consulta Azure; `Provision-RioClaro.ps1` crea Storage Standard_LRS, Function App Flex Python 3.11 y Static Web App Free únicamente con `-AuthorizeResourceCreation`. Asigna identidad administrada y rol `Storage Table Data Contributor` para datos de la aplicación. `Seed-RioClaro.ps1` escribe datos ficticios de forma idempotente. `Deploy-RioClaro.ps1` publica solo un **preview autenticado**, con IA suspendida y `DEMO_MODE=false`, si se le pasa `-AuthorizeAuthenticatedPreview`.

Antes de ejecutar provisión, confirmar presupuesto, permisos efectivos y disponibilidad de SKU en Azure for Students. Los proveedores `Microsoft.Storage` y `Microsoft.Web` figuran ahora `Registered`; el script comprueba su registro al ejecutarse. La CLI enumera `eastus2` para Storage, Function Flex y Static Web Apps, pero eso no garantiza que la oferta permita crearlos. [Functions Flex admite Python 3.11](https://learn.microsoft.com/en-us/azure/azure-functions/flex-consumption-how-to); [Static Web Apps permite crear un recurso sin integración GitHub](https://learn.microsoft.com/en-us/cli/azure/staticwebapp).

### Secuencia preparada para Windows PowerShell

```powershell
cd C:\Proyectos\rioclaro-ai
.\scripts\azure\Preflight-RioClaro.ps1

# Elegir nombres globalmente únicos y confirmar costo antes de ejecutar:
$storage = 'st<nombreunico>rioclaro'
$function = 'func-<nombreunico>-rioclaro'
$static = 'swa-<nombreunico>-rioclaro'
.\scripts\azure\Provision-RioClaro.ps1 -StorageName $storage -FunctionName $function -StaticName $static -AuthorizeResourceCreation

# Con Storage Table Data Contributor asignado a la identidad local, migrar datos
# SQLite existentes ANTES de la semilla (el script Python no sobrescribe filas):
$env:STORAGE_BACKEND = 'table'
$env:AZURE_TABLE_ACCOUNT_URL = "https://$storage.table.core.windows.net"
$env:AZURE_TABLE_NAME = 'RioClaroDemo'
cd backend
.\.venv\Scripts\python.exe scripts\migrate_sqlite_to_tables.py --source data\rioclaro.db --confirm-azure-write
cd ..
Remove-Item Env:\STORAGE_BACKEND, Env:\AZURE_TABLE_ACCOUNT_URL, Env:\AZURE_TABLE_NAME
.\scripts\azure\Seed-RioClaro.ps1 -StorageName $storage -AuthorizeAzureWrite

# Solo después de aprobar un preview protegido; la IA queda suspendida:
.\scripts\azure\Deploy-RioClaro.ps1 -FunctionName $function -StaticName $static -AuthorizeAuthenticatedPreview
```

Para la migración desde la máquina local, el operador necesita el rol de datos de Tables; `Owner` del grupo no otorga automáticamente permisos de datos. Tras crear el recurso se debe comprobar el rol y, si falta, asignarlo al operador usando su Object ID mediante `az role assignment create --assignee-object-id <oid> --assignee-principal-type User --role 'Storage Table Data Contributor' --scope <storage-id>`.

El preview no satisface todavía el requisito de evaluación anónima: la API conserva autorización Entra y React retiró el login. Antes de habilitar IA o anunciar una URL pública funcional faltan autenticación de demo pública con controles de abuso, pruebas reales de Tables y configuración segura de las credenciales de Azure OpenAI/Document Intelligence. La identidad administrada protege el acceso a datos Tables; el host de Functions usa por ahora la configuración de Storage creada por la CLI. No imprimir ni guardar sus claves en el repositorio.

