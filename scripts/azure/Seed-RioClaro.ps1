param(
    [Parameter(Mandatory=$true)][string]$StorageName,
    [string]$SubscriptionId = 'aa8016bc-c254-4cc9-8a5e-f97ee87cb4cc',
    [switch]$AuthorizeAzureWrite
)

$ErrorActionPreference = 'Stop'
if (-not $AuthorizeAzureWrite) { throw 'La semilla escribe datos en Azure Tables. Usa -AuthorizeAzureWrite tras confirmar el destino.' }
$backend = (Resolve-Path (Join-Path $PSScriptRoot '..\..\backend')).Path
$python = Join-Path $backend '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Instala dependencias Python en backend/.venv antes de ejecutar.' }
az account set --subscription $SubscriptionId
if ($LASTEXITCODE -ne 0) { throw 'No se pudo seleccionar la suscripción.' }

$env:STORAGE_BACKEND = 'table'
$env:AZURE_TABLE_ACCOUNT_URL = "https://$StorageName.table.core.windows.net"
$env:AZURE_TABLE_NAME = 'RioClaroDemo'
try {
    Push-Location $backend
    & $python -m seed_demo
    if ($LASTEXITCODE -ne 0) { throw 'Falló la semilla de facturas.' }
    & $python -m seed_business_demo
    if ($LASTEXITCODE -ne 0) { throw 'Falló la semilla empresarial.' }
    & $python -c 'from repositories.invoices import get_invoice_stats; from repositories.business_data import get_branch_report; print("facturas:", get_invoice_stats()["total_invoices"], "sucursales:", len(get_branch_report()["branches"]))'
    if ($LASTEXITCODE -ne 0) { throw 'Falló la comprobación de lectura.' }
} finally {
    Pop-Location
    Remove-Item Env:\STORAGE_BACKEND -ErrorAction SilentlyContinue
    Remove-Item Env:\AZURE_TABLE_ACCOUNT_URL -ErrorAction SilentlyContinue
    Remove-Item Env:\AZURE_TABLE_NAME -ErrorAction SilentlyContinue
}
