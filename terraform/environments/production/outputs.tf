# Cloudflare Outputs
output "frontend_url" {
  description = "Frontend URL"
  value       = module.cloudflare.frontend_url
}

output "api_url" {
  description = "API URL"
  value       = module.cloudflare.api_url
}

output "pages_project_name" {
  description = "Cloudflare Pages project name"
  value       = module.cloudflare.pages_project_name
}

# Render Outputs
output "api_service_id" {
  description = "Render API service ID"
  value       = module.render.api_service_id
}

output "api_service_url" {
  description = "Render API service URL"
  value       = module.render.api_service_url
}

output "worker_service_id" {
  description = "Render worker service ID"
  value       = module.render.worker_service_id
}

output "database_host" {
  description = "Database host"
  value       = module.render.database_host
}

output "database_name" {
  description = "Database name"
  value       = module.render.database_name
}

output "redis_host" {
  description = "Redis host"
  value       = module.render.redis_host
}

# GCP Outputs
output "gcp_project_id" {
  description = "GCP project ID"
  value       = module.gcp.project_id
}

output "audio_bucket_name" {
  description = "Audio storage bucket name"
  value       = module.gcp.audio_bucket_name
}

output "transcript_bucket_name" {
  description = "Transcript storage bucket name"
  value       = module.gcp.transcript_bucket_name
}

output "service_account_email" {
  description = "Main service account email"
  value       = module.gcp.main_service_account_email
}

# Environment Information
output "environment" {
  description = "Environment name"
  value       = "production"
}

output "region_gcp" {
  description = "GCP region"
  value       = var.gcp_region
}

output "region_render" {
  description = "Render region"
  value       = var.render_region
}

# Deployment Information
output "deployment_info" {
  description = "Deployment information"
  value = {
    environment    = "production"
    app_version   = var.app_version
    build_id      = var.build_id
    commit_sha    = var.commit_sha
    deploy_time   = timestamp()
  }
}

# Service Status
output "service_status" {
  description = "Service status information"
  value = {
    api_status      = module.render.api_service_status
    worker_status   = module.render.worker_service_status
    database_status = module.render.database_status
    redis_status    = module.render.redis_status
  }
}

# Configuration Summary
output "configuration_summary" {
  description = "Configuration summary"
  value = {
    auto_scaling_enabled     = module.render.api_auto_scaling_enabled
    database_ha_enabled     = module.render.database_ha_enabled
    backup_enabled          = module.render.backup_enabled
    monitoring_enabled      = module.render.monitoring_enabled
    firewall_rules_enabled  = module.cloudflare.firewall_rules_enabled
    audit_logs_enabled      = module.gcp.audit_logs_enabled
  }
}