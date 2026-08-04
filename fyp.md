# Codex Project Brief: AWS Academy Smart Parking IoT Prototype

You are Codex acting as a senior AWS serverless IoT engineer. Read this whole file first, then generate a complete working repository for an FYP prototype.

The project is a **Secure and Reliable Cloud-Native Smart Parking Management System using ESP32 Ultrasonic Sensors**. The goal is not to build a complicated web application. The goal is to build a meaningful AWS cloud solution that can be tested in an **AWS Academy Learner Lab / AWS Academy account** with limited credits and possible permission restrictions.

## 1. Main Objective

Create a working MVP that demonstrates this full cloud architecture:

```text
ESP32 + HC-SR04 ultrasonic sensor
        |
        | MQTT over TLS
        v
AWS IoT Core
        |
        | IoT Topic Rule
        v
AWS Lambda: sensor ingestion and validation
        |
        v
Amazon DynamoDB: live slot state + event history
        |
        v
Amazon API Gateway + Lambda: dashboard API
        |
        v
Amazon S3 Static Website Hosting: cloud-hosted dashboard
        |
        v
Amazon S3 report storage + Amazon CloudWatch logs
```

The project must be simple enough for a student to deploy, explain, test, and present inside AWS Academy, but it must still feel like a complete cloud solution.

The dashboard must be served from **Amazon S3 Static Website Hosting**, not from a local computer. Local hosting may only be mentioned as an optional developer debugging method, not as the official deployment method.

## 2. Important AWS Academy Constraints

Design this for AWS Academy, not a normal unrestricted AWS production account.

Assume the account may have these limitations:

* Limited AWS credits.
* Limited IAM permissions.
* Existing role named `LabRole` or `VocLabs` may be provided.
* Creating new IAM users, custom admin roles, or complex IAM policies may fail.
* Some services may be unavailable or restricted.
* Long-running EC2 instances may waste credits.
* Domain registration and Route 53 hosted zones should not be used.
* Advanced or expensive services should be avoided.

Therefore:

* Do **not** use EC2, ALB, Auto Scaling Group, RDS, EKS, ECS, Route 53, CloudFront, Amplify, Cognito, OpenSearch, Kinesis, IoT Analytics, IoT Events, or paid production-style architecture.
* Do **not** make customer-managed KMS keys or Secrets Manager core requirements.
* Do **not** create IAM users.
* Do **not** hardcode AWS access keys, secrets, certificates, or private keys in source code.
* Use the existing `LabRole` or `VocLabs` role for Lambda execution.
* Use serverless services that are low-cost and easy to clean up.
* Provide cleanup scripts.
* Terraform should fail clearly if AWS Academy blocks any required permission.

## 3. Required AWS Services

Use these core AWS services:

1. **AWS IoT Core**

   * Receive MQTT telemetry from ESP32 or test publisher.
   * Use topic pattern:

     ```text
     smart-parking/slot/{slotId}/telemetry
     ```
   * Example:

     ```text
     smart-parking/slot/A01/telemetry
     ```

2. **AWS IoT Rule**

   * Rule SQL should capture telemetry from:

     ```text
     smart-parking/slot/+/telemetry
     ```
   * Send matching messages to the ingestion Lambda.
   * Use rule SQL equivalent to `SELECT *, topic() AS mqttTopic FROM 'smart-parking/slot/+/telemetry'` so Lambda can extract `slotId`.

3. **AWS Lambda**

   * `ingest_sensor_data`: triggered by AWS IoT Rule.
   * `dashboard_api`: triggered by API Gateway.
   * Implement daily report generation inside `dashboard_api`; do not create a third Lambda.

4. **Amazon DynamoDB**

   * Table 1: `ParkingSlotState`
   * Table 2: `ParkingEvents`

5. **Amazon S3**

   * Bucket 1: S3 Static Website Hosting for dashboard.
   * Bucket 2: Report storage and generated CSV files.
   * Dashboard must be cloud-hosted through S3.

6. **Amazon API Gateway**

   * Use API Gateway **HTTP API**, not REST API, to keep Terraform, routing, and cost simple.
   * Expose endpoints for the S3 dashboard.

7. **Amazon CloudWatch**

   * Lambda logs.
   * Basic observability evidence.

## 4. Infrastructure as Code Requirement

Use **Terraform**, not CloudFormation.

Create this structure:

