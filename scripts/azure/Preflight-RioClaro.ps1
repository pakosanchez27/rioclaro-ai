param(
    [string]$SubscriptionId = 'aa8016bc-c254-4cc9-8a5e-f97ee87cb4cc',
    [string]$ResourceGroup = 'rg-rioclaro-ai-dev',
    [string]$Region = 'eastus2'
)

$ErrorActionPreference = 'Stop'
az account set --subscription $SubscriptionId
if ($LASTEXITCODE -ne 0) { throw 'No se pudo seleccionar la suscripción.' }

$account = az account show --query '{id:id,name:name,state:state}' -o json | ConvertFrom-Json
$group = az group show --name $ResourceGroup --query '{name:name,location:location}' -o json | ConvertFrom-Json
$storageProvider = az provider show -n Microsoft.Storage --query registrationState -o tsv
$webProvider = az provider show -n Microsoft.Web --query registrationState -o tsv
$flexLocations = az functionapp list-flexconsumption-locations --query '[].name' -o json | ConvertFrom-Json
$roles = az role assignment list --scope "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup" --include-inherited --query '[].roleDefinitionName' -o json | ConvertFrom-Json
$resources = az resource list -g $ResourceGroup --query '[].{name:name,type:type,location:location}' -o json | ConvertFrom-Json

[pscustomobject]@{
    Subscription = $account.id
    Offer = $account.name
    Group = $group.name
    GroupRegion = $group.location
    StorageProvider = $storageProvider
    WebProvider = $webProvider
    FlexRegionListed = ($flexLocations -contains $Region)
    Roles = ($roles -join ', ')
    ExistingResources = ($resources | ConvertTo-Json -Compress)
} | Format-List

Write-Host 'Esta inspección no confirma disponibilidad de SKU, cuota ni costo de Azure for Students.'
