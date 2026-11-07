param(
    [Parameter(Mandatory=$true)][string]$StorageName,
    [Parameter(Mandatory=$true)][string]$FunctionName,
    [Parameter(Mandatory=$true)][string]$StaticName,
    [string]$SubscriptionId = 'aa8016bc-c254-4cc9-8a5e-f97ee87cb4cc',
    [string]$ResourceGroup = 'rg-rioclaro-ai-dev',
    [string]$Region = 'eastus2',
    [switch]$AuthorizeResourceCreation
)

$ErrorActionPreference = 'Stop'
if (-not $AuthorizeResourceCreation) {
    throw 'Este script crea recursos de Azure. Ejecútalo solo tras confirmar costo, cuota y autorización, con -AuthorizeResourceCreation.'
}
if ($StorageName -notmatch '^[a-z0-9]{3,24}$') { throw 'StorageName debe tener entre 3 y 24 caracteres minúsculos o dígitos.' }

az account set --subscription $SubscriptionId
if ($LASTEXITCODE -ne 0) { throw 'No se pudo seleccionar la suscripción.' }
foreach ($provider in @('Microsoft.Storage', 'Microsoft.Web')) {
    $state = az provider show --namespace $provider --query registrationState -o tsv
    if ($LASTEXITCODE -ne 0) { throw "No se pudo consultar $provider." }
    if ($state -ne 'Registered') {
        az provider register --namespace $provider --wait --output none
        if ($LASTEXITCODE -ne 0) { throw "No se pudo registrar $provider." }
    }
}

az storage account create --name $StorageName --resource-group $ResourceGroup --location $Region --sku Standard_LRS --kind StorageV2 --min-tls-version TLS1_2 --allow-blob-public-access false --output none
if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear Storage Account.' }

az functionapp create --name $FunctionName --resource-group $ResourceGroup --storage-account $StorageName --flexconsumption-location $Region --runtime python --runtime-version 3.11 --functions-version 4 --instance-memory 2048 --maximum-instance-count 1 --output none
if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear Function App.' }

$principalId = az functionapp identity assign --name $FunctionName --resource-group $ResourceGroup --query principalId -o tsv
if ($LASTEXITCODE -ne 0 -or -not $principalId) { throw 'No se pudo asignar identidad administrada.' }
$storageId = az storage account show --name $StorageName --resource-group $ResourceGroup --query id -o tsv
az role assignment create --assignee-object-id $principalId --assignee-principal-type ServicePrincipal --role 'Storage Table Data Contributor' --scope $storageId --output none
if ($LASTEXITCODE -ne 0) { throw 'No se pudo asignar Storage Table Data Contributor.' }

az functionapp config appsettings set --name $FunctionName --resource-group $ResourceGroup --settings "STORAGE_BACKEND=table" "AZURE_TABLE_ACCOUNT_URL=https://$StorageName.table.core.windows.net" 'AZURE_TABLE_NAME=RioClaroDemo' 'AZURE_FUNCTIONS_ENVIRONMENT=Production' 'DEMO_MODE=false' 'ENABLE_ASSISTANT=false' 'ENABLE_INVOICE_ANALYSIS=false' 'PROD_MAX_DAILY_ASSISTANT_QUESTIONS=20' 'PROD_MAX_DAILY_INVOICE_ANALYSES=5' --output none
if ($LASTEXITCODE -ne 0) { throw 'No se pudo configurar Function App.' }

az staticwebapp create --name $StaticName --resource-group $ResourceGroup --location $Region --sku Free --output none
if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear Static Web App Free.' }

Write-Host 'Recursos creados. IA suspendida y DEMO_MODE=false. Aún no se ha desplegado código ni configurado autenticación pública.'
