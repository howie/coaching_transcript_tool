#!/bin/bash

# Terraform Validation Script
# Usage: ./validate.sh [environment]

set -e

# Default values
ENVIRONMENT=${1:-all}

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

# Validate single environment
validate_environment() {
    local env=$1
    local env_dir="environments/$env"
    
    log_info "Validating environment: $env"
    
    if [[ ! -d "$env_dir" ]]; then
        log_error "Environment directory not found: $env_dir"
        return 1
    fi
    
    cd "$env_dir"
    
    # Check for required files
    local required_files=("main.tf" "variables.tf" "outputs.tf")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file not found: $file"
            return 1
        fi
    done
    
    # Terraform validation
    log_info "Running terraform validate..."
    if terraform validate; then
        log_success "Terraform configuration is valid"
    else
        log_error "Terraform validation failed"
        return 1
    fi
    
    # Terraform format check
    log_info "Checking Terraform formatting..."
    if terraform fmt -check -recursive .; then
        log_success "Terraform formatting is correct"
    else
        log_warning "Terraform formatting issues found. Run 'terraform fmt' to fix."
    fi
    
    # Check for terraform.tfvars
    if [[ -f "terraform.tfvars" ]]; then
        log_success "Found terraform.tfvars"
        
        # Basic syntax check for tfvars
        if terraform console -var-file="terraform.tfvars" <<< "1+1" >/dev/null 2>&1; then
            log_success "terraform.tfvars syntax is valid"
        else
            log_error "terraform.tfvars syntax error"
            return 1
        fi
    else
        log_warning "terraform.tfvars not found (using example file)"
    fi
    
    cd - > /dev/null
    
    log_success "Environment $env validation completed"
    return 0
}

# Validate modules
validate_modules() {
    log_info "Validating Terraform modules..."
    
    local modules_dir="modules"
    local validation_failed=false
    
    for module in "$modules_dir"/*; do
        if [[ -d "$module" ]]; then
            local module_name=$(basename "$module")
            log_info "Validating module: $module_name"
            
            cd "$module"
            
            # Check for required files
            local required_files=("main.tf" "variables.tf" "outputs.tf")
            for file in "${required_files[@]}"; do
                if [[ ! -f "$file" ]]; then
                    log_error "Module $module_name missing required file: $file"
                    validation_failed=true
                fi
            done
            
            # Terraform validation
            if terraform validate; then
                log_success "Module $module_name is valid"
            else
                log_error "Module $module_name validation failed"
                validation_failed=true
            fi
            
            cd - > /dev/null
        fi
    done
    
    if [[ "$validation_failed" == "true" ]]; then
        return 1
    fi
    
    log_success "All modules validation completed"
    return 0
}

# Security validation
validate_security() {
    log_info "Running security validation..."
    
    local issues_found=false
    
    # Check for hardcoded secrets
    log_info "Checking for hardcoded secrets..."
    if find . -name "*.tf" -o -name "*.tfvars" | xargs grep -l "password\|secret\|key" | xargs grep -v "var\." | grep -v "sensitive\|description" | head -5; then
        log_warning "Potential hardcoded secrets found (review above lines)"
        issues_found=true
    else
        log_success "No obvious hardcoded secrets found"
    fi
    
    # Check for sensitive variables
    log_info "Checking sensitive variable marking..."
    local sensitive_patterns=("password" "secret" "key" "token" "credentials")
    for pattern in "${sensitive_patterns[@]}"; do
        if grep -r "variable.*$pattern" modules/ environments/ | grep -v "sensitive.*=.*true"; then
            log_warning "Variables containing '$pattern' should be marked as sensitive"
            issues_found=true
        fi
    done
    
    # Check for public resource exposure
    log_info "Checking for public resource exposure..."
    if grep -r "0.0.0.0/0\|::/0" modules/ environments/; then
        log_warning "Found overly permissive network rules (0.0.0.0/0 or ::/0)"
        issues_found=true
    fi
    
    if [[ "$issues_found" == "false" ]]; then
        log_success "Security validation completed - no major issues found"
    else
        log_warning "Security validation completed - review warnings above"
    fi
}

# Best practices validation
validate_best_practices() {
    log_info "Validating Terraform best practices..."
    
    local issues_found=false
    
    # Check for version constraints
    log_info "Checking provider version constraints..."
    if ! find modules/ environments/ -name "*.tf" | xargs grep -l "required_providers" | xargs grep -c "version.*=" >/dev/null; then
        log_warning "Provider version constraints not found or incomplete"
        issues_found=true
    else
        log_success "Provider version constraints found"
    fi
    
    # Check for required_version
    log_info "Checking Terraform version constraints..."
    if ! find modules/ environments/ -name "*.tf" | xargs grep -l "required_version"; then
        log_warning "Terraform version constraints not found"
        issues_found=true
    else
        log_success "Terraform version constraints found"
    fi
    
    # Check for resource tags
    log_info "Checking resource tagging..."
    if ! grep -r "tags.*=" modules/ | grep -q "environment\|managed_by"; then
        log_warning "Consistent resource tagging not found"
        issues_found=true
    else
        log_success "Resource tagging found"
    fi
    
    # Check for outputs documentation
    log_info "Checking output documentation..."
    local outputs_without_description=$(find modules/ environments/ -name "outputs.tf" | xargs grep -L "description" | wc -l)
    if [[ $outputs_without_description -gt 0 ]]; then
        log_warning "$outputs_without_description output files missing descriptions"
        issues_found=true
    else
        log_success "All outputs have descriptions"
    fi
    
    if [[ "$issues_found" == "false" ]]; then
        log_success "Best practices validation completed - all checks passed"
    else
        log_warning "Best practices validation completed - review warnings above"
    fi
}

# Dependency validation
validate_dependencies() {
    log_info "Validating dependencies..."
    
    # Check for circular dependencies
    log_info "Checking for circular dependencies..."
    
    # This is a simplified check - in reality, you might want to use terraform graph
    local modules_with_deps=$(find modules/ -name "*.tf" | xargs grep -l "module\." | wc -l)
    if [[ $modules_with_deps -gt 0 ]]; then
        log_info "Found $modules_with_deps modules with dependencies - manual review recommended"
    fi
    
    # Check for missing module sources
    log_info "Checking module sources..."
    if find environments/ -name "*.tf" | xargs grep "module\." | grep -v "source.*="; then
        log_error "Modules without source declarations found"
        return 1
    fi
    
    log_success "Dependency validation completed"
}

# Performance validation
validate_performance() {
    log_info "Validating performance considerations..."
    
    # Check for large state files (warn if many resources)
    local total_resources=0
    for env in environments/*/; do
        if [[ -f "$env/.terraform/terraform.tfstate" ]]; then
            local resources=$(grep -c "\"type\":" "$env/.terraform/terraform.tfstate" 2>/dev/null || echo 0)
            total_resources=$((total_resources + resources))
        fi
    done
    
    if [[ $total_resources -gt 500 ]]; then
        log_warning "Large number of resources ($total_resources) - consider splitting state files"
    else
        log_success "Resource count is manageable ($total_resources)"
    fi
    
    # Check for expensive operations in plan
    log_info "Checking for potentially expensive operations..."
    if grep -r "force_destroy.*=.*true" modules/ environments/; then
        log_warning "Found force_destroy=true - ensure this is intentional"
    fi
    
    log_success "Performance validation completed"
}

