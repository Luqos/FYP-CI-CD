# PowerShell Check AWS Identity Script
$ErrorActionPreference = "Stop"

Write-Host "=== AWS Identity and Configuration Check ===" -ForegroundColor Cyan

try {
    $identity = aws sts get-caller-identity | ConvertFrom-Json
    $region = aws configure get region
    if (-not $region) { $region = "us-east-1" }

    Write-Host "AWS Account ID : "$identity.Account -ForegroundColor Green
    Write-Host "User/Role ARN  : "$identity.Arn -ForegroundColor Green
    Write-Host "Active Region  : "$region -ForegroundColor Green
    Write-Host "=== Identity Check Passed ===" -ForegroundColor Cyan
} catch {
    Write-Host "ERROR: Unable to get AWS caller identity. AWS credentials may be missing or expired." -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}
