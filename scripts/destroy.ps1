# PowerShell Destroy Infrastructure Script
$ErrorActionPreference = "Stop"

$rootDir = Split-Path -Parent $PSScriptRoot
$tfDir = Join-Path $rootDir "infra\terraform"

Write-Host "=== Destroying AWS Academy Smart Parking Stack ===" -ForegroundColor Red

$labRoleArn = & (Join-Path $PSScriptRoot "find_lab_role.ps1")
if (-not $labRoleArn) { $labRoleArn = "dummy-arn" }

terraform -chdir="$tfDir" destroy -var="lab_role_arn=$labRoleArn" -auto-approve

Write-Host "=== Destroy Complete ===" -ForegroundColor Green
