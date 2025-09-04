#!/bin/bash

# Terraform Plan Script
# Usage: ./plan.sh [environment] [--detailed]

set -e

# Default values
ENVIRONMENT=${1:-production}
DETAILED=${2:-false}

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
            log_info "Planning Terraform deployment for environment: $ENVIRONMENT"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_error "Valid environments: development, staging, production"
            exit 1
            ;;
    esac
}

# Check if terraform.tfvars exists
check_tfvars() {
    local env_dir="environments/$ENVIRONMENT"
    local tfvars_file="$env_dir/terraform.tfvars"
    
    if [[ ! -f "$tfvars_file" ]]; then
        log_error "terraform.tfvars not found in $env_dir"
        log_error "Please create it from terraform.tfvars.example and add your values"
        exit 1
    fi
    
    log_success "Found terraform.tfvars"
}

# Validate required variables
validate_variables() {
    local env_dir="environments/$ENVIRONMENT"
    local tfvars_file="$env_dir/terraform.tfvars"
    
    log_info "Validating required variables..."
    
    # Check for placeholder values that need to be replaced
    local placeholders=(
        "your-cloudflare-api-token"
        "your-render-api-key"
        "your-zone-id"
        "your-account-id"
        "your-github-username"
        "your-super-secret-key"
        "your-google-client-id"
        "your-recaptcha-site-key"
    )
    
    local has_placeholders=false
    for placeholder in "${placeholders[@]}"; do
        if grep -q "$placeholder" "$tfvars_file"; then
            log_warning "Found placeholder value: $placeholder"
            has_placeholders=true
        fi
    done
    
    if [[ "$has_placeholders" == "true" ]]; then
        log_error "Please replace all placeholder values in $tfvars_file"
        exit 1
    fi
    
    log_success "Variable validation completed"
}

# Run security checks
run_security_checks() {
    local env_dir="environments/$ENVIRONMENT"
    
    log_info "Running security checks..."
    
    # Check for hardcoded secrets (basic check)
    cd "$env_dir"
    
    # Look for common secret patterns
    if grep -r "password\|secret\|key" *.tf | grep -v "var\." | grep -v "sensitive" | grep -v "description"; then
        log_warning "Potential hardcoded secrets found. Please review the above lines."
    fi
    
    # Check if sensitive variables are marked as sensitive
    if ! grep -q "sensitive.*=.*true" variables.tf; then
        log_warning "Some variables might not be marked as sensitive"
    fi
    
    cd - > /dev/null
    
    log_success "Security checks completed"
}

# Generate plan
generate_plan() {
    local env_dir="environments/$ENVIRONMENT"
    local plan_file="$env_dir/tfplan-$(date +%Y%m%d-%H%M%S)"
    
    cd "$env_dir"
    
    # Select the correct workspace
    terraform workspace select "$ENVIRONMENT" || {
        log_error "Workspace $ENVIRONMENT not found. Please run init.sh first."
        exit 1
    }
    
    log_info "Generating Terraform plan..."
    
    # Plan with variable file
    if [[ "$DETAILED" == "--detailed" ]]; then
        terraform plan -var-file="terraform.tfvars" -out="$plan_file" -detailed-exitcode
    else
        terraform plan -var-file="terraform.tfvars" -out="$plan_file"
    fi
    
    local plan_exit_code=$?
    
    # Save the plan file name for later use
    echo "$plan_file" > .latest-plan
    
    log_success "Plan generated: $plan_file"
    
    cd - > /dev/null
    
    return $plan_exit_code
}

# Analyze plan output
analyze_plan() {
    local env_dir="environments/$ENVIRONMENT"
    local plan_file=$(cat "$env_dir/.latest-plan" 2>/dev/null || echo "")
    
    if [[ -z "$plan_file" ]] || [[ ! -f "$env_dir/$plan_file" ]]; then
        log_warning "No plan file found for analysis"
        return
    fi
    
    cd "$env_dir"
    
    log_info "Analyzing plan changes..."
    
    # Show plan in a readable format
    terraform show "$plan_file" > plan-output.txt
    
    # Count changes
    local add_count=$(terraform show -json "$plan_file" | jq '[.resource_changes[]? | select(.change.actions[] | contains("create"))] | length')
    local change_count=$(terraform show -json "$plan_file" | jq '[.resource_changes[]? | select(.change.actions[] | contains("update"))] | length')
    local delete_count=$(terraform show -json "$plan_file" | jq '[.resource_changes[]? | select(.change.actions[] | contains("delete"))] | length')
    
    echo ""
    log_info "Plan Summary:"
    echo "  📦 Resources to create: $add_count"
    echo "  🔄 Resources to update: $change_count"
    echo "  🗑️  Resources to delete: $delete_count"
    echo ""
    
    # Check for potentially destructive changes
    if [[ "$delete_count" -gt 0 ]]; then
        log_warning "This plan includes resource deletions. Please review carefully!"
    fi
    
    # Check for database changes
    if terraform show "$plan_file" | grep -q "render_postgres\|google_sql"; then
        log_warning "This plan includes database changes. Please ensure you have backups!"
    fi
    
    cd - > /dev/null
}

# Main execution
main() {
    echo "📋 Terraform Plan Script"
    echo "========================"
    
    validate_environment
    
    # Change to terraform directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")"
    cd "$TERRAFORM_DIR"
    
    check_tfvars
    validate_variables
    run_security_checks
    
    # Generate plan
    if generate_plan; then
        analyze_plan
        
        echo ""
        log_success "Terraform plan completed for environment: $ENVIRONMENT"
        echo ""
        echo "Next steps:"
        echo "1. Review the plan output above"
        echo "2. If everything looks good, run: ./scripts/deploy.sh $ENVIRONMENT"
        echo "3. Or run: ./scripts/deploy.sh $ENVIRONMENT --auto-approve (skip confirmation)"
    else
        local exit_code=$?
        if [[ $exit_code -eq 2 ]]; then
            log_info "Plan completed with changes detected"
            analyze_plan
        else
            log_error "Plan failed with exit code: $exit_code"
            exit $exit_code
        fi
    fi
}

# Run main function
main "$@"