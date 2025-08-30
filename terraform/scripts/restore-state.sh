#!/bin/bash

# Terraform State Restore Script
# Usage: ./restore-state.sh <backup_file> [environment] [bucket_name]

set -e

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

# Check arguments
BACKUP_FILE=${1}
ENVIRONMENT=${2:-production}
BUCKET_NAME=${3:-coaching-assistant-terraform-state}

if [ -z "$BACKUP_FILE" ]; then
    log_error "Usage: $0 <backup_file> [environment] [bucket_name]"
    echo ""
    echo "Examples:"
    echo "  $0 backups/state/terraform-production-20250830-143022.tfstate"
    echo "  $0 backups/state/terraform-staging-20250830-143022.tfstate staging"
    echo ""
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Terraform State Restore"
echo "=========================="

# Validate environment
case $ENVIRONMENT in
    development|staging|production)
        log_info "Restoring state for environment: $ENVIRONMENT"
        ;;
    *)
        log_error "Invalid environment: $ENVIRONMENT"
        log_error "Valid environments: development, staging, production"
        exit 1
        ;;
esac

log_info "Source: $BACKUP_FILE"
log_info "Target: gs://$BUCKET_NAME/$ENVIRONMENT/default.tfstate"

# Validate backup file
log_info "Validating backup file..."
if ! jq empty "$BACKUP_FILE" 2>/dev/null; then
    log_error "Backup file is not valid JSON"
    exit 1
fi

RESOURCES=$(jq '.resources | length' "$BACKUP_FILE" 2>/dev/null || echo "unknown")
TF_VERSION=$(jq -r '.terraform_version' "$BACKUP_FILE" 2>/dev/null || echo "unknown")
BACKUP_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null || echo "unknown")

log_success "Backup file validation passed"
log_info "Resources: $RESOURCES"
log_info "Terraform version: $TF_VERSION"
log_info "File size: $BACKUP_SIZE bytes"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    log_error "Please authenticate with gcloud first: gcloud auth login"
    exit 1
fi

# Check if bucket exists
if ! gsutil ls gs://$BUCKET_NAME >/dev/null 2>&1; then
    log_error "Bucket gs://$BUCKET_NAME does not exist"
    exit 1
fi

# Create pre-restore backup of current state
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
PRE_RESTORE_DIR="backups/pre-restore"
mkdir -p "$PRE_RESTORE_DIR"

log_info "Creating pre-restore backup..."
PRE_RESTORE_FILE="$PRE_RESTORE_DIR/pre-restore-$ENVIRONMENT-$TIMESTAMP.tfstate"

if gsutil cp "gs://$BUCKET_NAME/$ENVIRONMENT/default.tfstate" "$PRE_RESTORE_FILE" 2>/dev/null; then
    log_success "Pre-restore backup created: $PRE_RESTORE_FILE"
    
    # Validate current state
    if jq empty "$PRE_RESTORE_FILE" 2>/dev/null; then
        CURRENT_RESOURCES=$(jq '.resources | length' "$PRE_RESTORE_FILE" 2>/dev/null || echo "unknown")
        log_info "Current state has $CURRENT_RESOURCES resources"
    fi
else
    log_warning "No existing state found to backup"
fi

# Confirm restore operation
if [ -t 0 ]; then  # Check if running interactively
    echo ""
    log_warning "This will replace the current Terraform state!"
    echo "Current state will be backed up to: $PRE_RESTORE_FILE"
    echo ""
    echo "Restore details:"
    echo "  • From: $BACKUP_FILE"
    echo "  • To: $ENVIRONMENT environment"
    echo "  • Resources to restore: $RESOURCES"
    echo ""
    read -p "Are you sure you want to continue? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "Restore cancelled by user"
        exit 1
    fi
fi

# Perform the restore
log_info "Restoring state file..."
if gsutil cp "$BACKUP_FILE" "gs://$BUCKET_NAME/$ENVIRONMENT/default.tfstate"; then
    log_success "State file restored successfully"
else
    log_error "Failed to restore state file"
    exit 1
fi

