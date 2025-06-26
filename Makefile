.PHONY: help init plan apply deploy destroy clean test

# デフォルトターゲット
help:
	@echo "Available commands:"
	@echo "  init     - Initialize Terraform"
	@echo "  plan     - Show Terraform execution plan"
	@echo "  apply    - Apply Terraform configuration"
	@echo "  deploy   - Build and deploy (init + apply)"
	@echo "  destroy  - Destroy infrastructure"
	@echo "  clean    - Clean build artifacts"
	@echo "  test     - Run local tests"

init:
	cd terraform && terraform init

plan: init
	cd terraform && terraform plan

apply: package
	cd terraform && terraform apply -auto-approve

deploy: package apply

# Lambda関数のパッケージング
package:
	@echo "Packaging Lambda functions..."
	cd src/main_agent && zip -r ../../terraform/main_agent.zip . -x "*.pyc" "__pycache__/*"
	cd src/sf_api && zip -r ../../terraform/sf_api.zip . -x "*.pyc" "__pycache__/*"
	cd src/web_search && zip -r ../../terraform/web_search.zip . -x "*.pyc" "__pycache__/*"

destroy:
	cd terraform && terraform destroy -auto-approve

# クリーンアップ
clean:
	rm -f terraform/*.zip
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +