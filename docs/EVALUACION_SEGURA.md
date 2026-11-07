# Acceso de evaluación: ejecución autorizada

La publicación y la activación son pasos separados. Ejecutar desde PowerShell 7 tras aprobar el cambio. No ejecutar `DEMO_MODE=true` en Azure. El código se entrega al evaluador por un canal privado; React solo recibe un token temporal de dos horas. El interruptor `EVALUATOR_ACCESS_ENABLED=false` invalida todas las sesiones inmediatamente.

## Configurar la credencial y CORS

```powershell
$rg = 'rg-rioclaro-ai-dev'
$function = 'func-rioclaro-626839'
$origin = 'https://purple-rock-0f2728210.5.azurestaticapps.net'
$secureCode = Read-Host 'Código de evaluación de alta entropía' -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureCode)
try { $plainCode = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
$salt = [Security.Cryptography.RandomNumberGenerator]::GetBytes(16)
$kdf = [Security.Cryptography.Rfc2898DeriveBytes]::new($plainCode, $salt, 210000, [Security.Cryptography.HashAlgorithmName]::SHA256)
try { $hash = [Convert]::ToHexString($kdf.GetBytes(32)).ToLowerInvariant() }
finally { $kdf.Dispose(); $plainCode = $null; $secureCode.Dispose() }
$saltHex = [Convert]::ToHexString($salt).ToLowerInvariant()
az functionapp config appsettings set -g $rg -n $function --settings "EVALUATOR_CODE_SALT=$saltHex" "EVALUATOR_CODE_HASH=$hash" 'EVALUATOR_ACCESS_ENABLED=false' --output none
$hash = $null; $saltHex = $null
az functionapp cors remove -g $rg -n $function --allowed-origins --output none
az functionapp cors add -g $rg -n $function --allowed-origins $origin --output none
az functionapp cors show -g $rg -n $function --query allowedOrigins -o json
```

## Publicar, sin habilitar IA

```powershell
Set-Location 'C:\Proyectos\rioclaro-ai'
.\backend\.venv\Scripts\python.exe -m pytest -q
Push-Location .\frontend
try { npm test -- --run; npm run build }
finally { Pop-Location }
$staticName = az staticwebapp list -g 'rg-rioclaro-ai-dev' --query "[?defaultHostname=='purple-rock-0f2728210.5.azurestaticapps.net'].name | [0]" -o tsv
if (-not $staticName) { throw 'No se encontró Static Web App con el dominio oficial.' }
.\scripts\azure\Deploy-RioClaro.ps1 -FunctionName 'func-rioclaro-626839' -StaticName $staticName -AuthorizeDeploy
```

El nombre del recurso Static Web App se obtiene por su dominio oficial.

## Activar tras aprobar pruebas funcionales

```powershell
az functionapp config appsettings set -g $rg -n $function --settings 'DEMO_MODE=false' 'STORAGE_BACKEND=table' 'PROD_MAX_DAILY_ASSISTANT_QUESTIONS=20' 'PROD_MAX_DAILY_INVOICE_ANALYSES=5' 'EVALUATOR_ACCESS_ENABLED=true' --output none
# Solo con autorización explícita para consumir créditos:
az functionapp config appsettings set -g $rg -n $function --settings 'ENABLE_ASSISTANT=true' 'ENABLE_INVOICE_ANALYSIS=true' --output none
```

## Desactivar de inmediato

```powershell
az functionapp config appsettings set -g 'rg-rioclaro-ai-dev' -n 'func-rioclaro-626839' --settings 'EVALUATOR_ACCESS_ENABLED=false' 'ENABLE_ASSISTANT=false' 'ENABLE_INVOICE_ANALYSIS=false' --output none
```

## Verificación sin créditos

Revisar que los nombres `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`, `DOCUMENTINTELLIGENCE_ENDPOINT` y `DOCUMENTINTELLIGENCE_API_KEY` estén presentes en App Settings. No imprimir sus valores. No se puede certificar la conectividad real ni los permisos de esos servicios sin una llamada de prueba autorizada. El frontend se compila con `VITE_API_BASE_URL=https://func-rioclaro-626839.azurewebsites.net/api` desde el script.

Desde el navegador: comprobar acceso incorrecto y bloqueo al noveno intento; acceso correcto y navegación de facturas, pedidos, reportes y quejas; recarga de página; cierre de sesión y rechazo del token anterior; expiración de dos horas; respuesta 401 sin token en endpoints protegidos; mensajes 429 de cuota y 503 con IA suspendida. Tras autorización de créditos, probar una pregunta y una factura, comprobar 20/5 como límites compartidos y verificar que los registros previos siguen presentes.
