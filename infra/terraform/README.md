# Terraform Infrastructure Module

This directory contains the Infrastructure as Code (IaC) configuration for deploying the **AWS Academy Smart Parking IoT Prototype**.

## Managed Resources

- **DynamoDB Tables**: `ParkingSlotState` and `ParkingEvents`
- **S3 Buckets**: Dashboard Static Website Hosting bucket and Private Reports storage bucket
- **Lambda Functions**: `ingest_sensor_data` and `dashboard_api`
- **API Gateway**: HTTP API with CORS configuration
- **AWS IoT Core**: Topic Rule routing `smart-parking/slot/+/telemetry` to Lambda

## Usage

```bash
# Package Lambdas first
../../scripts/package_lambdas.sh

# Initialize Terraform
terraform init

# Plan deployment with AWS Academy role
terraform plan -var="lab_role_arn=arn:aws:iam::ACCOUNT_ID:role/LabRole"

# Apply deployment
terraform apply -var="lab_role_arn=arn:aws:iam::ACCOUNT_ID:role/LabRole" -auto-approve
```
