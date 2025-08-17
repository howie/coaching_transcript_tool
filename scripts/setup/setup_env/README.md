# Setup Environment Scripts

This directory contains scripts for setting up the Google Cloud Storage (GCS) environment for the Coaching Assistant application.

## 📁 Script Overview: `setup-gcs.sh`

A comprehensive setup script that automates the creation and configuration of Google Cloud Storage resources needed for audio file uploads and transcription processing.

### 🎯 Purpose

This script sets up the complete GCS infrastructure including:
- Storage bucket with lifecycle policies
- Service account with appropriate permissions
- CORS configuration for frontend uploads
- Security configurations and best practices

## 🚀 Usage

### Prerequisites

1. **Google Cloud SDK** installed (`gcloud` command)
2. **Authenticated** with Google Cloud: 
   ```bash
   gcloud auth login
   ```
3. **Project access** with permissions to:
   - Create storage buckets
   - Create service accounts
   - Manage IAM permissions

### Running the Script

```bash
# Basic usage
./setup-gcs.sh PROJECT_ID [ENVIRONMENT]

# Examples
./setup-gcs.sh my-gcp-project development    # Creates coaching-audio-dev bucket
./setup-gcs.sh my-gcp-project staging       # Creates coaching-audio-staging bucket
./setup-gcs.sh my-gcp-project production    # Creates coaching-audio-prod bucket
```

### Parameters

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| `PROJECT_ID` | ✅ Yes | Your Google Cloud project ID | - |
| `ENVIRONMENT` | ❌ No | Environment name (development/staging/production) | `development` |

## 📋 What the Script Does

### 1. **Project Configuration**
- Sets the active GCP project
- Enables required APIs (Storage, IAM)

### 2. **Bucket Creation**
- **Name Pattern**: `coaching-audio-{environment}`
- **Location**: `us-central1`
- **Storage Class**: `STANDARD`
- **Features**:
  - Auto-deletion after 24 hours (GDPR compliance)
  - CORS enabled for frontend uploads

### 3. **Service Account Setup**
- **Account Name**: `coaching-storage@{project-id}.iam.gserviceaccount.com`
- **Display Name**: "Coaching Assistant Storage Account"
- **Permissions**:
  - `objectAdmin` - Full control over bucket objects
  - `legacyBucketReader` - List bucket contents

### 4. **Security Configuration**
- Generates service account key
- Converts key to base64 for easy environment variable usage
- Automatically updates `.gitignore` to prevent accidental commits
- Provides security warnings and best practices

### 5. **Verification**
- Tests bucket access with a temporary file
- Validates all permissions are correctly set

## 📝 Output

### Generated Files

```
coaching-storage-{environment}.json  # Service account key file
```

⚠️ **SECURITY WARNING**: This file contains sensitive credentials!
- Never commit to version control
- Delete after copying the base64 value
- Keep secure and never share

### Environment Variables

The script outputs ready-to-copy environment variables:

```env
ENVIRONMENT=development
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_STORAGE_BUCKET=coaching-audio-dev
GOOGLE_APPLICATION_CREDENTIALS_JSON=eyJ0eXBlIjoic2VydmljZV9hY2NvdW50Iiw...
```

Add these to your `.env` file:

```bash
# Copy the output and paste into your .env file
echo "GOOGLE_PROJECT_ID=your-project-id" >> .env
echo "GOOGLE_STORAGE_BUCKET=coaching-audio-dev" >> .env
echo "GOOGLE_APPLICATION_CREDENTIALS_JSON=base64-string" >> .env
```

## 🔐 Security Best Practices

1. **Immediate Actions After Running Script**:
   ```bash
   # 1. Copy the base64 credentials to .env
   # 2. Delete the JSON key file
   rm coaching-storage-*.json
   ```

2. **Key Management**:
   - Rotate service account keys every 90 days
   - Use different service accounts per environment
   - Monitor key usage in GCP Console

3. **Access Control**:
   - Limit service account permissions to minimum required
   - Use signed URLs for uploads (implemented in application)
   - Enable audit logging for sensitive operations

## 🧪 Verification

After setup, verify everything works:

```bash
# Check bucket exists and list contents
gcloud storage ls gs://coaching-audio-dev/

# Verify lifecycle policy (24-hour deletion)
gcloud storage buckets describe gs://coaching-audio-dev/ --format="get(lifecycle)"

# Check CORS configuration
gcloud storage buckets describe gs://coaching-audio-dev/ --format="get(cors)"

# Test with application API
curl -X POST http://localhost:8000/api/v1/sessions/{session_id}/confirm-upload
```

## 🔧 Troubleshooting

### Issue: Permission Denied

```bash
# Grant yourself Storage Admin role
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:your-email@example.com" \
  --role="roles/storage.admin"
```

### Issue: APIs Not Enabled

The script auto-enables APIs, but if it fails:
```bash
gcloud services enable storage.googleapis.com
gcloud services enable iam.googleapis.com
```

### Issue: Bucket Already Exists

The script handles this gracefully and reuses existing buckets. To start fresh:
```bash
# Delete existing bucket (must be empty)
gcloud storage rm -r gs://coaching-audio-dev/
```

### Issue: Service Account Already Exists

The script reuses existing accounts but generates new keys. To reset:
```bash
# Delete all existing keys
gcloud iam service-accounts keys list \
  --iam-account=coaching-storage@PROJECT_ID.iam.gserviceaccount.com

# Delete specific key
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=coaching-storage@PROJECT_ID.iam.gserviceaccount.com
```

## 🗑️ Complete Cleanup

To remove all created resources:

```bash
# 1. Delete bucket contents and bucket
gcloud storage rm -r gs://coaching-audio-dev/

# 2. Delete service account
gcloud iam service-accounts delete \
  coaching-storage@PROJECT_ID.iam.gserviceaccount.com

# 3. Remove local files
rm -f coaching-storage-*.json
rm -f *-base64.txt

# 4. Clean environment variables from .env
# Manual edit required
```

## 📚 Related Documentation

- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-for-using-and-managing-service-accounts)
- [Signed URLs for Direct Upload](https://cloud.google.com/storage/docs/access-control/signed-urls)
- [CORS Configuration](https://cloud.google.com/storage/docs/configuring-cors)

## 💡 Tips

1. **For Development**: Use personal GCP project with free tier
2. **For Production**: 
   - Use dedicated project with billing alerts
   - Enable audit logging
   - Set up monitoring for bucket usage
3. **Cost Optimization**:
   - 24-hour auto-deletion keeps costs minimal
   - Monitor usage with GCP Cost Explorer

## 🎯 Next Steps After Setup

1. **Run the script**:
   ```bash
   ./setup-gcs.sh your-project-id development
   ```

2. **Update `.env` file** with the output values

3. **Delete the JSON key file** for security

4. **Test the upload flow**:
   - Create a session via API
   - Get upload URL
   - Upload a file
   - Confirm upload with `/confirm-upload` endpoint
   - Start transcription

5. **Monitor in GCP Console**:
   - Check bucket for uploaded files
   - View service account activity
   - Monitor API usage

---

*Last Updated: 2025-01-09*