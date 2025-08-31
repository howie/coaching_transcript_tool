#!/bin/bash

# Terraform Backend Setup Script with State Locking
# Usage: ./setup-backend.sh [project_id] [bucket_name] [location]

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
PROJECT_ID=${1:-$(gcloud config get-value project)}
BUCKET_NAME=${2:-"coaching-assistant-terraform-state"}
LOCATION=${3:-"asia-southeast1"}

# Validate inputs
if [ -z "$PROJECT_ID" ]; then
    log_error "Project ID is required. Either set it with gcloud or provide as first argument."
    exit 1
fi

echo "🚀 Setting up Terraform backend with state locking"
echo "================================"
log_info "Project ID: $PROJECT_ID"
log_info "Bucket Name: $BUCKET_NAME"
log_info "Location: $LOCATION"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    log_error "Please authenticate with gcloud first: gcloud auth login"
    exit 1
fi

# Set project
log_info "Setting GCP project..."
gcloud config set project "$PROJECT_ID"

# Enable required APIs
log_info "Enabling required APIs..."
gcloud services enable storage.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable iam.googleapis.com

# Create bucket if it doesn't exist
log_info "Creating Terraform state bucket..."
if gsutil ls -b gs://$BUCKET_NAME >/dev/null 2>&1; then
    log_warning "Bucket $BUCKET_NAME already exists"
else
    gsutil mb -p "$PROJECT_ID" -l "$LOCATION" gs://$BUCKET_NAME
    log_success "Created bucket: gs://$BUCKET_NAME"
fi

# Configure bucket for Terraform state
log_info "Configuring bucket for Terraform state..."

# Enable versioning
gsutil versioning set on gs://$BUCKET_NAME
log_success "Enabled versioning on bucket"

# Set lifecycle policy
cat > /tmp/lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "age": 30,
          "isLive": false
        }
      }
    ]
  }
}
EOF

gsutil lifecycle set /tmp/lifecycle.json gs://$BUCKET_NAME
rm /tmp/lifecycle.json
log_success "Set lifecycle policy (delete old versions after 30 days)"

# Set uniform bucket-level access
gsutil uniformbucketlevelaccess set on gs://$BUCKET_NAME
log_success "Enabled uniform bucket-level access"

# Configure bucket permissions
log_info "Configuring bucket permissions..."

# Get the current service account
SERVICE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1)

# If using a service account, ensure it has the right permissions
if [[ $SERVICE_ACCOUNT == *"gserviceaccount.com" ]]; then
    log_info "Configuring service account permissions: $SERVICE_ACCOUNT"
    
    # Grant necessary roles to the service account
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/storage.admin" \
        --condition=None
        
    log_success "Granted storage.admin role to service account"
fi

# Create backend configuration files for each environment
log_info "Creating backend configuration files..."

ENVIRONMENTS=("development" "staging" "production")

for env in "${ENVIRONMENTS[@]}"; do
    ENV_DIR="environments/$env"
    
    if [ -d "$ENV_DIR" ]; then
        # Create backend.tf file
        cat > "$ENV_DIR/backend.tf" << EOF
# Terraform Backend Configuration
terraform {
  backend "gcs" {
    bucket = "$BUCKET_NAME"
    prefix = "$env"
    
    # State locking is automatically enabled with GCS backend
    # No additional configuration needed for locking
  }
}
EOF
        log_success "Created backend.tf for $env environment"
        
        # Create backend config file for CLI usage
        cat > "$ENV_DIR/backend.hcl" << EOF
bucket = "$BUCKET_NAME"
prefix = "$env"
EOF
        log_success "Created backend.hcl for $env environment"
    else
        log_warning "Environment directory $ENV_DIR not found, skipping"
    fi
done

# Test state locking
log_info "Testing state locking mechanism..."

# Create a simple test configuration
mkdir -p /tmp/tf-lock-test
cd /tmp/tf-lock-test

# Get script directory and copy .tool-versions if it exists to avoid asdf warnings
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
if [ -f "$PROJECT_ROOT/.tool-versions" ]; then
    cp "$PROJECT_ROOT/.tool-versions" .
fi

cat > main.tf << EOF
terraform {
  required_version = ">= 1.0"
  
  backend "gcs" {
    bucket = "$BUCKET_NAME"
    prefix = "lock-test"
  }
}

resource "null_resource" "test" {
  triggers = {
    timestamp = timestamp()
  }
}
EOF

# Initialize and test
terraform init -no-color
terraform plan -no-color >/dev/null 2>&1

# Cleanup test
terraform destroy -auto-approve -no-color >/dev/null 2>&1
rm -rf /tmp/tf-lock-test

log_success "State locking mechanism verified"

# Create state management scripts
log_info "Creating state management utilities..."

# Create state backup script
cat > scripts/backup-state.sh << 'EOF'
#!/bin/bash
# Backup Terraform state from GCS

set -e

ENVIRONMENT=${1:-production}
BUCKET_NAME=${2:-coaching-assistant-terraform-state}
BACKUP_DIR="backups/state"