```text
infra/
└── terraform/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── providers.tf
    ├── versions.tf
    ├── lambda.tf
    ├── dynamodb.tf
    ├── s3_dashboard.tf
    ├── s3_reports.tf
    ├── api_gateway.tf
    ├── iot_core.tf
    └── README.md
```

Terraform must create and manage:

```text
- DynamoDB table: ParkingSlotState
- DynamoDB table: ParkingEvents
- S3 bucket for dashboard static website hosting
- S3 bucket for reports
- S3 website hosting configuration
- S3 bucket policy for public read access to dashboard objects only
- Lambda function: ingest_sensor_data
- Lambda function: dashboard_api
- API Gateway routes
- Lambda permissions for API Gateway
- IoT Topic Rule
- Lambda permission for IoT Core to invoke ingestion Lambda
- CloudWatch log groups where applicable
```

Terraform must create the dashboard bucket and website configuration, but `scripts/deploy.sh` must upload the frontend files after `terraform apply`. This is required because `frontend/config.js` depends on the API Gateway URL produced by Terraform.

Terraform must output:

```text
- dashboard_url
- api_gateway_url
- dashboard_bucket_name
- reports_bucket_name
- slot_state_table_name
- events_table_name
- iot_topic_pattern
- ingest_lambda_name
- dashboard_api_lambda_name
```

## 5. AWS Academy LabRole / VocLabs Role Requirement

Terraform must use the existing AWS Academy role for services that require an execution role.

Support both role names:

```text
LabRole
VocLabs
```

The deploy script should try to detect the role automatically:

```bash
LAB_ROLE_ARN=$(aws iam get-role --role-name LabRole --query 'Role.Arn' --output text 2>/dev/null)

if [ -z "$LAB_ROLE_ARN" ] || [ "$LAB_ROLE_ARN" = "None" ]; then
  LAB_ROLE_ARN=$(aws iam get-role --role-name VocLabs --query 'Role.Arn' --output text 2>/dev/null)
fi
```

If both fail, the script must ask the user to manually provide the role ARN.

Terraform variable:

```hcl
variable "lab_role_arn" {
  description = "Existing AWS Academy LabRole or VocLabs role ARN used by Lambda functions"
  type        = string
}
```

Use this role for Lambda:

```hcl
resource "aws_lambda_function" "ingest_sensor_data" {
  function_name = "${var.project_name}-ingest-sensor-data"
  role          = var.lab_role_arn
  ...
}

resource "aws_lambda_function" "dashboard_api" {
  function_name = "${var.project_name}-dashboard-api"
  role          = var.lab_role_arn
  ...
}
```

Do not create new IAM users.
Do not create custom administrator roles.
Do not hardcode AWS credentials.
Do not commit AWS keys, certificates, or private keys.

## 6. Permission Failure Behaviour

Terraform should fail clearly if AWS Academy blocks any required permission.

Do not silently fall back to local hosting if S3 website hosting, public bucket policy, IoT Rule, Lambda permission, or API Gateway creation fails.

Example failure message:

```text
Deployment failed because the AWS Academy account does not allow changing S3 public access or bucket policy.
This is an AWS Academy permission limitation, not a project architecture issue.
```

Document common AWS Academy permission problems in `AWS_ACADEMY_DEPLOYMENT_GUIDE.md`.

## 7. Repository Structure

Generate a clean repository with this structure:

```text
smart-parking-aws-academy/
├── README.md
├── ARCHITECTURE.md
├── AWS_ACADEMY_DEPLOYMENT_GUIDE.md
├── .gitignore
├── .env.example
├── backend/
│   ├── ingest_sensor_data/
│   │   ├── app.py
│   │   └── requirements.txt
│   ├── dashboard_api/
│   │   ├── app.py
│   │   └── requirements.txt
│   └── shared/
│       ├── parking_logic.py
│       └── ingestion_service.py
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── config.js.example
├── firmware/
│   └── esp32_hcsr04_aws_iot/
│       ├── esp32_hcsr04_aws_iot.ino
│       ├── README.md
│       └── secrets_template.h
├── infra/
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── providers.tf
│       ├── versions.tf
│       ├── lambda.tf
│       ├── dynamodb.tf
│       ├── s3_dashboard.tf
│       ├── s3_reports.tf
│       ├── api_gateway.tf
│       ├── iot_core.tf
│       └── README.md
├── scripts/
│   ├── check_aws_identity.sh
│   ├── find_lab_role.sh
│   ├── package_lambdas.sh
│   ├── generate_frontend_config.sh
│   ├── deploy.sh
│   ├── destroy.sh
│   ├── publish_sample_aws_cli.sh
│   ├── create_iot_thing_and_cert.sh
│   └── get_outputs.sh
├── simulator/
│   ├── publish_sequence_aws_cli.py
│   ├── publish_mqtt_with_cert.py
│   └── sample_payloads/
│       ├── occupied.json
│       ├── available.json
│       └── sensor_error.json
└── tests/
    ├── test_parking_logic.py
    ├── test_ingestion_service.py
    ├── test_dashboard_api.py
    └── sample_events/
        └── iot_event.json
```

