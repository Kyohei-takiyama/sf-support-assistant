.PHONY: help init plan apply deploy destroy clean test check-tfvars force-update

# Terraform variables file
TFVARS_FILE := terraform/terraform.tfvars

# デフォルトターゲット
help:
	@echo "Available commands:"
	@echo "  init         - Initialize Terraform"
	@echo "  plan         - Show Terraform execution plan"
	@echo "  apply        - Apply Terraform configuration"
	@echo "  deploy       - Build and deploy (init + apply)"
	@echo "  force-update - Force update Lambda functions"
	@echo "  destroy      - Destroy infrastructure"
	@echo "  clean        - Clean build artifacts"
	@echo "  test         - Run local tests"
	@echo "  check-tfvars - Check if terraform.tfvars exists"

# terraform.tfvarsファイルの存在確認
check-tfvars:
	@if [ ! -f $(TFVARS_FILE) ]; then \
		echo "Error: $(TFVARS_FILE) not found!"; \
		echo "Please create $(TFVARS_FILE) based on terraform.tfvars.example"; \
		echo ""; \
		echo "Example:"; \
		echo "  cp terraform/terraform.tfvars.example $(TFVARS_FILE)"; \
		echo "  # Then edit $(TFVARS_FILE) with your actual values"; \
		exit 1; \
	fi

init: check-tfvars
	cd terraform && terraform init

plan: init
	cd terraform && terraform plan -var-file="terraform.tfvars"

apply: package
	cd terraform && terraform apply -var-file="terraform.tfvars" -auto-approve

deploy: package apply

# Lambda関数のパッケージング
package:
	@echo "Packaging Lambda functions..."
	
	# Main Agent Lambda (依存関係をインストール)
	@echo "Packaging main_agent with dependencies..."
	rm -rf /tmp/main_agent_package
	mkdir -p /tmp/main_agent_package
	cp -r src/main_agent/* /tmp/main_agent_package/
	cd /tmp/main_agent_package && pip install -r requirements.txt -t .
	cd /tmp/main_agent_package && zip -r $(PWD)/terraform/main_agent.zip . -x "*.pyc" "__pycache__/*"
	
	# SF API Lambda (依存関係をインストール)
	@echo "Packaging sf_api with dependencies..."
	rm -rf /tmp/sf_api_package
	mkdir -p /tmp/sf_api_package
	cp -r src/sf_api/* /tmp/sf_api_package/
	cd /tmp/sf_api_package && pip install -r requirements.txt -t .
	cd /tmp/sf_api_package && zip -r $(PWD)/terraform/sf_api.zip . -x "*.pyc" "__pycache__/*"
	
	# Web Search Lambda (依存関係をインストール)
	@echo "Packaging web_search with dependencies..."
	rm -rf /tmp/web_search_package
	mkdir -p /tmp/web_search_package
	cp -r src/web_search/* /tmp/web_search_package/
	cd /tmp/web_search_package && pip install -r requirements.txt -t .
	cd /tmp/web_search_package && zip -r $(PWD)/terraform/web_search.zip . -x "*.pyc" "__pycache__/*"
	
	@echo "Lambda packaging completed!"

destroy: check-tfvars
	cd terraform && terraform destroy -var-file="terraform.tfvars" -auto-approve

# Lambda関数の強制更新（リソース全体を再作成）
force-update: clean package check-tfvars
	@echo "🔄 Lambda関数を強制更新中..."
	cd terraform && terraform apply -target=aws_lambda_function.main_agent -replace=aws_lambda_function.main_agent -var-file="terraform.tfvars" -auto-approve
	cd terraform && terraform apply -target=aws_lambda_function.sf_api -replace=aws_lambda_function.sf_api -var-file="terraform.tfvars" -auto-approve
	cd terraform && terraform apply -target=aws_lambda_function.web_search -replace=aws_lambda_function.web_search -var-file="terraform.tfvars" -auto-approve
	@echo "✅ Lambda関数の強制更新完了"
	@echo "⚠️  注意: API Gateway権限の再設定が必要な場合があります"

# Lambda関数のコードのみを更新（権限は保持）
update-code: package
	@echo "📦 Lambda関数のコードのみを更新します（権限は保持されます）"
	./update_lambda.sh

# Lambda権限を修正
fix-permissions:
	@echo "🔧 API Gateway Lambda実行権限を修正中..."
	@API_ID=$$(cd terraform && terraform output -raw api_gateway_id 2>/dev/null || echo "pni8zharg4"); \
	REGION=$$(cd terraform && terraform output -raw aws_region 2>/dev/null || echo "ap-northeast-1"); \
	ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text); \
	echo "  API Gateway ID: $$API_ID"; \
	echo "  Region: $$REGION"; \
	echo "  Account ID: $$ACCOUNT_ID"; \
	aws lambda remove-permission \
		--function-name sf-support-assistant-main-agent \
		--statement-id AllowAPIGatewayInvoke 2>/dev/null || true; \
	aws lambda add-permission \
		--function-name sf-support-assistant-main-agent \
		--statement-id AllowAPIGatewayInvoke \
		--action lambda:InvokeFunction \
		--principal apigateway.amazonaws.com \
		--source-arn "arn:aws:execute-api:$$REGION:$$ACCOUNT_ID:$$API_ID/*/*"
	@echo "✅ 権限の修正完了"

# クリーンアップ
clean:
	rm -f terraform/*.zip
	rm -rf /tmp/*_package
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +