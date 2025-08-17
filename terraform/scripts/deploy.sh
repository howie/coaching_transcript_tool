#!/bin/bash

# Terraform Deploy Script
# Usage: ./deploy.sh [environment] [--auto-approve]

set -e

# Default values
ENVIRONMENT=${1:-production}
AUTO_APPROVE=${2:-false}

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
            log_info "Deploying to environment: $ENVIRONMENT"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_error "Valid environments: development, staging, production"
            exit 1
            ;;
    esac
}

# Pre-deployment checks
pre_deployment_checks() {
    local env_dir="environments/$ENVIRONMENT"
    
    log_info "Running pre-deployment checks..."
    
    # Check if terraform is initialized
    if [[ ! -d "$env_dir/.terraform" ]]; then
        log_error "Terraform not initialized. Please run init.sh first."
        exit 1
    fi
    
    # Check if plan exists
    local plan_file=$(cat "$env_dir/.latest-plan" 2>/dev/null || echo "")
    if [[ -z "$plan_file" ]] || [[ ! -f "$env_dir/$plan_file" ]]; then
        log_warning "No recent plan found. Generating a new plan..."
        bash "$(dirname "$0")/plan.sh" "$ENVIRONMENT"
        plan_file=$(cat "$env_dir/.latest-plan" 2>/dev/null || echo "")
    fi
    
    # Verify plan is not too old (more than 1 hour)
    if [[ -n "$plan_file" ]]; then
        local plan_age=$(($(date +%s) - $(stat -f %m "$env_dir/$plan_file" 2>/dev/null || echo 0)))
        if [[ $plan_age -gt 3600 ]]; then
            log_warning "Plan is older than 1 hour. Consider regenerating with plan.sh"
        fi
    fi
    
    log_success "Pre-deployment checks completed"
}

# Safety checks for production
production_safety_checks() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_info "Running production safety checks..."
        
        # Check if it's during business hours (warn only)
        local current_hour=$(date +%H)
        if [[ $current_hour -ge 9 ]] && [[ $current_hour -le 17 ]]; then
            log_warning "Deploying during business hours (9 AM - 5 PM). Consider deploying outside business hours."
        fi
        
        # Check for destructive changes
        local env_dir="environments/$ENVIRONMENT"
        local plan_file=$(cat "$env_dir/.latest-plan" 2>/dev/null || echo "")
        
        if [[ -n "$plan_file" ]]; then
            cd "$env_dir"
            local delete_count=$(terraform show -json "$plan_file" | jq '[.resource_changes[]? | select(.change.actions[] | contains("delete"))] | length' 2>/dev/null || echo 0)
            
            if [[ $delete_count -gt 0 ]]; then
                log_warning "This deployment will DELETE $delete_count resources in PRODUCTION!"
                if [[ "$AUTO_APPROVE" != "--auto-approve" ]]; then
                    echo "Are you absolutely sure you want to continue? (type 'DELETE' to confirm)"
                    read -r confirmation
                    if [[ "$confirmation" != "DELETE" ]]; then
                        log_error "Deployment cancelled"
                        exit 1
                    fi
                fi
            fi
            cd - > /dev/null
        fi
        
        log_success "Production safety checks completed"
    fi
}

# Backup current state (for production)
backup_state() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        local env_dir="environments/$ENVIRONMENT"
        local backup_dir="backups/$(date +%Y%m%d-%H%M%S)"
        
        log_info "Creating state backup..."
        
        mkdir -p "$backup_dir"
        
        cd "$env_dir"
        
        # Backup terraform state
        if terraform state pull > "../$backup_dir/terraform.tfstate.backup"; then
            log_success "State backup created: $backup_dir/terraform.tfstate.backup"
        else
            log_warning "Failed to create state backup"
        fi
        
        cd - > /dev/null
    fi
}

# Deploy infrastructure
deploy_infrastructure() {
    local env_dir="environments/$ENVIRONMENT"
    local plan_file=$(cat "$env_dir/.latest-plan" 2>/dev/null || echo "")
    
    cd "$env_dir"
    
    # Select the correct workspace
    terraform workspace select "$ENVIRONMENT" || {
        log_error "Workspace $ENVIRONMENT not found. Please run init.sh first."
        exit 1
    }
    
    log_info "Applying Terraform plan..."
    
    # Apply the plan
    if [[ -n "$plan_file" && -f "$plan_file" ]]; then
        # Use existing plan
        if [[ "$AUTO_APPROVE" == "--auto-approve" ]]; then
            terraform apply "$plan_file"
        else
            echo ""
            log_warning "You are about to apply the following plan:"
            terraform show "$plan_file" | head -50
            echo ""
            echo "Do you want to apply this plan? (y/N)"
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                terraform apply "$plan_file"
            else
                log_error "Deployment cancelled"
                exit 1
            fi
        fi
    else
        # Generate and apply plan in one step
        if [[ "$AUTO_APPROVE" == "--auto-approve" ]]; then
            terraform apply -var-file="terraform.tfvars" -auto-approve
        else
            terraform apply -var-file="terraform.tfvars"
        fi
    fi
    
    local apply_exit_code=$?
    
    cd - > /dev/null
    
    return $apply_exit_code
}