## 8. Data Model

### DynamoDB Table: ParkingSlotState

Use `slotId` as the partition key.

Example item:

```json
{
  "slotId": "A01",
  "status": "OCCUPIED",
  "distanceCm": 14.2,
  "confidence": 0.91,
  "lastSeenEpoch": 1781510400,
  "lastSeenIso": "2026-06-15T12:00:00Z",
  "sensorHealth": "ONLINE",
  "currentSessionId": "A01-1781510400-a1b2c3d4",
  "currentSessionStartedEpoch": 1781510400,
  "updatedBy": "iot"
}
```

Supported stored and presentation status values:

```text
AVAILABLE
OCCUPIED
SENSOR_ERROR
MAINTENANCE
OFFLINE
```

`OFFLINE` is presentation-only and must not be persisted as the live status by a scheduled job.

### DynamoDB Table: ParkingEvents

Use:

```text
Partition key: slotId
Sort key: eventKey
```

`eventKey` must be collision-safe and chronologically sortable:

```text
{eventTimeWithMilliseconds}#{eventId}
```

Keep `eventTime` and `eventId` as separate attributes for API responses and reports. Generate `eventTime` from authoritative Lambda receive time in UTC with millisecond precision, generate `eventId` with UUID v4, and concatenate them to produce `eventKey`.

Example item:

```json
{
  "slotId": "A01",
  "eventKey": "2026-06-15T12:00:00.123Z#550e8400-e29b-41d4-a716-446655440000",
  "eventTime": "2026-06-15T12:00:00.123Z",
  "eventId": "550e8400-e29b-41d4-a716-446655440000",
  "eventType": "STATUS_CHANGE",
  "previousStatus": "AVAILABLE",
  "newStatus": "OCCUPIED",
  "distanceCm": 14.2,
  "confidence": 0.91,
  "sessionId": "A01-1781510400-a1b2c3d4",
  "billingAmountRM": 0.0,
  "rawPayload": {
    "distanceCm": 14.2,
    "status": "OCCUPIED"
  }
}
```

## 9. MQTT Payload Format

The ESP32 or simulator should publish JSON like this:

```json
{
  "slotId": "A01",
  "distanceCm": 14.2,
  "status": "OCCUPIED",
  "confidence": 0.91,
  "timestamp": "2026-06-15T12:00:00Z",
  "deviceId": "esp32-A01",
  "firmwareVersion": "0.1.0"
}
```

The system must handle missing optional fields safely.

Minimum required field:

```json
{
  "distanceCm": 14.2
}
```

If `slotId` is missing from the payload, extract it from the MQTT topic when possible.

## 10. Sensor Validation Logic

Implement validation in:

```text
backend/shared/parking_logic.py
```

Use these default constants:

```python
MIN_DISTANCE_CM = 2
MAX_DISTANCE_CM = 400
OCCUPIED_THRESHOLD_CM = 30
STALE_AFTER_SECONDS = 60
GRACE_PERIOD_MINUTES = 10
HOURLY_RATE_RM = 2.00
```

Rules:

1. If `distanceCm` is missing, not numeric, lower than 2, or greater than 400:

   * status = `SENSOR_ERROR`
   * confidence = `0.0`

2. If distance is valid and `distanceCm <= 30`:

   * status = `OCCUPIED`

3. If distance is valid and `distanceCm > 30`:

   * status = `AVAILABLE`

4. If payload includes `status`, the cloud should still validate distance and not blindly trust the device.

5. Compute confidence if missing:

   * Use `round(min(1.0, max(0.1, abs(distanceCm - 30) / 30)), 2)`.
   * Very close to the threshold produces lower confidence; far from the threshold produces higher confidence.
   * If confidence is supplied, accept only numeric values from `0.0` to `1.0`; otherwise compute it.

