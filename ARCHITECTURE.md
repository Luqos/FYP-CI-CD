# Architecture & Well-Architected Framework Documentation

## System Architecture

The AWS Academy Smart Parking Management System is built on a serverless, event-driven IoT architecture.

### Component Map

1. **AWS IoT Core**: Acts as the central MQTT message broker. Receives device telemetry over TLS on topic `smart-parking/slot/{slotId}/telemetry`.
2. **AWS IoT Topic Rule**: Evaluates incoming telemetry SQL: `SELECT *, topic() AS mqttTopic FROM 'smart-parking/slot/+/telemetry'` and invokes `ingest_sensor_data` Lambda.
3. **ingest_sensor_data Lambda**: Performs server-side distance validation, status state machine transitions, session lifecycle tracking, and atomic DynamoDB updates.
4. **Amazon DynamoDB**:
   - `ParkingSlotState`: Partition key `slotId`. Stores current status, distance, confidence, last seen timestamp, and active session ID.
   - `ParkingEvents`: Partition key `slotId`, Sort key `eventKey` (`{eventTime}#{eventId}`). Chronologically sortable, immutable audit log of status changes and billing events.
5. **Amazon API Gateway HTTP API**: Serverless API Gateway routing requests to `dashboard_api` Lambda.
6. **dashboard_api Lambda**: Serves dashboard REST endpoints (`/slots`, `/events`, `/reports/daily`, `/ingest-test`, `/admin/...`).
7. **Amazon S3 Static Website Hosting**: Publicly hosts dashboard HTML/CSS/JS files without requiring EC2 instances.
8. **Amazon S3 Reports Bucket**: Private S3 bucket storing generated daily CSV parking reports.

---

## AWS Well-Architected Pillar Evidence

### Security Pillar Controls

- **MQTT over TLS**: Device communication with AWS IoT Core uses X.509 certificate authentication or IAM signed AWS CLI requests over TLS 1.2.
- **IAM Role Isolation**: Serverless Lambdas run under AWS Academy `LabRole` or `VocLabs` execution role with least-privilege AWS policies.
- **Private Data Storage**: Daily report CSV objects are stored in a strictly private S3 bucket (`block_public_acls = true`).
- **Public Website Boundaries**: Dashboard S3 bucket allows `s3:GetObject` read-only access for static assets; public write access is strictly blocked.
- **Zero Credentials in Repository**: Certificates, private keys, and AWS access keys are excluded via `.gitignore`.

### Reliability Pillar Controls

- **No Single Point of Failure (SPOF)**: Fully managed AWS serverless services automatically scale and distribute across Availability Zones.
- **Stale/Offline Telemetry Detection**: Sensor health dynamically presents `OFFLINE` if no telemetry is received within 60 seconds.
- **Atomic State Transitions**: DynamoDB `TransactWriteItems` ensures state updates and event logging execute atomically without partial failure or race conditions.
- **Infrastructure as Code**: Entire stack is reproducible and testable via Terraform.
