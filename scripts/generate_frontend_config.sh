#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform"
CONFIG_JS="$ROOT_DIR/frontend/config.js"

echo "=== Generating Frontend config.js ==="
API_URL=$(terraform -chdir="$TF_DIR" output -raw api_gateway_url 2>/dev/null || echo "")

if [ -z "$API_URL" ]; then
    echo "ERROR: Unable to read api_gateway_url from Terraform outputs."
    echo "Ensure terraform apply has succeeded."
    exit 1
fi

cat <<EOF > "$CONFIG_JS"
window.SMART_PARKING_CONFIG = {
  API_BASE_URL: "${API_URL}"
};
EOF

echo "Successfully wrote $CONFIG_JS with API_BASE_URL: $API_URL"