6. If current time minus `lastSeenEpoch` is more than 60 seconds:

   * API response should show sensor health as `OFFLINE`.

Use Lambda receive time as the authoritative time for `lastSeenEpoch`, session timing, event ordering, and stale detection. Preserve a valid device-provided timestamp only as optional diagnostic metadata.

`OFFLINE` is a derived API/dashboard presentation state, not a status written to DynamoDB by a scheduled process. When a reading is stale, return `sensorHealth: "OFFLINE"` and present the effective status as `OFFLINE`, while retaining the last persisted sensor status for when telemetry resumes.

Do not require a scheduled Lambda.

### DynamoDB Numeric Handling

Python `boto3` DynamoDB operations must not receive native `float` values. Recursively convert all decimal-capable numbers, including values inside `rawPayload`, to `decimal.Decimal` before writing to DynamoDB. Convert floats using `Decimal(str(value))` to avoid binary floating-point artifacts. Convert `Decimal` values back to JSON-safe `int` or `float` values before returning API or Lambda responses.

## 11. Basic Billing Logic

Keep billing simple. This is only for FYP demonstration.

When slot changes:

```text
AVAILABLE → OCCUPIED: start a session
OCCUPIED → AVAILABLE: end session and calculate charge
```

When starting a session, persist both `currentSessionId` and `currentSessionStartedEpoch` in `ParkingSlotState`. When ending a session, calculate duration from `currentSessionStartedEpoch`, write the final duration and billing values to the event, and remove both current-session attributes from the live state.

Generate a collision-safe session ID using `{slotId}-{startEpoch}-{uuid8}`, where `uuid8` is the first eight hexadecimal characters of a UUID v4.

Session lifecycle must use the persisted session attributes, not only the immediately previous status:

* A valid `OCCUPIED` reading starts a session only when no `currentSessionId` exists.
* A valid `AVAILABLE` reading ends and bills an existing session, even if the immediately previous status was `SENSOR_ERROR`.
* `SENSOR_ERROR` readings never start or end a session and must preserve any active session attributes.
* Entering `MAINTENANCE` cancels any active session without billing and removes the current-session attributes. Write an `ADMIN_OVERRIDE` event that records the cancellation.

Charge rule:

```text
First 10 minutes: RM 0.00
After 10 minutes: RM 2.00 per started hour, calculated from the total session duration
```

Use this exact formula:

```python
charge_rm = 0.0 if duration_minutes <= 10 else math.ceil(duration_minutes / 60) * 2.00
```

Example:

```text
5 minutes = RM 0.00
15 minutes = RM 2.00
61 minutes = RM 4.00
```

Do not integrate a real payment gateway.

## 12. Lambda: ingest_sensor_data

Implement:

```text
backend/ingest_sensor_data/app.py
```

Responsibilities:

* Receive IoT Rule event.
* Accept both direct JSON and wrapped IoT Rule payload formats.
* Determine `slotId`.
* Validate distance.
* Compare previous status from DynamoDB.
* Update `ParkingSlotState`.
* Write event to `ParkingEvents` if:

  * first reading for the slot,
  * the stored status changes, including entering or recovering from `SENSOR_ERROR`,
  * an admin override occurs.
* Do not create repeated events for consecutive readings that remain in `SENSOR_ERROR`.
* Start and end parking sessions according to the session lifecycle rules in Section 11.
* Return useful JSON for logs/testing.

Implement the reusable AWS persistence and ingestion operation in `backend/shared/ingestion_service.py` so both the IoT Lambda handler and the dashboard API `/ingest-test` fallback use the same validation, state update, event, and billing behavior without duplicated logic. Keep pure validation and billing calculations in `backend/shared/parking_logic.py`.

If a slot is in `MAINTENANCE`, normal sensor telemetry must update its latest distance, last-seen time, confidence, and sensor health, but must not replace the `MAINTENANCE` status. Only `POST /admin/slot/{slotId}/available` may clear maintenance mode.

For first readings, status transitions, session starts, and session ends, use DynamoDB `TransactWriteItems` to update state and insert the event together. For a new slot, condition on `attribute_not_exists(slotId)`. For an existing slot, condition on the previously read `status` and `currentSessionId`, including whether the session attribute was absent. On a conditional conflict, read the latest state and retry once; if it conflicts again, log and return a clear retryable error. Ordinary readings that do not create an event may use `UpdateItem`.

