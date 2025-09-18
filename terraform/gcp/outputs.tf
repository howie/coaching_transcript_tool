# Outputs for GCP Terraform configuration

output "project_id" {
  description = "The GCP project ID"
  value       = var.gcp_project_id
}

output "project_number" {
  description = "The GCP project number"
  value       = data.google_project.project.number
}

output "service_account_email" {
  description = "The service account email"
  value       = google_service_account.coaching_storage.email
}

output "service_account_id" {
  description = "The service account ID"
  value       = google_service_account.coaching_storage.account_id
}

output "service_account_key_id" {
  description = "The service account key ID"
  value       = google_service_account_key.coaching_storage_key.name
  sensitive   = true
}

output "service_account_private_key" {
  description = "The service account private key (base64 encoded)"
  value       = google_service_account_key.coaching_storage_key.private_key
  sensitive   = true
}

output "audio_storage_bucket" {
  description = "The audio storage bucket name"
  value       = google_storage_bucket.audio_storage.name
}

output "audio_storage_bucket_url" {
  description = "The audio storage bucket URL"
  value       = google_storage_bucket.audio_storage.url
}

# Transcript storage bucket outputs removed - transcripts stored in database

output "audio_storage_bucket_prod" {
  description = "The production audio storage bucket name"
  value       = google_storage_bucket.audio_storage_prod.name
}

output "audio_storage_bucket_prod_url" {
  description = "The production audio storage bucket URL"
  value       = google_storage_bucket.audio_storage_prod.url
}

# Production transcript storage bucket outputs removed - transcripts stored in database

output "enabled_apis" {
  description = "List of enabled APIs"
  value       = [for api in google_project_service.apis : api.service]
}

output "custom_speech_role_id" {
  description = "Custom Speech-to-Text v2 role ID"
  value       = google_project_iam_custom_role.speech_v2_user.role_id
}

output "service_account_credentials_json" {
  description = "Service account credentials in JSON format (decoded)"
  value       = base64decode(google_service_account_key.coaching_storage_key.private_key)
  sensitive   = true
}

# Environment variables template output
output "env_vars_template" {
  description = "Environment variables template for application configuration"
  value = {
    GOOGLE_APPLICATION_CREDENTIALS_JSON = base64decode(google_service_account_key.coaching_storage_key.private_key)
    GOOGLE_PROJECT_ID                   = var.gcp_project_id
    GCP_REGION                          = var.gcp_region
    AUDIO_STORAGE_BUCKET                = google_storage_bucket.audio_storage.name
    SPEECH_API_VERSION                  = "v2"
    ENVIRONMENT                         = var.environment == "dev" ? "development" : var.environment == "prod" ? "production" : var.environment
  }
  sensitive = true
}