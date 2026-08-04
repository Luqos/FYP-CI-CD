# AWS Academy Smart Parking IoT Prototype

A secure, reliable, cloud-native Smart Parking Management System prototype built specifically for deployment inside **AWS Academy Learner Lab** environments.

## Architecture Overview

```text
ESP32 + HC-SR04 ultrasonic sensor / AWS CLI Simulator
        |
        | MQTT over TLS (Topic: smart-parking/slot/{slotId}/telemetry)
        v
AWS IoT Core (Topic Rule)
        |
        v
AWS Lambda (ingest_sensor_data)
        |
        v
Amazon DynamoDB (ParkingSlotState + ParkingEvents)
        |
        v
Amazon API Gateway HTTP API (dashboard_api Lambda)
        |
        v
Amazon S3 Static Website Hosting (Cloud-hosted Dashboard)
        |
        v
Amazon S3 Private Report Storage + Amazon CloudWatch Logs
```

## Prerequisites

- **AWS CLI** v2
- **HashiCorp Terraform** >= v1.3
- **Python** 3.10+
- **Git Bash** (or PowerShell for Windows execution)
- **Arduino IDE** (Optional, required only for physical ESP32 flashing)

## Quick Start (Deployment)

### 1. Configure AWS Academy Credentials
Paste temporary Learner Lab credentials into `~/.aws/credentials`:
```bash
aws configure set region us-east-1
aws sts get-caller-identity
```

### 2. Run Automatic Deployment
Run either the Bash script (via Git Bash) or PowerShell script:

**Bash (Git Bash):**
```bash
chmod +x scripts/*.sh
./scripts/deploy.sh
```

**PowerShell:**
```powershell
.\scripts\deploy.ps1
```

The script will automatically detect `LabRole` or `VocLabs`, package Lambda functions, deploy Terraform resources, generate `frontend/config.js`, and upload the static dashboard website to S3.

### 3. Test Telemetry Publishing

Publish test sensor readings via AWS CLI:
```bash
# Bash
./scripts/publish_sample_aws_cli.sh A01 14.2   # Slot A01 -> OCCUPIED
./scripts/publish_sample_aws_cli.sh A01 85.0   # Slot A01 -> AVAILABLE (Calculates billing)
./scripts/publish_sample_aws_cli.sh A02 999.0  # Slot A02 -> SENSOR_ERROR

# PowerShell
.\scripts\publish_sample_aws_cli.ps1 A01 14.2
```

Or run the full 2-slot automated sequence simulator:
```bash
python simulator/publish_sequence_aws_cli.py
```

### 4. Access Cloud Dashboard

Open the S3 static website URL printed by the deployment script:
`http://smart-parking-fyp-dashboard-ACCOUNT-region.s3-website-us-east-1.amazonaws.com`

## Repository Structure

```text
.
├── README.md
├── ARCHITECTURE.md
├── AWS_ACADEMY_DEPLOYMENT_GUIDE.md
├── backend/
│   ├── ingest_sensor_data/
│   ├── dashboard_api/
│   └── shared/
├── frontend/
├── firmware/
│   └── esp32_hcsr04_aws_iot/
├── infra/
│   └── terraform/
├── scripts/
├── simulator/
└── tests/
```

## Local Unit Testing

Run Python unit tests before deployment:
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r backend/ingest_sensor_data/requirements.txt
pip install pytest
pytest
```

## Cleanup

Destroy all deployed AWS resources to save Learner Lab credits:
```bash
./scripts/destroy.sh
# OR
.\scripts\destroy.ps1
```