Use environment variables:

```text
SLOT_STATE_TABLE
EVENTS_TABLE
REPORTS_BUCKET
PROJECT_NAME
```

Use `boto3`. Avoid external dependencies unless necessary.

## 13. Lambda: dashboard_api

Implement:

```text
backend/dashboard_api/app.py
```

Required endpoints:

```text
GET /health
GET /slots
GET /slots/{slotId}
GET /events?slotId=A01&limit=20
POST /reports/daily
POST /ingest-test
POST /admin/slot/{slotId}/maintenance
POST /admin/slot/{slotId}/available
OPTIONS /{proxy+}
```

Keep admin endpoints simple. Do not implement login/auth for this MVP. Explain that production admin authentication is out of scope for the AWS Academy prototype.

`POST /ingest-test` is a documented AWS Academy fallback for demo use when IoT Rule creation is blocked. It must accept the same JSON payload as MQTT telemetry, require `slotId` in the request body because no MQTT topic is available, and call the shared ingestion operation. Clearly label this endpoint as prototype-only and unauthenticated.

Admin endpoint behavior:

* `POST /admin/slot/{slotId}/maintenance` sets and locks the slot status to `MAINTENANCE`, cancels any active session without billing, and writes an `ADMIN_OVERRIDE` event.
* `POST /admin/slot/{slotId}/available` clears maintenance, sets the slot to `AVAILABLE`, writes an `ADMIN_OVERRIDE` event, and does not start or end a billable parking session.

Validate every `slotId`, whether obtained from a topic, path, query, or request body, against `^[A-Za-z0-9_-]{1,32}$`. Reject invalid values with HTTP `400` or a clear ingestion error. For `/events`, default `limit` to `20` and accept only integer values from `1` to `100`.

API response must include CORS headers:

```text
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type
Access-Control-Allow-Methods: GET,POST,OPTIONS
```

For production, documentation should say the CORS origin should be restricted to the S3 dashboard domain.

Example `/slots` response:

```json
{
  "slots": [
    {
      "slotId": "A01",
      "status": "OCCUPIED",
      "distanceCm": 14.2,
      "confidence": 0.91,
      "sensorHealth": "ONLINE",
      "lastSeenIso": "2026-06-15T12:00:00Z",
      "isStale": false
    }
  ],
  "summary": {
    "total": 4,
    "available": 2,
    "occupied": 1,
    "offline": 1,
    "sensorError": 0
  }
}
```

### Daily Report Contract

`POST /reports/daily` must:

* Accept an optional JSON body such as `{"date": "2026-06-15"}`.
* Default to the current date in the `Asia/Kuala_Lumpur` timezone when `date` is omitted.
* Validate the date as `YYYY-MM-DD`.
* Convert the requested Kuala Lumpur local-day boundaries to UTC, then scan the small MVP `ParkingEvents` table and filter records by `eventTime`. Document that a production system would add a date-based index or reporting pipeline.
* Generate CSV columns: `slotId,eventTime,eventType,previousStatus,newStatus,distanceCm,confidence,sessionId,durationMinutes,billingAmountRM`.
* Upload the report to `s3://REPORTS_BUCKET/daily/YYYY-MM-DD/parking-events.csv`.
* Return JSON containing `date`, `recordCount`, `bucket`, and `key`. Do not return a public S3 URL because the reports bucket must remain private.

## 14. S3-Hosted Frontend Dashboard

Build a simple static dashboard only.

Do not use React, Next.js, Vue, Angular, Tailwind build tools, Vite, Node server, or complicated frontend tooling.

Use:

```text
frontend/index.html
frontend/style.css
frontend/app.js
frontend/config.js.example
```

Dashboard features:

* Automatically reads API Gateway URL from `config.js`.
* Cards for each slot.
* Total available / occupied / offline counters.
* Last updated time.
* Events table.
* Button to trigger sample report generation.
* Clear visual status labels:

  * AVAILABLE
  * OCCUPIED
  * SENSOR_ERROR
  * OFFLINE
  * MAINTENANCE

The official dashboard must be accessed through the Terraform output:

```text
dashboard_url = http://bucket-name.s3-website-region.amazonaws.com
```

The dashboard must not require opening `index.html` locally.

