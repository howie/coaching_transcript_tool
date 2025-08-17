# GCP Terraform Configuration

This directory contains Terraform configuration for setting up all Google Cloud Platform resources required by the Coaching Assistant application.

## Overview

This Terraform configuration sets up:

- **GCP Project APIs**: Speech-to-Text v2, Cloud Storage, IAM, etc.
- **Service Account**: `coaching-storage` with appropriate permissions
- **Storage Buckets**: Audio files (24h lifecycle) and transcripts
- **IAM Permissions**: Minimal required permissions for Speech-to-Text v2
- **Security**: Uniform bucket-level access, public access prevention

## Prerequisites

1. **Install Terraform** (>= 1.0)
   ```bash
   # macOS
   brew install terraform
   
   # Linux
   wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
   sudo apt update && sudo apt install terraform
   ```

2. **Install Google Cloud SDK**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Linux
   curl https://sdk.cloud.google.com | bash
   ```

3. **Authenticate with Google Cloud**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

4. **Set up project**
   ```bash
   gcloud config set project coachingassistant
   ```

## Quick Start

1. **Copy example variables**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit variables** (optional)
   ```bash
   nano terraform.tfvars
   ```

3. **Initialize Terraform**
   ```bash
   terraform init
   ```

4. **Plan the deployment**
   ```bash
   terraform plan
   ```

5. **Apply the configuration**
   ```bash
   terraform apply
   ```

## Configuration Files

- `main.tf` - Core infrastructure (project, APIs, storage)
- `variables.tf` - Input variables and defaults
- `iam.tf` - IAM roles and permissions configuration
- `services.tf` - GCP services and API configurations
- `outputs.tf` - Output values for application configuration
- `terraform.tfvars.example` - Example variables file

## Key Resources Created

### Service Account
- **Name**: `coaching-storage@coachingassistant.iam.gserviceaccount.com`
- **Permissions**: 
  - `roles/speech.user` - Speech-to-Text v2 API access
  - `roles/storage.objectAdmin` - Cloud Storage object management
  - `roles/storage.legacyBucketWriter` - Signed URL generation

### Storage Buckets
- **Audio Storage**: `coachingassistant-audio-storage`
  - 24-hour lifecycle (GDPR compliance)
  - CORS enabled for frontend uploads
  - Versioning enabled
- **Transcript Storage**: `coachingassistant-transcript-storage`
  - Long-term storage with lifecycle rules
  - Versioning enabled

### APIs Enabled
- Speech-to-Text API v2
- Cloud Storage APIs
- IAM API
- Cloud Resource Manager API
- Service Usage API
- Logging and Monitoring APIs
- Error Reporting API

## Environment Variables

After deployment, configure your application with these environment variables:

```bash
# Get the service account credentials
terraform output -raw service_account_credentials_json

# Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS_JSON="$(terraform output -raw service_account_credentials_json)"
export GCP_PROJECT_ID="$(terraform output -raw project_id)"
export AUDIO_STORAGE_BUCKET="$(terraform output -raw audio_storage_bucket)"
export TRANSCRIPT_STORAGE_BUCKET="$(terraform output -raw transcript_storage_bucket)"
```

Or use the template output:
```bash
terraform output env_vars_template
```

## Security Features

### IAM Security
- **Minimal permissions**: Service account has only required permissions
- **Custom roles**: Optional custom Speech-to-Text role with specific permissions
- **Conditional access**: Example conditional IAM bindings (commented out)

### Storage Security
- **Uniform bucket-level access**: Simplified and secure access control
- **Public access prevention**: Buckets cannot be made public
- **CORS restrictions**: Limited to specific domains
- **Lifecycle policies**: Automatic cleanup for compliance

### API Security
- **Service-specific permissions**: Each API has targeted access controls
- **Service account keys**: Properly managed with Terraform

## Troubleshooting

### Common Issues

1. **403 Permission Denied**
   ```bash
   # Ensure you're authenticated
   gcloud auth application-default login
   
   # Check current project
   gcloud config get-value project
   
   # Verify service account permissions
   gcloud projects get-iam-policy coachingassistant
   ```

2. **API Not Enabled**
   ```bash
   # Check enabled APIs
   gcloud services list --enabled
   
   # Force re-enable if needed
   terraform taint google_project_service.apis["speech.googleapis.com"]
   terraform apply
   ```

3. **Storage Access Issues**
   ```bash
   # Test storage access
   gsutil ls gs://coachingassistant-audio-storage
   
   # Check bucket IAM
   gsutil iam get gs://coachingassistant-audio-storage
   ```

### Manual Fixes (Emergency)

If Terraform fails, you can manually apply the key permissions:

```bash
# Add Speech-to-Text permissions
gcloud projects add-iam-policy-binding coachingassistant \
    --member="serviceAccount:coaching-storage@coachingassistant.iam.gserviceaccount.com" \
    --role="roles/speech.user"

# Add Storage permissions
gcloud projects add-iam-policy-binding coachingassistant \
    --member="serviceAccount:coaching-storage@coachingassistant.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

## Maintenance

### Updating Permissions
1. Modify `variables.tf` service_account_roles
2. Run `terraform plan` to review changes
3. Run `terraform apply` to update

### Adding New APIs
1. Add API to `required_apis` in `variables.tf`
2. Run `terraform apply`

### Monitoring
- Check Cloud Console for API usage
- Monitor IAM policy changes
- Review storage bucket access logs

## Cost Optimization

- Storage lifecycle rules minimize costs
- APIs are pay-per-use
- Monitor usage with Cloud Monitoring
- Consider budget alerts

## Migration from Manual Setup

If you have existing resources:

1. **Import existing service account**
   ```bash
   terraform import google_service_account.coaching_storage projects/coachingassistant/serviceAccounts/coaching-storage@coachingassistant.iam.gserviceaccount.com
   ```

2. **Import existing buckets** (if any)
   ```bash
   terraform import google_storage_bucket.audio_storage coachingassistant-audio-storage
   ```

3. **Review and apply**
   ```bash
   terraform plan
   terraform apply
   ```

## Related Documentation

- [GCP Speech-to-Text v2 API](https://cloud.google.com/speech-to-text/v2/docs)
- [Cloud Storage IAM](https://cloud.google.com/storage/docs/access-control/iam)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest)
- [Project Documentation](../../docs/)