# PowerShell Get Terraform Outputs Script
$rootDir = Split-Path -Parent $PSScriptRoot
$tfDir = Join-Path $rootDir "infra\terraform"

Write-Host "=== Deployed AWS Infrastructure Outputs ===" -ForegroundColor Cyan
terraform -chdir="$tfDir" output