### Frontend Config

Use a generated `frontend/config.js` file:

```javascript
window.SMART_PARKING_CONFIG = {
  API_BASE_URL: "https://xxxx.execute-api.us-east-1.amazonaws.com/dev"
};
```

Create:

```text
scripts/generate_frontend_config.sh
```

This script should generate `frontend/config.js` using the API Gateway URL from Terraform outputs.

## 15. S3 Dashboard Hosting Requirements

Create an S3 bucket specifically for the dashboard.

Required bucket naming pattern:

```text
${project_name}-dashboard-${account_id}-${region}
```

Configure:

```text
- Static website hosting enabled
- index.html as index document
- Public read access for dashboard files
- Bucket policy allowing s3:GetObject for public users
- Block Public Access adjusted only for this dashboard bucket
```

Bucket policy should allow public read only for objects:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadForWebsite",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::BUCKET_NAME/*"
    }
  ]
}
```

Do not allow public write access.

Document this:

```text
For this AWS Academy prototype, the S3 dashboard website may use HTTP because S3 Static Website Hosting does not provide HTTPS directly. In production, CloudFront with HTTPS would be added, but CloudFront is excluded from this FYP MVP to reduce AWS Academy complexity.
```

## 16. ESP32 Firmware

Create Arduino IDE firmware for ESP32 + HC-SR04.

Files:

```text
firmware/esp32_hcsr04_aws_iot/esp32_hcsr04_aws_iot.ino
firmware/esp32_hcsr04_aws_iot/secrets_template.h
firmware/esp32_hcsr04_aws_iot/README.md
```

Assume:

```text
HC-SR04 TRIG pin = GPIO 5
HC-SR04 ECHO pin = GPIO 18
Publish interval = 5 seconds
Topic = smart-parking/slot/A01/telemetry
```

Firmware requirements:

* Connect to Wi-Fi.
* Connect to AWS IoT Core using MQTT over TLS.
* Use certificates from `secrets.h`.
* Measure distance from HC-SR04.
* Publish JSON payload.
* Reconnect if Wi-Fi/MQTT disconnects.
* Include clear comments for where to paste:

  * Wi-Fi SSID/password
  * AWS IoT endpoint
  * Amazon Root CA
  * device certificate
  * private key

Do not commit real certificates. Include `.gitignore` entries for:

```text
secrets.h
certs/
*.pem
*.key
*.crt
```

## 17. Simulator and Testing Without Real ESP32

Because AWS Academy testing may be easier before hardware is ready, include simulator options.

### Option A: AWS CLI IoT Data Publish

Create:

```text
scripts/publish_sample_aws_cli.sh
```

It should support:

```bash
./scripts/publish_sample_aws_cli.sh A01 14.2
./scripts/publish_sample_aws_cli.sh A02 80
./scripts/publish_sample_aws_cli.sh A03 999
```

Internally it should use:

```bash
IOT_DATA_ENDPOINT=$(aws iot describe-endpoint \
  --endpoint-type iot:Data-ATS \
  --query endpointAddress \
  --output text)

aws iot-data publish \
  --endpoint-url "https://${IOT_DATA_ENDPOINT}" \
  --topic "smart-parking/slot/A01/telemetry" \
  --cli-binary-format raw-in-base64-out \
  --payload '{"distanceCm": 14.2, "deviceId": "sim-A01"}'
