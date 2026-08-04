# Amazon API Gateway HTTP API
resource "aws_apigatewayv2_api" "dashboard_api" {
  name          = "${var.project_name}-http-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.dashboard_api.id
  name        = "dev"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "dashboard_api" {
  api_id                 = aws_apigatewayv2_api.dashboard_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.dashboard_api.invoke_arn
  payload_format_version = "2.0"
}

# Proxy Route: ANY /{proxy+}
resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.dashboard_api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.dashboard_api.id}"
}

# Root Route: ANY /
resource "aws_apigatewayv2_route" "root" {
  api_id    = aws_apigatewayv2_api.dashboard_api.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.dashboard_api.id}"
}

# Lambda Permission for API Gateway invocation
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dashboard_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.dashboard_api.execution_arn}/*/*"
}