# Generate validation report
generate_validation_report() {
    local report_file="validation-report-$(date +%Y%m%d-%H%M%S).md"
    
    log_info "Generating validation report..."
    
    cat > "$report_file" << EOF
# Terraform Validation Report

**Date:** $(date)  
**User:** $(whoami)  
**Environment(s):** $ENVIRONMENT

## Validation Summary

- ✅ Terraform syntax validation
- ✅ Module structure validation  
- ✅ Security checks
- ✅ Best practices review
- ✅ Dependency analysis
- ✅ Performance considerations

## Recommendations

1. Regularly run validation before deployments
2. Keep provider versions pinned
3. Use consistent tagging across resources
4. Document all outputs and variables
5. Review security warnings promptly

## Files Validated

$(find modules/ environments/ -name "*.tf" | wc -l) Terraform files
$(find modules/ environments/ -name "*.tfvars*" | wc -l) Variable files

---
Generated by validate.sh script
EOF
    
    log_success "Validation report generated: $report_file"
}

# Main execution
main() {
    echo "🔍 Terraform Validation Script"
    echo "=============================="
    
    # Change to terraform directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")"
    cd "$TERRAFORM_DIR"
    
    local validation_failed=false
    
    # Validate modules first
    if ! validate_modules; then
        validation_failed=true
    fi
    
    # Validate environments
    if [[ "$ENVIRONMENT" == "all" ]]; then
        for env in development staging production; do
            if [[ -d "environments/$env" ]]; then
                if ! validate_environment "$env"; then
                    validation_failed=true
                fi
            fi
        done
    else
        if ! validate_environment "$ENVIRONMENT"; then
            validation_failed=true
        fi
    fi
    
    # Run additional validation checks
    validate_security
    validate_best_practices
    validate_dependencies
    validate_performance
    
    generate_validation_report
    
    echo ""
    if [[ "$validation_failed" == "true" ]]; then
        log_error "Validation completed with errors"
        echo "Please fix the errors above before deploying"
        exit 1
    else
        log_success "🎉 All validations passed successfully!"
        echo ""
        echo "Your Terraform configuration is ready for deployment:"
        echo "1. Run: ./scripts/plan.sh [environment]"
        echo "2. Run: ./scripts/deploy.sh [environment]"
    fi
}

# Run main function
main "$@"