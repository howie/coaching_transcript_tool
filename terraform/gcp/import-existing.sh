#!/bin/bash

# Import script for existing GCP resources
# This script imports existing GCP resources into Terraform state

set -e

echo "🔄 Importing existing GCP resources into Terraform state..."

# Check if we're in the right directory
if [[ ! -f "main.tf" ]]; then
    echo "❌ Error: Please run this script from the terraform/gcp directory"
    exit 1
fi

# Check if Terraform is initialized
if [[ ! -d ".terraform" ]]; then
    echo "🔧 Initializing Terraform..."
    terraform init
fi

# Import existing service account
echo "📝 Importing existing service account..."
if terraform import google_service_account.coaching_storage projects/coachingassistant/serviceAccounts/coaching-storage@coachingassistant.iam.gserviceaccount.com; then
    echo "✅ Service account imported successfully"
else
    echo "⚠️ Service account import failed (may already be imported)"
fi

# Check for existing buckets and import if they exist
echo "🔍 Checking for existing storage buckets..."

# Try to import audio storage bucket if it exists
if gsutil ls gs://coaching-audio-prod >/dev/null 2>&1; then
    echo "📦 Found existing audio storage bucket, importing..."
    terraform import google_storage_bucket.audio_storage coaching-audio-prod || echo "⚠️ Audio bucket import failed (may already be imported)"
else
    echo "ℹ️ Audio storage bucket does not exist, will be created"
fi

# Try to import transcript storage bucket if it exists  
if gsutil ls gs://coaching-transcript-prod >/dev/null 2>&1; then
    echo "📦 Found existing transcript storage bucket, importing..."
    terraform import google_storage_bucket.transcript_storage coaching-transcript-prod || echo "⚠️ Transcript bucket import failed (may already be imported)"
else
    echo "ℹ️ Transcript storage bucket does not exist, will be created"
fi

echo ""
echo "🎯 Import process completed!"
echo ""
echo "Next steps:"
echo "1. Run 'terraform plan' to see remaining changes"
echo "2. Run 'terraform apply' to create missing resources"
echo "3. Run 'make env-file' to generate environment variables"