# Post-deployment verification
post_deployment_verification() {
    local env_dir="environments/$ENVIRONMENT"
    
    log_info "Running post-deployment verification..."
    
    cd "$env_dir"
    
    # Get outputs
    terraform output > deployment-outputs.txt 2>/dev/null || true
    
    # Basic connectivity tests
    local frontend_url=$(terraform output -raw frontend_url 2>/dev/null || echo "")
    local api_url=$(terraform output -raw api_url 2>/dev/null || echo "")
    
    if [[ -n "$frontend_url" ]]; then
        log_info "Testing frontend connectivity: $frontend_url"
        if curl -s -o /dev/null -w "%{http_code}" "$frontend_url" | grep -q "200\|301\|302"; then
            log_success "Frontend is accessible"
        else
            log_warning "Frontend connectivity test failed"
        fi
    fi
    
    if [[ -n "$api_url" ]]; then
        log_info "Testing API connectivity: $api_url/api/health"
        if curl -s -o /dev/null -w "%{http_code}" "$api_url/api/health" | grep -q "200"; then
            log_success "API is accessible"
        else
            log_warning "API connectivity test failed (this is normal if services are still starting)"
        fi
    fi
    
    cd - > /dev/null
    
    log_success "Post-deployment verification completed"
}

# Generate deployment report
generate_deployment_report() {
    local env_dir="environments/$ENVIRONMENT"
    local report_file="deployment-report-$(date +%Y%m%d-%H%M%S).md"
    
    cd "$env_dir"
    
    log_info "Generating deployment report..."
    
    cat > "$report_file" << EOF
# Deployment Report

**Environment:** $ENVIRONMENT  
**Date:** $(date)  
**User:** $(whoami)  
**Host:** $(hostname)

## Terraform State

\`\`\`
$(terraform workspace show)
\`\`\`

## Applied Resources

\`\`\`
$(terraform state list | wc -l) resources managed
\`\`\`

## Outputs

\`\`\`
$(terraform output 2>/dev/null || echo "No outputs available")
\`\`\`

## Service URLs

$(terraform output -raw frontend_url 2>/dev/null && echo "" || echo "Frontend URL: Not available")
$(terraform output -raw api_url 2>/dev/null && echo "" || echo "API URL: Not available")

## Next Steps

1. Verify all services are running correctly
2. Run smoke tests
3. Monitor logs for any issues
4. Update monitoring dashboards

---
Generated by deploy.sh script
EOF
    
    log_success "Deployment report generated: $env_dir/$report_file"
    
    cd - > /dev/null
}

# Main execution
main() {
    echo "🚀 Terraform Deployment Script"
    echo "==============================="
    
    validate_environment
    
    # Change to terraform directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")"
    cd "$TERRAFORM_DIR"
    
    pre_deployment_checks
    production_safety_checks
    backup_state
    
    # Deploy
    if deploy_infrastructure; then
        post_deployment_verification
        generate_deployment_report
        
        echo ""
        log_success "🎉 Deployment completed successfully for environment: $ENVIRONMENT"
        echo ""
        echo "Deployment summary:"
        cd "environments/$ENVIRONMENT"
        if terraform output frontend_url &>/dev/null; then
            echo "  🌐 Frontend: $(terraform output -raw frontend_url)"
        fi
        if terraform output api_url &>/dev/null; then
            echo "  🔗 API: $(terraform output -raw api_url)"
        fi
        echo ""
        echo "Next steps:"
        echo "1. Monitor the services to ensure they start correctly"
        echo "2. Run integration tests"
        echo "3. Check application logs"
        if [[ "$ENVIRONMENT" == "production" ]]; then
            echo "4. Notify stakeholders of the deployment"
        fi
    else
        log_error "Deployment failed. Please check the error messages above."
        exit 1
    fi
}

# Run main function
main "$@"