```

Make region configurable and fail with a clear message if the IoT data endpoint cannot be discovered.

### Option B: Python MQTT Publisher with Certificate

Create:

```text
simulator/publish_mqtt_with_cert.py
```

Use `paho-mqtt`.

It should read these values from environment variables or CLI arguments:

```text
AWS_IOT_ENDPOINT
CLIENT_ID
TOPIC
ROOT_CA_PATH
CERT_PATH
PRIVATE_KEY_PATH
```

Also create:

```text
simulator/publish_sequence_aws_cli.py
```

It should simulate:

```text
1. A01 available
2. A01 occupied
3. A01 still occupied
4. A01 available
5. A02 sensor error
6. A03 offline simulation by not sending updates
```

## 18. Deployment Scripts

Create these scripts:

### `scripts/check_aws_identity.sh`

Should run:

```bash
aws sts get-caller-identity
aws configure get region
```

and print useful guidance.

### `scripts/find_lab_role.sh`

Should try:

```bash
aws iam get-role --role-name LabRole --query 'Role.Arn' --output text
```

Then try:

```bash
aws iam get-role --role-name VocLabs --query 'Role.Arn' --output text
```

If denied, explain that AWS Academy may restrict IAM lookup and the user can copy the role ARN from the AWS Console if visible.

### `scripts/package_lambdas.sh`

Should package both Lambdas into zip files for Terraform deployment. Each zip must include the shared `parking_logic.py` and `ingestion_service.py` modules at importable paths. The dashboard API package must be able to call the same reusable ingestion operation used by the IoT handler.

### `scripts/generate_frontend_config.sh`

Should generate:

```text
frontend/config.js
```

using the API Gateway URL from Terraform output.

### `scripts/deploy.sh`

Should:

```text
1. Check AWS identity.
2. Detect AWS region.
3. Detect LabRole or VocLabs role ARN.
4. Package Lambda functions.
5. Run terraform init.
6. Run terraform plan.
7. Run terraform apply.
8. Read Terraform outputs.
9. Generate frontend/config.js using API Gateway URL.
10. Upload `index.html`, `style.css`, `app.js`, and generated `config.js` to the S3 dashboard bucket.
11. Print the final S3 dashboard website URL.
12. Print sample IoT publish commands.
```

The final output should look like:

```text
Deployment complete.

Dashboard URL:
http://smart-parking-fyp-dashboard-xxxx.s3-website-us-east-1.amazonaws.com

API Gateway URL:
https://xxxx.execute-api.us-east-1.amazonaws.com/dev

