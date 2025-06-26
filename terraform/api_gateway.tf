# API Gateway REST API
resource "aws_api_gateway_rest_api" "sf_support_api" {
  name        = "${var.project_name}-api"
  description = "SF Support Assistant API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# CORS用リソース
resource "aws_api_gateway_resource" "agent" {
  rest_api_id = aws_api_gateway_rest_api.sf_support_api.id
  parent_id   = aws_api_gateway_rest_api.sf_support_api.root_resource_id
  path_part   = "agent"
}

# POST メソッド
resource "aws_api_gateway_method" "agent_post" {
  rest_api_id   = aws_api_gateway_rest_api.sf_support_api.id
  resource_id   = aws_api_gateway_resource.agent.id
  http_method   = "POST"
  authorization = "NONE"
}

# OPTIONS メソッド（CORS用）
resource "aws_api_gateway_method" "agent_options" {
  rest_api_id   = aws_api_gateway_rest_api.sf_support_api.id
  resource_id   = aws_api_gateway_resource.agent.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# Lambda統合（POST）
resource "aws_api_gateway_integration" "agent_integration" {
  rest_api_id = aws_api_gateway_rest_api.sf_support_api.id
  resource_id = aws_api_gateway_resource.agent.id
  http_method = aws_api_gateway_method.agent_post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.main_agent.invoke_arn
}

# CORS統合（OPTIONS）
resource "aws_api_gateway_integration" "agent_options_integration" {
  rest_api_id = aws_api_gateway_rest_api.sf_support_api.id
  resource_id = aws_api_gateway_resource.agent.id
  http_method = aws_api_gateway_method.agent_options.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

# OPTIONS レスポンス
resource "aws_api_gateway_method_response" "agent_options_200" {
  rest_api_id = aws_api_gateway_rest_api.sf_support_api.id
  resource_id = aws_api_gateway_resource.agent.id
  http_method = aws_api_gateway_method.agent_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "agent_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.sf_support_api.id
  resource_id = aws_api_gateway_resource.agent.id
  http_method = aws_api_gateway_method.agent_options.http_method
  status_code = aws_api_gateway_method_response.agent_options_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST,PUT'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# Lambda権限
resource "aws_lambda_permission" "apigw_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main_agent.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.sf_support_api.execution_arn}/*/*"
}

# デプロイメント
resource "aws_api_gateway_deployment" "sf_support_deployment" {
  depends_on = [
    aws_api_gateway_integration.agent_integration,
    aws_api_gateway_integration.agent_options_integration,
  ]

  rest_api_id = aws_api_gateway_rest_api.sf_support_api.id
  stage_name  = var.environment
}
