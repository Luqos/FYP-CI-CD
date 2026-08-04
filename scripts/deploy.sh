#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform"

echo "========================================================"
echo " AWS Academy Smart Parking Prototype Deployment Script  "
echo "========================================================"

# Step 1: Check Identity
"$SCRIPT_DIR/check_aws_identity.sh"

# Step 2: Detect Region
AWS_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")
echo "Target AWS Region: $AWS_REGION"

# Step 3: Detect LabRole / VocLabs
LAB_ROLE_ARN=$("$SCRIPT_DIR/find_lab_role.sh" || echo "")
if [ -z "$LAB_ROLE_ARN" ]; then
    echo "ERROR: Unable to detect AWS Academy IAM role."
    exit 1
fi
echo "Using IAM Execution Role: $LAB_ROLE_ARN"

# Step 4: Package Lambdas
"$SCRIPT_DIR/package_lambdas.sh"

# Step 5-7: Terraform Apply
echo "=== Running Terraform Infrastructure Deployment ==="
terraform -chdir="$TF_DIR" init
terraform -chdir="$TF_DIR" plan -var="lab_role_arn=$LAB_ROLE_ARN" -var="aws_region=$AWS_REGION"
terraform -chdir="$TF_DIR" apply -var="lab_role_arn=$LAB_ROLE_ARN" -var="aws_region=$AWS_REGION" -auto-approve

# Step 8-9: Read outputs and generate frontend config
"$SCRIPT_DIR/generate_frontend_config.sh"

DASHBOARD_BUCKET=$(terraform -chdir="$TF_DIR" output -raw dashboard_bucket_name)
DASHBOARD_URL=$(terraform -chdir="$TF_DIR" output -raw dashboard_url)
API_URL=$(terraform -chdir="$TF_DIR" output -raw api_gateway_url)

# Step 10: Upload Dashboard files to S3
echo "=== Uploading Frontend Dashboard to S3 Bucket ($DASHBOARD_BUCKET) ==="
aws s3 cp "$ROOT_DIR/frontend/index.html" "s3://$DASHBOARD_BUCKET/index.html"
aws s3 cp "$ROOT_DIR/frontend/style.css" "s3://$DASHBOARD_BUCKET/style.css"
aws s3 cp "$ROOT_DIR/frontend/app.js" "s3://$DASHBOARD_BUCKET/app.js"
aws s3 cp "$ROOT_DIR/frontend/config.js" "s3://$DASHBOARD_BUCKET/config.js"

# Step 11-12: Print Final Summary
echo ""
echo "========================================================"
echo " Deployment Complete!                                   "
echo "========================================================"
echo " S3 Dashboard URL:"
echo "   $DASHBOARD_URL"
echo ""
echo " API Gateway URL:"
echo "   $API_URL"
echo ""
echo " Sample Test Commands:"
echo "   ./scripts/publish_sample_aws_cli.sh A01 14.2"
echo "   ./scripts/publish_sample_aws_cli.sh A02 85.0"
echo "========================================================"
