# PowerShell Generate Frontend Config Script
$ErrorActionPreference = "Stop"

$rootDir = Split-Path -Parent $PSScriptRoot
$tfDir = Join-Path $rootDir "infra\terraform"
$configJs = Join-Path $rootDir "frontend\config.js"

Write-Host "=== Generating Frontend config.js ===" -ForegroundColor Cyan

$apiUrl = terraform -chdir="$tfDir" output -raw api_gateway_url 2>$null

if (-not $apiUrl) {
    Write-Host "ERROR: Unable to read api_gateway_url from Terraform outputs." -ForegroundColor Red
    exit 1
}

$content = @"
window.SMART_PARKING_CONFIG = {
  API_BASE_URL: "$apiUrl"
};
"@

Set-Content -Path $configJs -Value $content -Encoding UTF8
Write-Host "Successfully wrote $configJs with API_BASE_URL: $apiUrl" -ForegroundColor Green
