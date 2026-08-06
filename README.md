# AWS Academy Smart Parking IoT Prototype 🚗☁️

> **A Meaningful Cloud Solution Architected for Security, Reliability, and Infinite Scale.**

This project transcends traditional monolithic university IoT projects. It is a **100% Serverless and Event-Driven** Smart Parking Management System built specifically for deployment inside AWS Academy Learner Lab environments. 

By adopting a cloud-native serverless architecture (AWS Lambda, API Gateway, DynamoDB), this system fundamentally aligns computing costs with real-world physical events. It scales instantly from zero to thousands of concurrent vehicles processing telemetry, ensuring cost-efficiency and zero server maintenance.

---

## 🌟 Key Features & The Two Pillars

Built around the **AWS Well-Architected Framework**:

### 🔒 Pillar 1: Security (Defense-in-Depth)
- **Encryption in Transit (mTLS):** ESP32 sensors authenticate to the cloud using Mutual TLS (mTLS) with X.509 device certificates.
- **Multi-Layer Input Validation:** Strict regex and numeric bounds checking drop malformed physical telemetry payloads before they touch the database.
- **XSS Prevention:** All data fetched from the cloud is aggressively sanitized on the dashboard.

### 🔄 Pillar 2: Reliability (Self-Healing)
- **Stale Sensor Detection (Offline Resilience):** The cloud proactively overwrites the frontend display to `OFFLINE` if a sensor goes silent for more than 60 seconds.
- **Atomic Transactions:** Uses DynamoDB `TransactWriteItems` to ensure slot status updates and event ledger logs succeed or fail together.
- **Graceful Degradation:** Hardware timeouts on the ESP32 prevent infinite blocking loops, auto-reconnecting seamlessly if Wi-Fi or MQTT drops.

---

## 🏗️ Cloud Architecture

```text
[Physical World]            [AWS Cloud Boundary]                   [Data & API Layer]
                                     
 ESP32 Hardware ───mTLS──► AWS IoT Core ──Rule──► Lambda Ingest ──Atomic──► DynamoDB Tables
 (X.509 Auth)              (Message Broker)       (Validation)               (NoSQL)
                                                                               ▲
                                                                               │
 S3 Frontend    ◄──HTTPS── API Gateway  ◄──────── Lambda API    ◄──────────────┘
 (Static Web)              (REST Routing)         (Business Logic)
```

The entire cloud infrastructure is defined through **Infrastructure as Code (Terraform)**, proving that the architecture is not a manual, fragile click-through setup, but a robust, version-controlled, and reproducible engineering solution. Complete with **GitHub Actions CI/CD pipelines** for automated testing and deployment.

---

## 🚀 Quick Start (Deployment)

### 1. Configure AWS Academy Credentials
Paste your temporary Learner Lab credentials into your terminal:
```bash
aws configure set region us-east-1
aws sts get-caller-identity
```

### 2. Run Automatic Deployment
The deployment scripts will automatically package Lambdas, apply Terraform, and deploy the React-style dashboard to S3.

**Bash (Git Bash / Linux / macOS):**
```bash
chmod +x scripts/*.sh
./scripts/deploy.sh
```

**PowerShell (Windows):**
```powershell
.\scripts\deploy.ps1
```

### 3. Test the Live System
Publish test sensor readings via the AWS CLI to watch the real-time cloud dashboard update:
```bash
./scripts/publish_sample_aws_cli.sh A01 14.2   # Slot A01 -> OCCUPIED
./scripts/publish_sample_aws_cli.sh A01 85.0   # Slot A01 -> AVAILABLE (Calculates billing)
```
Or run the fully automated sequence simulator:
```bash
python simulator/publish_sequence_aws_cli.py
```

### 4. Cleanup
Destroy all deployed AWS resources to save Learner Lab credits:
```bash
./scripts/destroy.sh
```
