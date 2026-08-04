#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform"

echo "=== Destroying AWS Academy Smart Parking Stack ==="

LAB_ROLE_ARN=$("$SCRIPT_DIR/find_lab_role.sh" || echo "dummy-arn")

terraform -chdir="$TF_DIR" destroy -var="lab_role_arn=$LAB_ROLE_ARN" -auto-approve

echo "=== Destroy Complete ==="
