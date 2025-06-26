# Main Agent Lambda (Strands Agents)
resource "aws_lambda_function" "main_agent" {
  filename         = "main_agent.zip"
  function_name    = "${var.project_name}-main-agent"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  timeout          = 60
  memory_size      = 512
  source_code_hash = filebase64sha256("main_agent.zip")

  environment {
    variables = {
      SF_API_FUNCTION_NAME     = aws_lambda_function.sf_api.function_name
      WEB_SEARCH_FUNCTION_NAME = aws_lambda_function.web_search.function_name
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_basic_execution]
}

# Salesforce API Lambda
resource "aws_lambda_function" "sf_api" {
  filename         = "sf_api.zip"
  function_name    = "${var.project_name}-sf-api"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256
  source_code_hash = filebase64sha256("sf_api.zip")

  environment {
    variables = {
      SALESFORCE_INSTANCE_URL  = var.salesforce_instance_url
      SALESFORCE_CLIENT_ID     = var.salesforce_client_id
      SALESFORCE_CLIENT_SECRET = var.salesforce_client_secret
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_basic_execution]
}

# Web Search Lambda (Tavily)
resource "aws_lambda_function" "web_search" {
  filename         = "web_search.zip"
  function_name    = "${var.project_name}-web-search"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256
  source_code_hash = filebase64sha256("web_search.zip")

  environment {
    variables = {
      TAVILY_API_KEY = var.tavily_api_key
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_basic_execution]
}
