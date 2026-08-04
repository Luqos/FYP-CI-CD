# PowerShell Package Lambdas Script
$ErrorActionPreference = "Stop"

$rootDir = Split-Path -Parent $PSScriptRoot
$buildDir = Join-Path $rootDir "build"

Write-Host "=== Packaging Lambda Functions ===" -ForegroundColor Cyan

if (Test-Path $buildDir) { Remove-Item $buildDir -Recurse -Force }
New-Item -ItemType Directory -Path $buildDir | Out-Null

# Package 1: ingest_sensor_data.zip
$tempIngest = Join-Path $buildDir "temp_ingest"
New-Item -ItemType Directory -Path (Join-Path $tempIngest "shared") -Force | Out-Null
Copy-Item (Join-Path $rootDir "backend\ingest_sensor_data\app.py") $tempIngest
Copy-Item (Join-Path $rootDir "backend\shared\*.py") (Join-Path $tempIngest "shared")

$ingestZip = Join-Path $buildDir "ingest_sensor_data.zip"
Compress-Archive -Path "$tempIngest\*" -DestinationPath $ingestZip -Force
Remove-Item $tempIngest -Recurse -Force
Write-Host "Created $ingestZip" -ForegroundColor Green

# Package 2: dashboard_api.zip
$tempApi = Join-Path $buildDir "temp_api"
New-Item -ItemType Directory -Path (Join-Path $tempApi "shared") -Force | Out-Null
Copy-Item (Join-Path $rootDir "backend\dashboard_api\app.py") $tempApi
Copy-Item (Join-Path $rootDir "backend\shared\*.py") (Join-Path $tempApi "shared")

$apiZip = Join-Path $buildDir "dashboard_api.zip"
Compress-Archive -Path "$tempApi\*" -DestinationPath $apiZip -Force
Remove-Item $tempApi -Recurse -Force
Write-Host "Created $apiZip" -ForegroundColor Green

Write-Host "=== Packaging Complete ===" -ForegroundColor Cyan
