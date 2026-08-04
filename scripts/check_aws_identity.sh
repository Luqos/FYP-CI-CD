#!/usr/bin/env bash
set -e

echo "=== AWS Identity and Configuration Check ==="
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI is not installed or not in PATH."
    exit 1
fi

IDENTITY=$(aws sts get-caller-identity 2>&1)
if [ $? -ne 0 ]; then
    echo "ERROR: Unable to get AWS caller identity. AWS credentials may be missing or expired."
    echo "$IDENTITY"
    exit 1
fi

REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")

echo "AWS Caller Identity:"
echo "$IDENTITY"
echo "Active AWS Region: $REGION"
echo "=== Identity Check Passed ==="
