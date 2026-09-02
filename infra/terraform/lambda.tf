# Lambda 1: ingest_sensor_data
resource "aws_lambda_function" "ingest_sensor_data" {
  function_name = "${var.project_name}-ingest-sensor-data"
  role          = var.lab_role_arn
  handler       = "app.lambda_handler"
  runtime       = "python3.11"
  timeout       = 15
  memory_size   = 512

  filename         = "${path.module}/../../build/ingest_sensor_data.zip"
  source_code_hash = fileexists("${path.module}/../../build/ingest_sensor_data.zip") ? filebase64sha256("${path.module}/../../build/ingest_sensor_data.zip") : null

  environment {
    variables = {
      SLOT_STATE_TABLE = aws_dynamodb_table.slot_state.name
      EVENTS_TABLE     = aws_dynamodb_table.parking_events.name
      PROJECT_NAME     = var.project_name
    }
  }
}

resource "aws_cloudwatch_log_group" "ingest_sensor_data" {
  name              = "/aws/lambda/${aws_lambda_function.ingest_sensor_data.function_name}"
  retention_in_days = 7
}

# Lambda 2: dashboard_api
resource "aws_lambda_function" "dashboard_api" {
  function_name = "${var.project_name}-dashboard-api"
  role          = var.lab_role_arn
  handler       = "app.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 512

  filename         = "${path.module}/../../build/dashboard_api.zip"
  source_code_hash = fileexists("${path.module}/../../build/dashboard_api.zip") ? filebase64sha256("${path.module}/../../build/dashboard_api.zip") : null

  environment {
    variables = {
      SLOT_STATE_TABLE = aws_dynamodb_table.slot_state.name
      EVENTS_TABLE     = aws_dynamodb_table.parking_events.name
      REPORTS_BUCKET   = aws_s3_bucket.reports.id
      PROJECT_NAME     = var.project_name
    }
  }
}

resource "aws_cloudwatch_log_group" "dashboard_api" {
  name              = "/aws/lambda/${aws_lambda_function.dashboard_api.function_name}"
  retention_in_days = 7
}
