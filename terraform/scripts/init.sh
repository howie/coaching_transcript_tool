#!/bin/bash

# Terraform Initialization Script
# Usage: ./init.sh [environment] [--force]

set -e

# Default values
ENVIRONMENT=${1:-production}
FORCE_INIT=${2:-false}

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Validate environment
validate_environment() {
    case $ENVIRONMENT in
        development|staging|production)
            log_info "Initializing Terraform for environment: $ENVIRONMENT"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_error "Valid environments: development, staging, production"
            exit 1
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if terraform is installed
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Please install Terraform first."
        exit 1
    fi
    
    # Check terraform version
    TERRAFORM_VERSION=$(terraform version -json | jq -r '.terraform_version')
    log_info "Terraform version: $TERRAFORM_VERSION"
    
    # Check if gcloud is installed (for GCS backend)
    if ! command -v gcloud &> /dev/null; then
        log_warning "Google Cloud CLI is not installed. You may need it for GCS backend authentication."
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        log_warning "jq is not installed. Some features may not work correctly."
    fi
    
    log_success "Prerequisites check completed"
}

# Initialize GCS backend bucket
initialize_backend_bucket() {
    log_info "Checking GCS backend bucket..."
    
    BUCKET_NAME="coaching-assistant-terraform-state"
    
    # Check if bucket exists
    if gsutil ls -b "gs://$BUCKET_NAME" &> /dev/null; then
        log_info "Backend bucket already exists: $BUCKET_NAME"
    else
        log_info "Creating backend bucket: $BUCKET_NAME"
        
        # Create bucket with versioning enabled
        gsutil mb -p "$(gcloud config get-value project)" -l asia-southeast1 "gs://$BUCKET_NAME"
        gsutil versioning set on "gs://$BUCKET_NAME"
        
        # Set lifecycle rule to delete old versions
        cat > /tmp/lifecycle.json << EOF
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {
        "age": 30,
        "isLive": false
      }
    }
  ]
}
EOF
        gsutil lifecycle set /tmp/lifecycle.json "gs://$BUCKET_NAME"
        rm /tmp/lifecycle.json
        
        log_success "Backend bucket created: $BUCKET_NAME"
    fi
}

# Initialize Terraform
initialize_terraform() {
    local env_dir="environments/$ENVIRONMENT"
    
    if [[ ! -d "$env_dir" ]]; then
        log_error "Environment directory not found: $env_dir"
        exit 1
    fi
    
    cd "$env_dir"
    
    log_info "Initializing Terraform in $env_dir..."
    
    # Initialize with backend configuration
    if [[ "$FORCE_INIT" == "--force" ]]; then
        terraform init -reconfigure
    else
        terraform init
    fi
    
    log_success "Terraform initialized"
    
    # Create or select workspace
    log_info "Managing Terraform workspace..."
    
    if terraform workspace list | grep -q "$ENVIRONMENT"; then
        terraform workspace select "$ENVIRONMENT"
        log_info "Selected existing workspace: $ENVIRONMENT"
    else
        terraform workspace new "$ENVIRONMENT"
        log_success "Created new workspace: $ENVIRONMENT"
    fi
    
    # Validate configuration
    log_info "Validating Terraform configuration..."
    terraform validate
    log_success "Configuration is valid"
    
    cd - > /dev/null
}

# Generate sample terraform.tfvars if it doesn't exist
generate_sample_tfvars() {
    local env_dir="environments/$ENVIRONMENT"
    local tfvars_file="$env_dir/terraform.tfvars"
    local example_file="$env_dir/terraform.tfvars.example"
    
    if [[ ! -f "$tfvars_file" ]] && [[ -f "$example_file" ]]; then
        log_info "Creating terraform.tfvars from example..."
        cp "$example_file" "$tfvars_file"
        log_warning "Please edit $tfvars_file with your actual values before running plan/apply"
    fi
}

# Main execution
main() {
    echo "🚀 Terraform Initialization Script"
    echo "=================================="
    
    validate_environment
    check_prerequisites
    
    # Change to terraform directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")"
    cd "$TERRAFORM_DIR"
    
    initialize_backend_bucket
    initialize_terraform
    generate_sample_tfvars
    
    echo ""
    log_success "Terraform initialization completed for environment: $ENVIRONMENT"
    echo ""
    echo "Next steps:"
    echo "1. Edit environments/$ENVIRONMENT/terraform.tfvars with your actual values"
    echo "2. Run: ./scripts/plan.sh $ENVIRONMENT"
    echo "3. Run: ./scripts/deploy.sh $ENVIRONMENT"
}

# Run main function
main "$@"