# PowerShell AWS CLI Sample IoT Telemetry Publisher
param (
    [string]$SlotId = "A01",
    [double]$DistanceCm = 14.2
)

$ErrorActionPreference = "Stop"

Write-Host "=== AWS CLI Sample IoT Telemetry Publisher ===" -ForegroundColor Cyan
$iotEndpoint = aws iot describe-endpoint --endpoint-type iot:Data-ATS --query endpointAddress --output text

if (-not $iotEndpoint -or $iotEndpoint -eq "None") {
    Write-Host "ERROR: Could not discover AWS IoT ATS endpoint address." -ForegroundColor Red
    exit 1
}

$topic = "smart-parking/slot/$SlotId/telemetry"
$payload = "{`"slotId`":`"$SlotId`",`"distanceCm`":$DistanceCm,`"deviceId`":`"cli-publisher-$SlotId`"}"

Write-Host "Target Endpoint: https://$iotEndpoint"
Write-Host "Publishing to Topic: $topic"
Write-Host "Payload: $payload"

aws iot-data publish `
    --endpoint-url "https://$iotEndpoint" `
    --topic "$topic" `
    --cli-binary-format raw-in-base64-out `
    --payload "$payload"

Write-Host "Published successfully!" -ForegroundColor Green
