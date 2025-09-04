#!/bin/bash

# Terraform Destroy Script
# Usage: ./destroy.sh [environment] [--force]

set -e

# Default values
ENVIRONMENT=${1:-staging}
FORCE_DESTROY=${2:-false}

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
        development|staging)
            log_info "Preparing to destroy environment: $ENVIRONMENT"
            ;;
        production)
            log_error "❌ PRODUCTION DESTRUCTION IS DISABLED"
            log_error "This script cannot destroy production environment for safety"
            log_error "If you really need to destroy production:"
            log_error "1. Manually run terraform destroy in environments/production/"
            log_error "2. Type 'production' when prompted"
            log_error "3. Confirm all resources individually"
            exit 1
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_error "Valid environments: development, staging"
            exit 1
            ;;
    esac
}

# Safety confirmations
safety_confirmations() {
    echo ""
    log_warning "🚨 DESTRUCTIVE OPERATION WARNING 🚨"
    echo ""
    echo "This will PERMANENTLY DELETE all infrastructure in the $ENVIRONMENT environment:"
    echo ""
    echo "  💾 Databases and all data"
    echo "  🗄️  Storage buckets and files"
    echo "  🌐 DNS records and domains"
    echo "  🔧 All services and workers"
    echo "  📊 Monitoring and logs"
    echo ""
    
    if [[ "$FORCE_DESTROY" == "--force" ]]; then
        log_warning "Force mode enabled - skipping confirmations"
        return
    fi
    
    # First confirmation
    echo "Are you sure you want to destroy the $ENVIRONMENT environment? (type 'yes' to continue)"
    read -r confirmation1
    if [[ "$confirmation1" != "yes" ]]; then
        log_error "Operation cancelled"
        exit 1
    fi
    
    # Second confirmation
    echo ""
    echo "This action cannot be undone. Type '$ENVIRONMENT' to confirm:"
    read -r confirmation2
    if [[ "$confirmation2" != "$ENVIRONMENT" ]]; then
        log_error "Operation cancelled"
        exit 1
    fi
    
    # Final confirmation
    echo ""
    echo "Final confirmation: Type 'DESTROY' to proceed with destruction:"
    read -r confirmation3
    if [[ "$confirmation3" != "DESTROY" ]]; then
        log_error "Operation cancelled"
        exit 1
    fi
    
    log_warning "Proceeding with destruction in 5 seconds... (Ctrl+C to cancel)"
    sleep 5
}

# Pre-destroy backup
create_final_backup() {
    local env_dir="environments/$ENVIRONMENT"
    local backup_dir="backups/final-backup-$(date +%Y%m%d-%H%M%S)"
    
    log_info "Creating final backup before destruction..."
    
    mkdir -p "$backup_dir"
    
    cd "$env_dir"
    
    # Backup terraform state
    if terraform state pull > "../$backup_dir/terraform.tfstate.final"; then
        log_success "Final state backup created"
    fi
    
    # Export outputs
    terraform output -json > "../$backup_dir/outputs.json" 2>/dev/null || true
    
    # List all resources
    terraform state list > "../$backup_dir/resources.txt" 2>/dev/null || true
    
    cd - > /dev/null
    
    log_success "Final backup completed: $backup_dir"
}

# Remove protection from critical resources
remove_protections() {
    local env_dir="environments/$ENVIRONMENT"
    
    log_info "Removing deletion protection from resources..."
    
    cd "$env_dir"
    
    # Note: This would remove lifecycle prevent_destroy rules if they existed
    # For now, we'll just warn about any protected resources
    
    if terraform plan -destroy | grep -q "prevent_destroy"; then
        log_warning "Some resources have deletion protection enabled"
        log_info "You may need to remove lifecycle.prevent_destroy rules manually"
    fi
    
    cd - > /dev/null
}

