# The API: the public front door for FlowForge
resource "aws_apigatewayv2_api" "flowforge" {
  name          = "flowforge-api"
  protocol_type = "HTTP"

  # Lets a browser on another domain (the CloudFront site) call this API
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST", "OPTIONS"]
    allow_headers = ["content-type"]
    max_age       = 3600
  }
}

# Connects the API to the Lambda (proxy: the Lambda gets the whole request)
resource "aws_apigatewayv2_integration" "generate_flow" {
  api_id                 = aws_apigatewayv2_api.flowforge.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.generate_flow.invoke_arn
  payload_format_version = "2.0"
}

# POST /flow goes to the Lambda
resource "aws_apigatewayv2_route" "post_flow" {
  api_id    = aws_apigatewayv2_api.flowforge.id
  route_key = "POST /flow"
  target    = "integrations/${aws_apigatewayv2_integration.generate_flow.id}"
}

# Where the access logs go, kept for 14 days
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/flowforge"
  retention_in_days = 14
}

# The stage: the live version of the API, with throttling and logging
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.flowforge.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_rate_limit  = 5
    throttling_burst_limit = 10
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId        = "$context.requestId"
      ip               = "$context.identity.sourceIp"
      requestTime      = "$context.requestTime"
      method           = "$context.httpMethod"
      route            = "$context.routeKey"
      status           = "$context.status"
      responseLength   = "$context.responseLength"
      integrationError = "$context.integrationErrorMessage"
    })
  }
}

# Lets this API (and only this API) invoke the Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.generate_flow.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.flowforge.execution_arn}/*/*"
}

output "api_url" {
  value = "${aws_apigatewayv2_api.flowforge.api_endpoint}/flow"
}