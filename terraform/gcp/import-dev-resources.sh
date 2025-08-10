#!/bin/bash

# Import script for existing GCP resources in dev workspace
# This script imports existing GCP resources into Terraform dev workspace

set -e

echo "🔄 Importing existing GCP resources into Terraform dev workspace..."

# Check if we're in the right directory
if [[ ! -f "main.tf" ]]; then
    echo "❌ Error: Please run this script from the terraform/gcp directory"
    exit 1
fi

# Check if we're in dev workspace
current_workspace=$(terraform workspace show)
if [[ "$current_workspace" != "dev" ]]; then
    echo "❌ Error: Please switch to dev workspace first: terraform workspace select dev"
    exit 1
fi

echo "📝 Importing existing service account..."
if terraform import google_service_account.coaching_storage projects/coachingassistant/serviceAccounts/coaching-storage@coachingassistant.iam.gserviceaccount.com; then
    echo "✅ Service account imported successfully"
else
    echo "⚠️ Service account import failed (may already be imported)"
fi

echo "📝 Importing existing custom IAM role..."
if terraform import google_project_iam_custom_role.speech_v2_user projects/coachingassistant/roles/speechV2User; then
    echo "✅ Custom IAM role imported successfully"
else
    echo "⚠️ Custom IAM role import failed (may already be imported)"
fi

echo "📝 Importing existing project IAM members..."
terraform import 'google_project_iam_member.coaching_storage_roles["roles/speech.client"]' "coachingassistant roles/speech.client serviceAccount:coaching-storage@coachingassistant.iam.gserviceaccount.com" || echo "⚠️ Speech client role import failed"

terraform import 'google_project_iam_member.coaching_storage_roles["roles/storage.objectAdmin"]' "coachingassistant roles/storage.objectAdmin serviceAccount:coaching-storage@coachingassistant.iam.gserviceaccount.com" || echo "⚠️ Storage object admin role import failed"

echo "📝 Importing existing APIs..."
for api in "speech.googleapis.com" "storage-api.googleapis.com" "storage-component.googleapis.com" "iam.googleapis.com" "serviceusage.googleapis.com" "cloudresourcemanager.googleapis.com"; do
    terraform import "google_project_service.apis[\"$api\"]" "coachingassistant/$api" || echo "⚠️ API $api import failed"
done

terraform import google_project_service.logging coachingassistant/logging.googleapis.com || echo "⚠️ Logging API import failed"
terraform import google_project_service.monitoring coachingassistant/monitoring.googleapis.com || echo "⚠️ Monitoring API import failed"  
terraform import google_project_service.errorreporting coachingassistant/clouderrorreporting.googleapis.com || echo "⚠️ Error reporting API import failed"

echo ""
echo "🎯 Import process completed for dev workspace!"
echo ""
echo "Next steps:"
echo "1. Run 'terraform plan -var-file=\"terraform.tfvars.dev\"' to see remaining changes"  
echo "2. Run 'terraform apply -var-file=\"terraform.tfvars.dev\"' to create dev buckets"