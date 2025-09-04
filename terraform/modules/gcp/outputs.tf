# Project Information
output "project_id" {
  description = "GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP region"
  value       = var.region
}

# Storage Module Outputs
output "storage_buckets" {
  description = "Created storage buckets"
  value       = module.storage.buckets
}

output "audio_bucket_name" {
  description = "Audio storage bucket name"
  value       = module.storage.audio_bucket_name
}

output "transcript_bucket_name" {
  description = "Transcript storage bucket name"
  value       = module.storage.transcript_bucket_name
}

output "audit_bucket_name" {
  description = "Audit logs bucket name"
  value       = module.storage.audit_bucket_name
}

# IAM Module Outputs
output "service_accounts" {
  description = "Created service accounts"
  value       = module.iam.service_accounts
}

output "main_service_account_email" {
  description = "Main service account email"
  value       = module.iam.main_service_account_email
}

output "main_service_account_key" {
  description = "Main service account key"
  value       = module.iam.main_service_account_key
  sensitive   = true
}

# Speech Module Outputs
output "speech_api_enabled" {
  description = "Whether Speech API is enabled"
  value       = module.speech.api_enabled
}

output "speech_v2_enabled" {
  description = "Whether Speech v2 API is enabled"
  value       = var.enable_speech_v2
}

# Secret Manager Outputs
output "secrets" {
  description = "Created secrets"
  value       = { for k, v in google_secret_manager_secret.api_secrets : k => v.id }
}

output "secret_versions" {
  description = "Secret versions"
  value       = { for k, v in google_secret_manager_secret_version.api_secrets : k => v.id }
  sensitive   = true
}

# Enabled APIs
output "enabled_apis" {
  description = "List of enabled APIs"
  value       = [for api in google_project_service.required_apis : api.service]
}

# Monitoring Outputs
output "monitoring_enabled" {
  description = "Whether monitoring is enabled"
  value       = var.enable_monitoring
}

output "notification_channels" {
  description = "Created notification channels"
  value       = var.enable_monitoring ? [for ch in google_monitoring_notification_channel.channels : ch.id] : []
}

output "alert_policies" {
  description = "Created alert policies"
  value = var.enable_monitoring ? {
    storage_errors = google_monitoring_alert_policy.storage_errors[0].id
    speech_quota   = google_monitoring_alert_policy.speech_quota[0].id
  } : {}
}

# Audit Logging Outputs
output "audit_logs_enabled" {
  description = "Whether audit logs are enabled"
  value       = var.enable_audit_logs
}

output "audit_sink_id" {
  description = "Audit log sink ID"
  value       = var.enable_audit_logs ? google_logging_project_sink.audit_sink[0].id : ""
}

# Environment Information
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "resource_labels" {
  description = "Standard resource labels"
  value = {
    environment = var.environment
    managed_by  = "terraform"
    project     = var.project_id
  }
}