# Verify the restore
log_info "Verifying restore..."
TEMP_VERIFY=$(mktemp)
if gsutil cp "gs://$BUCKET_NAME/$ENVIRONMENT/default.tfstate" "$TEMP_VERIFY" 2>/dev/null; then
    if jq empty "$TEMP_VERIFY" 2>/dev/null; then
        RESTORED_RESOURCES=$(jq '.resources | length' "$TEMP_VERIFY" 2>/dev/null || echo "unknown")
        RESTORED_VERSION=$(jq -r '.terraform_version' "$TEMP_VERIFY" 2>/dev/null || echo "unknown")
        
        log_success "Restore verification passed"
        log_info "Restored resources: $RESTORED_RESOURCES"
        log_info "Terraform version: $RESTORED_VERSION"
    else
        log_error "Restored state file is invalid"
        rm -f "$TEMP_VERIFY"
        exit 1
    fi
    rm -f "$TEMP_VERIFY"
else
    log_error "Failed to verify restored state"
    exit 1
fi

# Create restore metadata
METADATA_DIR="backups/metadata"
mkdir -p "$METADATA_DIR"
METADATA_FILE="$METADATA_DIR/restore-$ENVIRONMENT-$TIMESTAMP.json"

cat > "$METADATA_FILE" << EOF
{
  "environment": "$ENVIRONMENT",
  "bucket": "$BUCKET_NAME",
  "restore_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "backup_file": "$BACKUP_FILE",
  "pre_restore_backup": "$PRE_RESTORE_FILE",
  "restored_resources": $RESTORED_RESOURCES,
  "backup_resources": $RESOURCES,
  "terraform_version": "$RESTORED_VERSION",
  "restore_type": "manual",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo "unknown")",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"
}
EOF

log_success "Created restore metadata: $METADATA_FILE"

# Update backup index
INDEX_FILE="backups/index.json"
if [ -f "$INDEX_FILE" ]; then
    log_info "Updating backup index..."
    TEMP_INDEX=$(mktemp)
    jq --argjson restore_info "$(cat "$METADATA_FILE")" \
       '.restores += [$restore_info] | .restores = (.restores | sort_by(.restore_time) | reverse)' \
       "$INDEX_FILE" > "$TEMP_INDEX" && mv "$TEMP_INDEX" "$INDEX_FILE"
    log_success "Updated backup index"
fi

# Generate restore report
REPORT_FILE="backups/restore-report-$ENVIRONMENT-$TIMESTAMP.txt"
cat > "$REPORT_FILE" << EOF
Terraform State Restore Report
==============================

Environment: $ENVIRONMENT
Date: $(date)
Bucket: gs://$BUCKET_NAME

Restore Details:
- Source backup: $BACKUP_FILE
- Resources restored: $RESTORED_RESOURCES
- Terraform version: $RESTORED_VERSION
- Pre-restore backup: $PRE_RESTORE_FILE

Git Information:
- Commit: $(git rev-parse HEAD 2>/dev/null || echo "unknown")
- Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

Restore Status: SUCCESS

Next Steps:
1. Verify the restored state:
   cd terraform/environments/$ENVIRONMENT
   terraform plan

2. If restore was incorrect, revert using:
   ./scripts/restore-state.sh "$PRE_RESTORE_FILE" $ENVIRONMENT

3. Run infrastructure validation:
   ./scripts/validate.sh $ENVIRONMENT
EOF

log_success "Generated restore report: $REPORT_FILE"

# Provide next steps
echo ""
log_success "🎉 State restore completed successfully!"
echo ""
echo "📋 Summary:"
echo "  • Environment: $ENVIRONMENT"
echo "  • Resources restored: $RESTORED_RESOURCES"
echo "  • Pre-restore backup: $PRE_RESTORE_FILE"
echo "  • Report: $REPORT_FILE"
echo ""
echo "🔍 Next steps:"
echo "  1. Verify the restore:"
echo "     cd terraform/environments/$ENVIRONMENT"
echo "     terraform plan"
echo ""
echo "  2. If restore was incorrect, revert using:"
echo "     ./scripts/restore-state.sh \"$PRE_RESTORE_FILE\" $ENVIRONMENT"
echo ""
log_warning "Important: Run 'terraform plan' to verify the state matches your configuration!"