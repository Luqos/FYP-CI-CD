#!/usr/bin/env bash
set -e

THING_NAME="${1:-esp32-A01-thing}"
CERTS_DIR="$(pwd)/certs"

echo "=== AWS IoT Thing and Certificate Creator ==="
mkdir -p "$CERTS_DIR"

echo "Creating IoT Thing: $THING_NAME..."
aws iot create-thing --thing-name "$THING_NAME" || true

echo "Creating Keys and Certificate..."
CERT_OUTPUT=$(aws iot create-keys-and-certificate --set-as-active --output json 2>/dev/null || echo "")

if [ -z "$CERT_OUTPUT" ]; then
    echo "WARNING: AWS Academy permissions prevented creating certificates via CLI."
    echo "Please create Thing and Certificate manually via AWS IoT Core Console."
    exit 0
fi

CERT_ARN=$(echo "$CERT_OUTPUT" | grep -o '"certificateArn": "[^"]*' | cut -d'"' -f4)
echo "$CERT_OUTPUT" | grep -o '"certificatePem": "[^"]*' | cut -d'"' -f4 | sed 's/\\n/\n/g' > "$CERTS_DIR/device-certificate.pem.crt"
echo "$CERT_OUTPUT" | grep -o '"privateKey": "[^"]*' | cut -d'"' -f4 | sed 's/\\n/\n/g' > "$CERTS_DIR/private.pem.key"

echo "Attaching Thing Principal..."
aws iot attach-thing-principal --thing-name "$THING_NAME" --principal "$CERT_ARN" || true

echo "Saved certificates to $CERTS_DIR/"
echo "WARNING: DO NOT COMMIT CERTIFICATES TO GIT REPOSITORY."