Test publish:
./scripts/publish_sample_aws_cli.sh A01 14.2
./scripts/publish_sample_aws_cli.sh A02 80
./scripts/publish_sample_aws_cli.sh A03 999
```

### `scripts/destroy.sh`

Should destroy Terraform-managed resources.

### `scripts/get_outputs.sh`

Should print:

```text
API URL
Dashboard URL
DynamoDB table names
S3 bucket names
IoT topic pattern
Lambda function names
```

### `scripts/create_iot_thing_and_cert.sh`

Optional helper:

* Create IoT Thing for one slot.
* Create certificate and private key.
* Attach IoT policy.
* Save certs under `certs/`.
* Warn user not to commit certs.
* If AWS Academy denies certificate creation, print manual console steps.

## 19. Manual AWS Academy Deployment Guide

Create:

```text
AWS_ACADEMY_DEPLOYMENT_GUIDE.md
```

It must explain the process clearly for beginners:

1. Start AWS Academy Learner Lab.
2. Open AWS Console.
3. Copy AWS CLI credentials from the lab.
4. Configure local terminal:

   ```bash
   aws configure
   ```
5. Verify:

   ```bash
   aws sts get-caller-identity
   ```
6. Choose region.
7. Deploy:

   ```bash
   cd smart-parking-aws-academy
   chmod +x scripts/*.sh
   ./scripts/deploy.sh
   ```
8. Publish test payload:

   ```bash
   ./scripts/publish_sample_aws_cli.sh A01 14.2
   ./scripts/publish_sample_aws_cli.sh A02 80
   ./scripts/publish_sample_aws_cli.sh A03 999
   ```
9. Open the S3 dashboard URL from Terraform output.
10. Screenshot evidence for FYP:

    * AWS IoT Rule
    * Lambda logs in CloudWatch
    * DynamoDB updated slot state
    * API Gateway endpoint
    * S3 Static Website dashboard
    * S3 report file
11. Cleanup:

    ```bash
    ./scripts/destroy.sh
    ```

## 20. Security Requirements

Implement and document these security controls:

* MQTT over TLS for ESP32 device connection.
* AWS IoT certificate-based authentication for real device.
* IoT policy should only allow required topics.
* No hardcoded AWS access keys.
* No real certificates committed.
* Lambda uses role-based permissions through AWS Academy `LabRole` or `VocLabs`.
* DynamoDB and S3 use default encryption.
* Input validation for all payloads.
* CORS configured for prototype.
* Admin functions are marked prototype-only.
* S3 dashboard bucket allows public read only, never public write.
* Production recommendation: use CloudFront + HTTPS + restricted CORS origin.

Create a section in `ARCHITECTURE.md` mapping Security Pillar evidence.

## 21. Reliability Requirements

Implement and document these reliability controls:

* Serverless architecture reduces EC2 failure risk.
* DynamoDB stores live and historical data.
* Sensor stale/offline detection.
* Sensor error handling.
* Lambda logs errors to CloudWatch.
* Dashboard displays stale/offline slots.
* Deployment can be recreated using Terraform and scripts.
* Cleanup script prevents unnecessary cost.
* Define an `enable_pitr` Terraform variable that defaults to `false`. Enable DynamoDB Point-in-Time Recovery only when the user explicitly sets it to `true`; if AWS Academy denies it, Terraform must fail clearly and the guide must tell the user to retry with `enable_pitr = false`.

Create a section in `ARCHITECTURE.md` mapping Reliability Pillar evidence.

## 22. Fallback Plan if AWS Academy Blocks Something

Add a troubleshooting section.

If IoT Rule creation fails:

* Provide manual AWS Console steps to create the rule.
* Also provide the fallback `/ingest-test` API endpoint that calls the same reusable ingestion operation through API Gateway for demo testing.

If API Gateway creation fails:

* Keep backend Lambda code still usable.
* Document the exact Terraform error.

If S3 dashboard hosting fails:

* Do not silently switch the official deployment to local hosting.
* Print a clear message that AWS Academy blocked S3 public website hosting or bucket policy configuration.
* State that this is an AWS Academy account limitation, not a project architecture issue.

If IAM `get-role` or `iam:PassRole` fails:

* Explain how to manually find or paste the LabRole/VocLabs role ARN.
* Do not ask the user to create a new admin role.

If IoT certificate creation fails:

* Tell the user to create the Thing and certificate manually in AWS IoT Core Console.
* The project must still be testable using AWS CLI `iot-data publish`.

## 23. README Requirements

The README must include:

* Project overview.
* Architecture diagram in text form.
* Required tools:

  * AWS CLI
  * Terraform
  * Python 3.10+
  * Arduino IDE for ESP32 firmware
  * Optional: paho-mqtt
* Quick start.
* AWS Academy notes.
* Terraform deployment.
* Testing with sample publisher.
* S3 dashboard usage.
* ESP32 setup.
* Cleanup.
* Common errors and fixes.

## 24. Code Quality Requirements

* Keep code beginner-friendly.
* Add comments where useful.
* Use environment variables.
* Avoid unnecessary dependencies.
* Use Python standard library where possible.
* Include unit tests for `parking_logic.py`, ingestion/session behavior, and dashboard API routing.
* Include type hints where practical.
* Handle errors gracefully.
* Print useful logs.
* Do not overengineer.

Required test scenarios:

* Distance boundary validation at 2 cm, 30 cm, and 400 cm, plus missing, non-numeric, and out-of-range values.
* Exact billing examples for 5, 15, and 61 minutes.
* Session start, repeated occupied reading, sensor error during a session, recovery to available, and session completion.
* Maintenance override cancellation and maintenance lock behavior.
* Collision-safe `eventKey` creation and DynamoDB `Decimal` serialization.
* `/ingest-test`, stale/offline presentation, `/events`, admin routes, and daily report validation using mocked AWS clients.

## 25. Definition of Done

The project is complete only when a student can:

```text
1. Deploy the AWS resources using Terraform in AWS Academy.
2. Use LabRole or VocLabs role for Lambda execution.
3. Publish a sample MQTT payload to AWS IoT Core.
4. Trigger the IoT Rule and ingestion Lambda.
5. See logs in CloudWatch.
6. See slot state updated in DynamoDB.
7. Open the dashboard from an S3 Static Website URL.
8. See live parking slot status from API Gateway.
9. Generate or simulate a CSV report.
10. Destroy the Terraform stack and clean up resources.
11. Later replace the simulator with a real ESP32 + HC-SR04 using MQTT over TLS.
```

Do not mark the project complete if the dashboard only works locally.

## 26. Do Not Build These

Do not build:

* Complex login system.
* Payment gateway.
* Mobile app.
* EC2 web server.
* ALB/ASG deployment.
* RDS database.
* Kubernetes/Docker deployment.
* Overly complex admin panel.
* Machine learning detection.
* Camera or number plate recognition.
* Multi-region disaster recovery.
* CloudFront for this MVP.
* Route 53 custom domain.

Keep it focused: **ESP32 ultrasonic sensor + AWS IoT Core + Lambda + DynamoDB + API Gateway + S3-hosted dashboard + Terraform + AWS Academy LabRole/VocLabs role**.
