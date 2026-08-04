#!/usr/bin/env bash
set -e

LAB_ROLE_ARN=$(aws iam get-role --role-name LabRole --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$LAB_ROLE_ARN" ] || [ "$LAB_ROLE_ARN" = "None" ]; then
    LAB_ROLE_ARN=$(aws iam get-role --role-name VocLabs --query 'Role.Arn' --output text 2>/dev/null || echo "")
fi

if [ -n "$LAB_ROLE_ARN" ] && [ "$LAB_ROLE_ARN" != "None" ]; then
    echo "$LAB_ROLE_ARN"
else
    echo "ERROR: Unable to detect 'LabRole' or 'VocLabs' IAM role in AWS account." >&2
    echo "Please ensure you are running inside AWS Academy Learner Lab or set LAB_ROLE_ARN manually." >&2
    exit 1
fi