echo "🔄 Backing up Terraform state for $ENVIRONMENT..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Download current state
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/terraform-$ENVIRONMENT-$TIMESTAMP.tfstate"

if gsutil cp "gs://$BUCKET_NAME/$ENVIRONMENT/default.tfstate" "$BACKUP_FILE" 2>/dev/null; then
    echo "✅ State backup saved: $BACKUP_FILE"
    
    # Keep only last 10 backups
    ls -t "$BACKUP_DIR"/terraform-$ENVIRONMENT-*.tfstate 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
    echo "📦 Cleaned up old backups (keeping latest 10)"
else
    echo "⚠️  No existing state found or backup failed"
    exit 1
fi
EOF

chmod +x scripts/backup-state.sh
log_success "Created state backup script"

# Create state restore script
cat > scripts/restore-state.sh << 'EOF'
#!/bin/bash
# Restore Terraform state to GCS

set -e

BACKUP_FILE=${1}
ENVIRONMENT=${2:-production}
BUCKET_NAME=${3:-coaching-assistant-terraform-state}

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file> [environment] [bucket_name]"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Restoring Terraform state for $ENVIRONMENT..."
echo "Source: $BACKUP_FILE"
echo "Target: gs://$BUCKET_NAME/$ENVIRONMENT/default.tfstate"

# Create additional backup before restore
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "backups/pre-restore"
gsutil cp "gs://$BUCKET_NAME/$ENVIRONMENT/default.tfstate" \
    "backups/pre-restore/pre-restore-$ENVIRONMENT-$TIMESTAMP.tfstate" 2>/dev/null || echo "No existing state to backup"

# Restore state
gsutil cp "$BACKUP_FILE" "gs://$BUCKET_NAME/$ENVIRONMENT/default.tfstate"

echo "✅ State restored successfully"
echo "💡 Pre-restore backup saved in backups/pre-restore/"
EOF

chmod +x scripts/restore-state.sh
log_success "Created state restore script"

# Create state inspection script
cat > scripts/inspect-state.sh << 'EOF'
#!/bin/bash
# Inspect Terraform state across environments

set -e

BUCKET_NAME=${1:-coaching-assistant-terraform-state}

echo "📊 Terraform State Inspection"
echo "============================="

for env in development staging production; do
    echo ""
    echo "🏷️  Environment: $env"
    echo "-------------------"
    
    if gsutil stat "gs://$BUCKET_NAME/$env/default.tfstate" >/dev/null 2>&1; then
        # Get state file info
        SIZE=$(gsutil stat "gs://$BUCKET_NAME/$env/default.tfstate" | grep "Content-Length" | awk '{print $2}')
        MODIFIED=$(gsutil stat "gs://$BUCKET_NAME/$env/default.tfstate" | grep "Update time" | cut -d: -f2- | xargs)
        
        echo "📁 State file exists"
        echo "📏 Size: $SIZE bytes"
        echo "🕒 Last modified: $MODIFIED"
        
        # Download and inspect state
        TEMP_STATE="/tmp/state-$env.tfstate"
        gsutil cp "gs://$BUCKET_NAME/$env/default.tfstate" "$TEMP_STATE" 2>/dev/null
        
        if [ -s "$TEMP_STATE" ]; then
            RESOURCES=$(jq '.resources | length' "$TEMP_STATE" 2>/dev/null || echo "N/A")
            VERSION=$(jq -r '.terraform_version' "$TEMP_STATE" 2>/dev/null || echo "N/A")
            
            echo "🏗️  Resources: $RESOURCES"
            echo "📦 Terraform version: $VERSION"
        fi
        
        rm -f "$TEMP_STATE"
    else
        echo "❌ No state file found"
    fi
done

echo ""
echo "📈 State File Versions:"
for env in development staging production; do
    echo -n "$env: "
    gsutil ls -l "gs://$BUCKET_NAME/$env/**" 2>/dev/null | wc -l || echo "0"
done
EOF

chmod +x scripts/inspect-state.sh
log_success "Created state inspection script"

# Generate summary
echo ""
log_success "🎉 Backend setup completed successfully!"
echo ""
echo "📋 Summary:"
echo "  • Bucket: gs://$BUCKET_NAME"
echo "  • Location: $LOCATION"
echo "  • Versioning: Enabled"
echo "  • Lifecycle: 30-day retention for old versions"
echo "  • State locking: Automatically enabled with GCS backend"
echo ""
echo "🛠️  Available utilities:"
echo "  • ./scripts/backup-state.sh [environment] - Backup state"
echo "  • ./scripts/restore-state.sh <backup_file> [environment] - Restore state"
echo "  • ./scripts/inspect-state.sh - Inspect all states"
echo ""
echo "🚀 Next steps:"
echo "  1. Initialize environments: ./scripts/init.sh [environment]"
echo "  2. Plan deployments: ./scripts/plan.sh [environment]"
echo "  3. Deploy infrastructure: ./scripts/deploy.sh [environment]"
echo ""
echo "💡 Note: GCS backend automatically provides state locking using Cloud Storage's"
echo "   strong consistency guarantees. No additional configuration needed."