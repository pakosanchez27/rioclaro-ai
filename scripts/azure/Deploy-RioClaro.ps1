param(
    [Parameter(Mandatory=$true)][string]$FunctionName,
    [Parameter(Mandatory=$true)][string]$StaticName,
    [string]$SubscriptionId = 'aa8016bc-c254-4cc9-8a5e-f97ee87cb4cc',
    [string]$ResourceGroup = 'rg-rioclaro-ai-dev',
    [switch]$AuthorizeDeploy
)

$ErrorActionPreference = 'Stop'
if (-not $AuthorizeDeploy) {
    throw 'Agrega -AuthorizeDeploy para publicar. El script no modifica App Settings ni habilita IA.'
}
az account set --subscription $SubscriptionId
if ($LASTEXITCODE -ne 0) { throw 'No se pudo seleccionar la suscripción.' }
$settings = az functionapp config appsettings list -g $ResourceGroup -n $FunctionName --query '[].{name:name,value:value}' -o json | ConvertFrom-Json
function Get-Setting([string]$name) { return ($settings | Where-Object { $_.name -eq $name } | Select-Object -First 1).value }
if ((Get-Setting 'STORAGE_BACKEND') -ne 'table' -or (Get-Setting 'DEMO_MODE') -ne 'false' -or
    (Get-Setting 'PROD_MAX_DAILY_ASSISTANT_QUESTIONS') -ne '20' -or
    (Get-Setting 'PROD_MAX_DAILY_INVOICE_ANALYSES') -ne '5') {
    throw 'Se requiere Tables, DEMO_MODE=false y cuotas de producción 20/5. No se cambió ninguna configuración.'
}

$backend = (Resolve-Path (Join-Path $PSScriptRoot '..\..\backend')).Path
$frontend = (Resolve-Path (Join-Path $PSScriptRoot '..\..\frontend')).Path
Push-Location $backend
try {
    func azure functionapp publish $FunctionName --python
    if ($LASTEXITCODE -ne 0) { throw 'Falló el despliegue de Azure Functions.' }
} finally { Pop-Location }

$hostName = az staticwebapp show -n $StaticName -g $ResourceGroup --query defaultHostname -o tsv
if ($LASTEXITCODE -ne 0 -or -not $hostName) { throw 'No se pudo consultar el dominio de Static Web Apps.' }
$origins = @(az functionapp cors show -n $FunctionName -g $ResourceGroup --query allowedOrigins -o tsv)
if ($LASTEXITCODE -ne 0 -or $origins.Count -ne 1 -or $origins[0] -ne "https://$hostName") {
    throw "CORS debe permitir exclusivamente https://$hostName. Configúralo antes del despliegue."
}

Push-Location $frontend
try {
    $env:VITE_API_BASE_URL = "https://$FunctionName.azurewebsites.net/api"
    npm ci
    if ($LASTEXITCODE -ne 0) { throw 'Falló npm ci.' }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación de React.' }
    $env:SWA_CLI_DEPLOYMENT_TOKEN = az staticwebapp secrets list -n $StaticName -g $ResourceGroup --query properties.apiKey -o tsv
    if ($LASTEXITCODE -ne 0 -or -not $env:SWA_CLI_DEPLOYMENT_TOKEN) { throw 'No se pudo obtener el token de despliegue.' }
    npx --yes @azure/static-web-apps-cli deploy ./dist --env production
    if ($LASTEXITCODE -ne 0) { throw 'Falló el despliegue de Static Web Apps.' }
} finally {
    Remove-Item Env:\VITE_API_BASE_URL -ErrorAction SilentlyContinue
    Remove-Item Env:\SWA_CLI_DEPLOYMENT_TOKEN -ErrorAction SilentlyContinue
    Pop-Location
}
Write-Host "Aplicación publicada en https://$hostName. Los App Settings y las banderas de IA se conservaron."
