# PowerShell Create IoT Thing & Certificates Helper Script
param (
    [string]$ThingName = "esp32-A01-thing"
)

$ErrorActionPreference = "SilentlyContinue"
$certsDir = Join-Path (Get-Location) "certs"
New-Item -ItemType Directory -Path $certsDir -Force | Out-Null

Write-Host "=== AWS IoT Thing and Certificate Creator ===" -ForegroundColor Cyan
aws iot create-thing --thing-name $ThingName

Write-Host "Creating Keys and Certificate..."
$certJson = aws iot create-keys-and-certificate --set-as-active --output json
if (-not $certJson) {
    Write-Host "WARNING: AWS Academy permissions prevented creating certificates via CLI." -ForegroundColor Yellow
    Write-Host "Please create Thing and Certificate manually via AWS IoT Core Console." -ForegroundColor Yellow
    exit 0
}

$certObj = $certJson | ConvertFrom-Json
$certArn = $certObj.certificateArn

# Save certificate PEM
$certObj.certificatePem | Set-Content -Path (Join-Path $certsDir "device-certificate.pem.crt") -Encoding UTF8
# Save private key
$certObj.keyPair.PrivateKey | Set-Content -Path (Join-Path $certsDir "private.pem.key") -Encoding UTF8

Write-Host "Attaching Thing Principal..."
aws iot attach-thing-principal --thing-name $ThingName --principal $certArn

Write-Host "Certificates created and saved to $certsDir" -ForegroundColor Green
Write-Host "WARNING: DO NOT COMMIT CERTIFICATES TO GIT REPOSITORY." -ForegroundColor Red