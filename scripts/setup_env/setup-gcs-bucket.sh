#!/bin/bash

# Google Cloud Storage Bucket Setup Script for Coaching Assistant
# Usage: ./setup-gcs-bucket.sh PROJECT_ID ENVIRONMENT

set -e

PROJECT_ID=$1
ENVIRONMENT=${2:-development}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: Please provide PROJECT_ID as first argument"
    echo "Usage: ./setup-gcs-bucket.sh PROJECT_ID [ENVIRONMENT]"
    echo "Example: ./setup-gcs-bucket.sh my-gcp-project development"
    exit 1
fi

# Map environment to bucket suffix
case $ENVIRONMENT in
    development)
        BUCKET_SUFFIX=dev
        ;;
    staging)
        BUCKET_SUFFIX=staging
        ;;
    production)
        BUCKET_SUFFIX=prod
        ;;
    *)
        echo "Warning: Unknown environment '$ENVIRONMENT', using 'dev'"
        BUCKET_SUFFIX=dev
        ;;
esac

BUCKET_NAME="coaching-audio-${BUCKET_SUFFIX}"
SERVICE_ACCOUNT_EMAIL="coaching-storage@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🚀 Setting up Google Cloud Storage for Coaching Assistant"
echo "Project ID: $PROJECT_ID"
echo "Environment: $ENVIRONMENT"
echo "Bucket Name: $BUCKET_NAME"
echo ""

# Set the active project
echo "📋 Setting active project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable storage.googleapis.com
gcloud services enable iam.googleapis.com

# Create the bucket
echo "🪣 Creating storage bucket..."
if gsutil ls gs://$BUCKET_NAME 2>/dev/null; then
    echo "Bucket gs://$BUCKET_NAME already exists"
else
    gsutil mb -p $PROJECT_ID -c STANDARD -l us-central1 gs://$BUCKET_NAME
    echo "Created bucket gs://$BUCKET_NAME"
fi

# Set bucket lifecycle for auto-deletion (24 hours)
echo "⏰ Setting up auto-deletion lifecycle (24 hours)..."
cat > /tmp/lifecycle.json << EOF
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 1}
    }
  ]
}
EOF

gsutil lifecycle set /tmp/lifecycle.json gs://$BUCKET_NAME

# Set CORS policy for direct uploads
echo "🌐 Setting up CORS policy..."
cat > /tmp/cors.json << EOF
[
  {
    "origin": ["https://coachly.doxa.com.tw", "http://localhost:3000"],
    "method": ["GET", "PUT", "POST", "HEAD"],
    "responseHeader": ["Content-Type", "Access-Control-Allow-Origin"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set /tmp/cors.json gs://$BUCKET_NAME

# Create service account
echo "👤 Creating service account..."
if gcloud iam service-accounts describe coaching-storage@$PROJECT_ID.iam.gserviceaccount.com 2>/dev/null; then
    echo "Service account already exists"
else
    gcloud iam service-accounts create coaching-storage \
        --display-name="Coaching Assistant Storage Account" \
        --description="Service account for audio file storage operations"
fi

# Grant bucket permissions
echo "🔐 Setting up permissions..."
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT_EMAIL}:objectAdmin gs://$BUCKET_NAME
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT_EMAIL}:legacyBucketReader gs://$BUCKET_NAME

# Create service account key
echo "🗝️  Creating service account key..."
KEY_FILE="coaching-storage-${ENVIRONMENT}.json"
gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=${SERVICE_ACCOUNT_EMAIL}

# Convert to base64
echo "📝 Converting key to base64..."
BASE64_KEY=$(base64 -i $KEY_FILE)

# Cleanup temporary files
rm -f /tmp/lifecycle.json /tmp/cors.json

# Output environment variables
echo ""
echo "✅ Setup complete! Add these environment variables:"
echo ""
echo "ENVIRONMENT=$ENVIRONMENT"
echo "GOOGLE_PROJECT_ID=$PROJECT_ID"
echo "GOOGLE_STORAGE_BUCKET=$BUCKET_NAME"
echo "GOOGLE_APPLICATION_CREDENTIALS_JSON=$BASE64_KEY"
echo ""
echo "📋 Service account key saved to: $KEY_FILE"
echo "⚠️  Keep this file secure and do not commit it to version control!"
echo ""

# Test the setup
echo "🧪 Testing bucket access..."
if echo "test" | gsutil cp - gs://$BUCKET_NAME/test.txt && gsutil rm gs://$BUCKET_NAME/test.txt; then
    echo "✅ Bucket access test successful!"
else
    echo "❌ Bucket access test failed"
    exit 1
fi

echo ""
echo "🎉 Google Cloud Storage setup completed successfully!"
echo "You can now start using the audio upload feature."