output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = "${aws_api_gateway_deployment.sf_support_deployment.invoke_url}/agent"
}

output "main_agent_function_name" {
  description = "Main Agent Lambda function name"
  value       = aws_lambda_function.main_agent.function_name
}

output "sf_api_function_name" {
  description = "SF API Lambda function name"
  value       = aws_lambda_function.sf_api.function_name
}

output "web_search_function_name" {
  description = "Web Search Lambda function name"
  value       = aws_lambda_function.web_search.function_name
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = aws_api_gateway_rest_api.sf_support_api.id
}
