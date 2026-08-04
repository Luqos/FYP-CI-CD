# AWS Academy Learner Lab Deployment & Troubleshooting Guide

This guide provides step-by-step instructions for deploying and presenting the Smart Parking Prototype inside an **AWS Academy Learner Lab** account.

## Step 1: Start AWS Academy Learner Lab

1. Sign in to AWS Academy and navigate to your **Learner Lab**.
2. Click **Start Lab** and wait until the status indicator turns green.
3. Click **AWS Details** and copy the **AWS CLI credentials** block.

## Step 2: Configure Local Credentials

On your local Windows computer:
1. Open PowerShell or Notepad and edit `C:\Users\<User>\.aws\credentials`:
   ```ini
   [default]
   aws_access_key_id=ASIA...
   aws_secret_access_key=...
   aws_session_token=...
   ```
2. Set default region:
   ```bash
   aws configure set region us-east-1
   aws sts get-caller-identity
   ```

## Step 3: Run One-Click Deployment

In Git Bash or PowerShell:

```bash
# Git Bash
./scripts/deploy.sh

# PowerShell
.\scripts\deploy.ps1
```

The script will automatically detect `LabRole` or `VocLabs`, run Terraform, generate frontend configuration, and upload website files to S3.

## Troubleshooting AWS Academy Permissions & Environment Errors

### 1. Windows Application Control / AppLocker Blocking Binary Execution (`terraform-provider-aws.exe`)
- **Symptom**: `An Application Control policy has blocked this file` when running `terraform` or `pytest`.
- **Cause**: Windows host security policies may restrict executing binary executables extracted into user profile subfolders (like `.terraform/providers/...`).
- **Fix**:
  - Run scripts inside **Git Bash** (`./scripts/deploy.sh`), or inside **WSL (Windows Subsystem for Linux)**.
  - Alternatively, execute deployment commands inside CloudShell or an AWS EC2 / Cloud9 development environment.

### 2. Permission Denied on IAM Role Lookup (`iam:GetRole`)
- **Symptom**: `find_lab_role.sh` reports AccessDenied.
- **Cause**: Some AWS Academy labs block `iam:GetRole` CLI calls.
- **Fix**: Open the AWS Console, navigate to IAM -> Roles, copy the ARN for `LabRole` (e.g. `arn:aws:iam::123456789012:role/LabRole`), and set:
  ```bash
  export LAB_ROLE_ARN="arn:aws:iam::123456789012:role/LabRole"
  ```

### 3. S3 Public Access Block Error
- **Symptom**: Terraform fails setting S3 bucket policy or public access block.
- **Cause**: AWS Academy account has account-level S3 block public access enabled.
- **Fix**: Use the fallback API endpoint (`/ingest-test`) and document that AWS Academy account policy restricts public S3 website hosting.

### 4. IoT Rule Creation Blocked
- **Symptom**: Terraform fails creating `aws_iot_topic_rule`.
- **Fix**: Use the prototype fallback API endpoint (`POST /ingest-test`) via API Gateway to ingest sensor telemetry directly.

## Presentation & Evidence Screenshots Checklist

For your Final Year Project (FYP) demonstration, capture screenshots of:
1. AWS IoT Core Topic Rule configuration console view.
2. CloudWatch Log Group logs for `ingest_sensor_data` Lambda.
3. DynamoDB `ParkingSlotState` items table scan.
4. DynamoDB `ParkingEvents` event audit log table scan.
5. S3 Static Website hosted dashboard running in browser.
6. Private S3 report bucket containing `parking-events.csv`.
