#!/usr/bin/env bash
set -e

SLOT_ID="${1:-A01}"
DISTANCE_CM="${2:-14.2}"

echo "=== AWS CLI Sample IoT Telemetry Publisher ==="
IOT_ENDPOINT=$(aws iot describe-endpoint --endpoint-type iot:Data-ATS --query endpointAddress --output text 2>/dev/null)

if [ -z "$IOT_ENDPOINT" ] || [ "$IOT_ENDPOINT" = "None" ]; then
    echo "ERROR: Could not discover AWS IoT ATS endpoint address."
    exit 1
fi

TOPIC="smart-parking/slot/${SLOT_ID}/telemetry"
PAYLOAD="{\"slotId\":\"${SLOT_ID}\",\"distanceCm\":${DISTANCE_CM},\"deviceId\":\"cli-publisher-${SLOT_ID}\"}"

echo "Target Endpoint: https://${IOT_ENDPOINT}"
echo "Publishing to Topic: ${TOPIC}"
echo "Payload: ${PAYLOAD}"

aws iot-data publish \
    --endpoint-url "https://${IOT_ENDPOINT}" \
    --topic "${TOPIC}" \
    --cli-binary-format raw-in-base64-out \
    --payload "${PAYLOAD}"

echo "Published successfully!"
