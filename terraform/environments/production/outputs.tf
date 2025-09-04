# Cloudflare Outputs - re-enabled since module is active
output "frontend_url" {
  description = "Frontend URL"
  value       = module.cloudflare.frontend_url
}

output "api_url" {
  description = "API URL"
  value       = module.cloudflare.api_url
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
    environment = "production"
    app_version = var.app_version
    build_id    = var.build_id
    commit_sha  = var.commit_sha
    deploy_time = timestamp()
  }
}

# Configuration Summary
output "configuration_summary" {
  description = "Configuration summary"
  value = {
    environment     = "production"
    render_region   = var.render_region
    project_name    = var.project_name
  }
}