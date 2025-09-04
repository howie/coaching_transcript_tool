# Makefile for GCP Terraform operations

.PHONY: init plan apply destroy validate format check clean install help config-check

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Installation and setup
install: ## Install required tools (Terraform, gcloud)
	@echo "Checking for required tools..."
	@which terraform || (echo "Please install Terraform: https://www.terraform.io/downloads.html" && exit 1)
	@which gcloud || (echo "Please install gcloud: https://cloud.google.com/sdk/docs/install" && exit 1)
	@echo "All tools are installed ✓"

setup: install ## Setup project and authenticate
	@echo "Setting up GCP project..."
	@gcloud auth application-default login
	@gcloud config set project coachingassistant
	@echo "Setup complete ✓"

# Terraform operations
init: ## Initialize Terraform
	terraform init

validate: ## Validate Terraform configuration
	terraform validate

format: ## Format Terraform files
	terraform fmt -recursive

check: validate format ## Run validation and format checks

plan: ## Show Terraform execution plan
	terraform plan

plan-out: ## Save Terraform execution plan to file
	terraform plan -out=tfplan

apply: ## Apply Terraform configuration
	terraform apply

apply-auto: ## Apply Terraform configuration without confirmation
	terraform apply -auto-approve

apply-plan: ## Apply saved Terraform plan
	terraform apply tfplan

destroy: ## Destroy all Terraform resources (BE CAREFUL!)
	terraform destroy

destroy-auto: ## Destroy all Terraform resources without confirmation (DANGEROUS!)
	terraform destroy -auto-approve

# Output operations
output: ## Show all Terraform outputs
	terraform output

output-json: ## Show all Terraform outputs in JSON format
	terraform output -json

output-env: ## Show environment variables template
	terraform output env_vars_template

output-credentials: ## Show service account credentials (sensitive)
	@echo "Service Account Email:"
	@terraform output -raw service_account_email
	@echo "\nService Account Credentials (JSON):"
	@terraform output -raw service_account_credentials_json

# State operations
state: ## Show Terraform state list
	terraform state list

state-show: ## Show detailed state for a resource (usage: make state-show RESOURCE=resource_name)
	terraform state show $(RESOURCE)

refresh: ## Refresh Terraform state
	terraform refresh

# Import operations
import-existing: ## Import all existing GCP resources automatically
	./import-existing.sh

import-service-account: ## Import existing service account manually
	terraform import google_service_account.coaching_storage projects/coachingassistant/serviceAccounts/coaching-storage@coachingassistant.iam.gserviceaccount.com

import-audio-bucket: ## Import existing audio storage bucket manually
	terraform import google_storage_bucket.audio_storage coaching-audio-prod

import-transcript-bucket: ## Import existing transcript storage bucket manually
	terraform import google_storage_bucket.transcript_storage coaching-transcript-prod

# Environment setup
env-file: ## Create environment file from Terraform outputs
	@echo "Creating environment file from Terraform outputs..."
	@echo "# Environment variables from Terraform outputs" > .env.terraform
	@echo "# Generated on $$(date)" >> .env.terraform
	@echo "GOOGLE_APPLICATION_CREDENTIALS_JSON='$$(terraform output -raw service_account_credentials_json)'" >> .env.terraform
	@echo "GCP_PROJECT_ID='$$(terraform output -raw project_id)'" >> .env.terraform
	@echo "GCP_REGION='asia-east1'" >> .env.terraform
	@echo "AUDIO_STORAGE_BUCKET='$$(terraform output -raw audio_storage_bucket)'" >> .env.terraform
	@echo "TRANSCRIPT_STORAGE_BUCKET='$$(terraform output -raw transcript_storage_bucket)'" >> .env.terraform
	@echo "SPEECH_API_VERSION='v2'" >> .env.terraform
	@echo "Environment file created: .env.terraform"

