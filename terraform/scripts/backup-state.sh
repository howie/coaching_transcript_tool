#!/bin/bash

# Terraform State Backup Script
# Usage: ./backup-state.sh [environment] [bucket_name]

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

# Default values
ENVIRONMENT=${1:-production}
BUCKET_NAME=${2:-coaching-assistant-terraform-state}
BACKUP_DIR="backups/state"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "🔄 Terraform State Backup"
echo "========================="

# Validate environment
case $ENVIRONMENT in
    development|staging|production)
        log_info "Backing up state for environment: $ENVIRONMENT"
        ;;
    *)
        log_error "Invalid environment: $ENVIRONMENT"
        log_error "Valid environments: development, staging, production"
        exit 1
        ;;
esac

# Create backup directory
mkdir -p "$BACKUP_DIR"
mkdir -p "backups/metadata"

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

# Backup main state file
log_info "Downloading state file..."
BACKUP_FILE="$BACKUP_DIR/terraform-$ENVIRONMENT-$TIMESTAMP.tfstate"

if gsutil cp "gs://$BUCKET_NAME/$ENVIRONMENT/default.tfstate" "$BACKUP_FILE" 2>/dev/null; then
    log_success "State backup saved: $BACKUP_FILE"
    
    # Get file size
    SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null || echo "unknown")
    log_info "Backup file size: $SIZE bytes"
    
    # Validate backup file (check if it's valid JSON)
    if jq empty "$BACKUP_FILE" 2>/dev/null; then
        RESOURCES=$(jq '.resources | length' "$BACKUP_FILE" 2>/dev/null || echo "unknown")
        TF_VERSION=$(jq -r '.terraform_version' "$BACKUP_FILE" 2>/dev/null || echo "unknown")
        log_success "Backup validation passed (Resources: $RESOURCES, TF Version: $TF_VERSION)"
    else
        log_warning "Backup file may be corrupted (invalid JSON)"
    fi
else
    log_error "Failed to download state file from gs://$BUCKET_NAME/$ENVIRONMENT/default.tfstate"
    log_info "This might be normal if no state exists yet"
    exit 1
fi

# Create metadata file
METADATA_FILE="backups/metadata/backup-$ENVIRONMENT-$TIMESTAMP.json"
cat > "$METADATA_FILE" << EOF
{
  "environment": "$ENVIRONMENT",
  "bucket": "$BUCKET_NAME",
  "backup_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "backup_file": "$BACKUP_FILE",
  "file_size": $SIZE,
  "terraform_version": "$(jq -r '.terraform_version' "$BACKUP_FILE" 2>/dev/null || echo "unknown")",
  "resource_count": $(jq '.resources | length' "$BACKUP_FILE" 2>/dev/null || echo 0),
  "backup_type": "manual",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo "unknown")",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"
}
EOF

log_success "Created metadata file: $METADATA_FILE"

# Backup versions (if they exist)
log_info "Backing up state versions..."
VERSION_DIR="$BACKUP_DIR/versions/$ENVIRONMENT-$TIMESTAMP"
mkdir -p "$VERSION_DIR"

# List all versions
VERSIONS=$(gsutil ls "gs://$BUCKET_NAME/$ENVIRONMENT/**" 2>/dev/null || echo "")
if [ -n "$VERSIONS" ]; then
    VERSION_COUNT=0
    while IFS= read -r version_path; do
        if [ -n "$version_path" ]; then
            VERSION_FILE="$VERSION_DIR/version-$VERSION_COUNT.tfstate"
            if gsutil cp "$version_path" "$VERSION_FILE" 2>/dev/null; then
                ((VERSION_COUNT++))
            fi
        fi
    done <<< "$VERSIONS"
    
    if [ $VERSION_COUNT -gt 0 ]; then
        log_success "Backed up $VERSION_COUNT state versions"
    else
        log_info "No state versions found"
    fi
else
    log_info "No state versions available"
fi

# Cleanup old backups (keep last 10 backups per environment)
log_info "Cleaning up old backups..."
OLD_BACKUPS=$(ls -t "$BACKUP_DIR"/terraform-$ENVIRONMENT-*.tfstate 2>/dev/null | tail -n +11)
if [ -n "$OLD_BACKUPS" ]; then
    echo "$OLD_BACKUPS" | xargs rm -f
    OLD_COUNT=$(echo "$OLD_BACKUPS" | wc -l | tr -d ' ')
    log_success "Removed $OLD_COUNT old backups (keeping latest 10)"
else
    log_info "No old backups to clean up"
fi

# Create backup index
log_info "Updating backup index..."
INDEX_FILE="backups/index.json"

if [ ! -f "$INDEX_FILE" ]; then
    echo '{"backups": []}' > "$INDEX_FILE"
fi

# Add current backup to index
TEMP_INDEX=$(mktemp)
jq --argjson new_backup "$(cat "$METADATA_FILE")" \
   '.backups += [$new_backup] | .backups = (.backups | sort_by(.backup_time) | reverse)' \
   "$INDEX_FILE" > "$TEMP_INDEX" && mv "$TEMP_INDEX" "$INDEX_FILE"

log_success "Updated backup index"

# Generate backup report
REPORT_FILE="backups/backup-report-$ENVIRONMENT-$TIMESTAMP.txt"
cat > "$REPORT_FILE" << EOF
Terraform State Backup Report
============================

Environment: $ENVIRONMENT
Date: $(date)
Bucket: gs://$BUCKET_NAME

Backup Details:
- Main state file: $BACKUP_FILE
- File size: $SIZE bytes
- Resources: $(jq '.resources | length' "$BACKUP_FILE" 2>/dev/null || echo "unknown")
- Terraform version: $(jq -r '.terraform_version' "$BACKUP_FILE" 2>/dev/null || echo "unknown")

Git Information:
- Commit: $(git rev-parse HEAD 2>/dev/null || echo "unknown")
- Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

Backup Status: SUCCESS

Next Steps:
- To restore this backup: ./scripts/restore-state.sh "$BACKUP_FILE" $ENVIRONMENT
- To view all backups: ./scripts/list-backups.sh $ENVIRONMENT
- To inspect state: ./scripts/inspect-state.sh
EOF

log_success "Generated backup report: $REPORT_FILE"

# Final summary
echo ""
log_success "🎉 Backup completed successfully!"
echo ""
echo "📋 Summary:"
echo "  • Environment: $ENVIRONMENT"
echo "  • Backup file: $BACKUP_FILE"
echo "  • File size: $SIZE bytes"
echo "  • Resources: $(jq '.resources | length' "$BACKUP_FILE" 2>/dev/null || echo "unknown")"
echo "  • Report: $REPORT_FILE"
echo ""
echo "🔄 To restore this backup:"
echo "  ./scripts/restore-state.sh \"$BACKUP_FILE\" $ENVIRONMENT"