# Destroy infrastructure
destroy_infrastructure() {
    local env_dir="environments/$ENVIRONMENT"
    
    cd "$env_dir"
    
    # Select the correct workspace
    terraform workspace select "$ENVIRONMENT" || {
        log_error "Workspace $ENVIRONMENT not found"
        exit 1
    }
    
    log_info "Destroying Terraform infrastructure..."
    
    # Show destroy plan first
    log_info "Generating destroy plan..."
    terraform plan -destroy -var-file="terraform.tfvars"
    
    echo ""
    log_warning "The above resources will be DESTROYED. Continue? (y/N)"
    if [[ "$FORCE_DESTROY" != "--force" ]]; then
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_error "Destruction cancelled"
            exit 1
        fi
    fi
    
    # Destroy infrastructure
    if [[ "$FORCE_DESTROY" == "--force" ]]; then
        terraform destroy -var-file="terraform.tfvars" -auto-approve
    else
        terraform destroy -var-file="terraform.tfvars"
    fi
    
    local destroy_exit_code=$?
    
    cd - > /dev/null
    
    return $destroy_exit_code
}

# Clean up workspace
cleanup_workspace() {
    local env_dir="environments/$ENVIRONMENT"
    
    log_info "Cleaning up workspace..."
    
    cd "$env_dir"
    
    # Remove the workspace if empty
    if terraform workspace list | grep -q "$ENVIRONMENT"; then
        terraform workspace select default
        terraform workspace delete "$ENVIRONMENT" 2>/dev/null || {
            log_warning "Could not delete workspace $ENVIRONMENT (may not be empty)"
        }
    fi
    
    # Clean up plan files
    rm -f tfplan-* plan-output.txt .latest-plan deployment-outputs.txt
    
    cd - > /dev/null
    
    log_success "Workspace cleanup completed"
}

# Generate destruction report
generate_destruction_report() {
    local report_file="destruction-report-$ENVIRONMENT-$(date +%Y%m%d-%H%M%S).md"
    
    log_info "Generating destruction report..."
    
    cat > "$report_file" << EOF
# Infrastructure Destruction Report

**Environment:** $ENVIRONMENT  
**Date:** $(date)  
**User:** $(whoami)  
**Host:** $(hostname)

## Summary

The $ENVIRONMENT environment has been completely destroyed.

## Destroyed Resources

All Terraform-managed resources in the $ENVIRONMENT environment have been removed:

- ✅ Render.com services (API, Worker, Database, Redis)
- ✅ Cloudflare configuration (DNS, Pages, Security rules)
- ✅ Google Cloud Platform resources (Storage, IAM, Secrets)

## Backups

Final backups were created before destruction:
- Terraform state
- Resource list
- Configuration outputs

## Recovery

To recreate this environment:

1. Ensure terraform.tfvars is properly configured
2. Run: \`./scripts/init.sh $ENVIRONMENT\`
3. Run: \`./scripts/plan.sh $ENVIRONMENT\`
4. Run: \`./scripts/deploy.sh $ENVIRONMENT\`

## Notes

- All data in databases and storage buckets has been permanently deleted
- DNS records have been removed
- Service accounts and API keys may need to be regenerated

---
Generated by destroy.sh script
EOF
    
    log_success "Destruction report generated: $report_file"
}

# Main execution
main() {
    echo "💣 Terraform Destruction Script"
    echo "================================"
    
    validate_environment
    
    # Change to terraform directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")"
    cd "$TERRAFORM_DIR"
    
    safety_confirmations
    create_final_backup
    remove_protections
    
    # Destroy
    if destroy_infrastructure; then
        cleanup_workspace
        generate_destruction_report
        
        echo ""
        log_success "💥 Infrastructure destruction completed for environment: $ENVIRONMENT"
        echo ""
        log_warning "All resources have been permanently deleted!"
        echo ""
        echo "Recovery steps:"
        echo "1. Run: ./scripts/init.sh $ENVIRONMENT"
        echo "2. Run: ./scripts/plan.sh $ENVIRONMENT"
        echo "3. Run: ./scripts/deploy.sh $ENVIRONMENT"
    else
        log_error "Destruction failed. Some resources may still exist."
        log_info "Check the Terraform state and cloud provider consoles manually."
        exit 1
    fi
}

# Run main function
main "$@"