# Verification operations
verify: ## Verify the deployment by testing key resources
	@echo "Verifying Terraform deployment..."
	@echo "1. Checking project..."
	@gcloud config get-value project
	@echo "2. Checking service account..."
	@gcloud iam service-accounts describe coaching-storage@coachingassistant.iam.gserviceaccount.com
	@echo "3. Checking enabled APIs..."
	@gcloud services list --enabled --filter="name:speech OR name:storage"
	@echo "4. Checking storage buckets..."
	@gsutil ls -p coachingassistant | grep -E "(audio-storage|transcript-storage)" || echo "Buckets not found"
	@echo "5. Checking IAM permissions..."
	@gcloud projects get-iam-policy coachingassistant --format="table(bindings.role,bindings.members)" --filter="bindings.members:coaching-storage@coachingassistant.iam.gserviceaccount.com"
	@echo "Verification complete ✓"

test-speech: ## Test Speech-to-Text API access
	@echo "Testing Speech-to-Text API access..."
	@gcloud auth activate-service-account --key-file=<(terraform output -raw service_account_credentials_json)
	@gcloud ml speech recognize --language-code=en-US --encoding=LINEAR16 --sample-rate=16000 --audio-uri=gs://cloud-samples-tests/speech/brooklyn.wav
	@echo "Speech-to-Text test complete ✓"

# Cleanup operations
clean: ## Clean up temporary files
	rm -f tfplan
	rm -f .env.terraform
	rm -f terraform.tfstate.backup.*

clean-all: clean ## Clean up all temporary and cache files
	rm -rf .terraform
	rm -f .terraform.lock.hcl

# Emergency operations
emergency-permissions: ## Apply critical permissions manually (emergency use)
	@echo "Applying emergency permissions manually..."
	@echo "Adding Speech-to-Text permissions..."
	@gcloud projects add-iam-policy-binding coachingassistant \
		--member="serviceAccount:coaching-storage@coachingassistant.iam.gserviceaccount.com" \
		--role="roles/speech.user"
	@echo "Adding Storage permissions..."
	@gcloud projects add-iam-policy-binding coachingassistant \
		--member="serviceAccount:coaching-storage@coachingassistant.iam.gserviceaccount.com" \
		--role="roles/storage.objectAdmin"
	@echo "Adding Legacy Bucket Writer permissions..."
	@gcloud projects add-iam-policy-binding coachingassistant \
		--member="serviceAccount:coaching-storage@coachingassistant.iam.gserviceaccount.com" \
		--role="roles/storage.legacyBucketWriter"
	@echo "Emergency permissions applied ✓"

# Development helpers
diff: ## Show difference between current and planned state
	terraform plan -detailed-exitcode

graph: ## Generate dependency graph
	terraform graph | dot -Tsvg > terraform-graph.svg
	@echo "Graph saved to terraform-graph.svg"

# Variables and configuration
vars: ## Show current variable values
	@echo "Current Terraform variables:"
	@echo "GCP Project ID: coachingassistant"
	@echo "GCP Region: asia-east1"
	@echo "Environment: prod"
	@if [ -f terraform.tfvars ]; then \
		echo "Custom variables file exists: terraform.tfvars"; \
	else \
		echo "No custom variables file (terraform.tfvars)"; \
		echo "Copy terraform.tfvars.example to terraform.tfvars to customize"; \
	fi

# Configuration checking operations
config-check: ## Run comprehensive configuration check
	@echo "Running comprehensive configuration check..."
	@cd ../.. && ./terraform/scripts/check-config.sh comprehensive

config-check-security: ## Run security audit on configuration
	@echo "Running security audit..."
	@cd ../.. && ./terraform/scripts/check-config.sh security-audit

config-check-terraform: ## Validate Terraform configuration consistency
	@echo "Checking Terraform consistency..."
	@cd ../.. && ./terraform/scripts/check-config.sh terraform-check production

config-discover: ## Discover all configuration files
	@echo "Discovering configuration files..."
	@../scripts/check-config.sh discover

config-report: ## Generate detailed configuration report
	@echo "Generating configuration report..."
	@cd ../.. && terraform/scripts/check-config.sh report