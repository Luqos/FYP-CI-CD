# AWS IoT Core Topic Rule for telemetry ingestion
resource "aws_iot_topic_rule" "sensor_telemetry" {
  name        = replace("${var.project_name}_telemetry_rule", "-", "_")
  description = "Routes ESP32 ultrasonic telemetry messages to ingest_sensor_data Lambda"
  enabled     = true
  sql         = "SELECT *, topic() AS mqttTopic FROM 'smart-parking/slot/+/telemetry'"
  sql_version = "2016-03-23"

  lambda {
    function_arn = aws_lambda_function.ingest_sensor_data.arn
  }
}

# Lambda Permission for AWS IoT Core Rule invocation
resource "aws_lambda_permission" "iot_core" {
  statement_id  = "AllowIoTCoreInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest_sensor_data.function_name
  principal     = "iot.amazonaws.com"
  source_arn    = aws_iot_topic_rule.sensor_telemetry.arn
}
