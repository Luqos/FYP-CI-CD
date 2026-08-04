output "dashboard_url" {
  description = "Public URL for the S3 static website hosting dashboard"
  value       = "http://${aws_s3_bucket_website_configuration.dashboard.website_endpoint}"
}

output "api_gateway_url" {
  description = "Base URL of the API Gateway HTTP API"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "dashboard_bucket_name" {
  description = "S3 bucket name hosting the static dashboard"
  value       = aws_s3_bucket.dashboard.id
}

output "reports_bucket_name" {
  description = "S3 bucket name storing generated CSV reports"
  value       = aws_s3_bucket.reports.id
}

output "slot_state_table_name" {
  description = "DynamoDB live slot state table name"
  value       = aws_dynamodb_table.slot_state.name
}

output "events_table_name" {
  description = "DynamoDB events history table name"
  value       = aws_dynamodb_table.parking_events.name
}

output "iot_topic_pattern" {
  description = "AWS IoT Core MQTT telemetry topic filter pattern"
  value       = "smart-parking/slot/+/telemetry"
}

output "ingest_lambda_name" {
  description = "Name of the sensor ingestion Lambda function"
  value       = aws_lambda_function.ingest_sensor_data.function_name
}

output "dashboard_api_lambda_name" {
  description = "Name of the dashboard API Lambda function"
  value       = aws_lambda_function.dashboard_api.function_name
}
