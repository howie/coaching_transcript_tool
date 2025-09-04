# API Status
output "api_enabled" {
  description = "Whether Speech API is enabled"
  value       = google_project_service.speech_api.service
}

output "speech_v2_enabled" {
  description = "Whether Speech v2 API is enabled"
  value       = var.enable_speech_v2
}

# Monitoring Resources
output "monitoring_dashboard_id" {
  description = "Speech API monitoring dashboard ID"
  value       = var.enable_monitoring ? google_monitoring_dashboard.speech_dashboard[0].id : ""
}

output "quota_alert_policy_id" {
  description = "Speech API quota alert policy ID"
  value       = var.enable_monitoring ? google_monitoring_alert_policy.speech_quota_alert[0].id : ""
}

output "error_alert_policy_id" {
  description = "Speech API error alert policy ID"
  value       = var.enable_monitoring ? google_monitoring_alert_policy.speech_error_alert[0].id : ""
}

# Configuration Information
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "region" {
  description = "GCP region"
  value       = var.region
}

output "project_id" {
  description = "GCP project ID"
  value       = var.project_id
}