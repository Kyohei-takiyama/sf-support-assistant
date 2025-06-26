variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "sf-support-assistant"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Salesforce設定
variable "salesforce_instance_url" {
  description = "Salesforce instance URL"
  type        = string
  sensitive   = true
}

variable "salesforce_client_id" {
  description = "Salesforce Connected App Client ID"
  type        = string
  sensitive   = true
}

variable "salesforce_client_secret" {
  description = "Salesforce Connected App Client Secret"
  type        = string
  sensitive   = true
}

# API Keys
variable "tavily_api_key" {
  description = "Tavily API key"
  type        = string
  sensitive   = true
}
