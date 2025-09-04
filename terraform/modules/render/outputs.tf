# Service IDs
output "api_service_id" {
  description = "API service ID"
  value       = render_web_service.api.id
}

output "worker_service_id" {
  description = "Worker service ID"
  value       = render_background_worker.celery.id
}

# Flower service disabled - commented out
# output "flower_service_id" {
#   description = "Flower service ID"
#   value       = var.enable_flower_monitoring ? render_background_worker.flower[0].id : ""
# }

# Service URLs
output "api_service_url" {
  description = "API service URL"
  value       = render_web_service.api.url
}

# output "api_internal_url" {
#   description = "API internal URL"
#   value       = render_web_service.api.internal_url
# }

# Database Information
output "database_id" {
  description = "Database ID"
  value       = render_postgres.main.id
}

output "database_connection_string" {
  description = "Database connection string"
  value       = "postgresql://${render_postgres.main.database_user}:****@${render_postgres.main.id}.singapore-postgres.render.com:5432/${render_postgres.main.database_name}"
  sensitive   = true
}

# Internal connection string not available in current provider
# output "database_internal_connection_string" {
#   description = "Database internal connection string"
#   value       = render_postgres.main.internal_connection_string
#   sensitive   = true
# }

output "database_host" {
  description = "Database host"
  value       = "${render_postgres.main.id}.singapore-postgres.render.com"
}

output "database_port" {
  description = "Database port"
  value       = 5432 # Standard PostgreSQL port
}

output "database_name" {
  description = "Database name"
  value       = render_postgres.main.database_name
}

output "database_user" {
  description = "Database user"
  value       = render_postgres.main.database_user
}

# Read Replica disabled - commented out
# output "database_replica_id" {
#   description = "Database replica ID"
#   value       = var.environment == "production" && var.enable_read_replica ? render_postgres_read_replica.main_replica[0].id : ""
# }

# output "database_replica_connection_string" {
#   description = "Database replica connection string"
#   value       = var.environment == "production" && var.enable_read_replica ? render_postgres_read_replica.main_replica[0].connection_string : ""
#   sensitive   = true
# }

# Redis Information
output "redis_id" {
  description = "Redis ID"
  value       = render_redis.main.id
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = "redis://****@${render_redis.main.name}:6379"
  sensitive   = true
}

# Internal connection string not available in current provider
# output "redis_internal_connection_string" {
#   description = "Redis internal connection string"
#   value       = render_redis.main.internal_connection_string
#   sensitive   = true
# }

output "redis_host" {
  description = "Redis host"
  value       = render_redis.main.name # Using available attribute
}

output "redis_port" {
  description = "Redis port"
  value       = 6379 # Standard Redis port
}

# Custom domains not available in current provider
# output "api_custom_domains" {
#   description = "API custom domains"
#   value       = render_web_service.api.custom_domains
# }

# Auto-scaling Information
output "api_auto_scaling_enabled" {
  description = "API auto-scaling enabled"
  value       = var.enable_auto_scaling
}

output "worker_auto_scaling_enabled" {
  description = "Worker auto-scaling enabled"
  value       = var.enable_worker_auto_scaling
}

# Environment Configuration
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "region" {
  description = "Render region"
  value       = var.region
}

# Service Plans
output "api_plan" {
  description = "API service plan"
  value       = var.api_plan
}

output "worker_plan" {
  description = "Worker service plan"
  value       = var.worker_plan
}

output "database_plan" {
  description = "Database plan"
  value       = var.database_plan
}

output "redis_plan" {
  description = "Redis plan"
  value       = var.redis_plan
}

# Monitoring Configuration
output "monitoring_enabled" {
  description = "Whether monitoring is enabled"
  value       = var.monitoring_email != ""
}

# High Availability Status
output "database_ha_enabled" {
  description = "Database high availability enabled"
  value       = var.environment == "production" ? var.database_ha : false
}

output "redis_ha_enabled" {
  description = "Redis high availability enabled"
  value       = var.environment == "production" ? true : false
}

# Backup Configuration
output "backup_enabled" {
  description = "Database backup enabled"
  value       = var.backup_enabled
}

output "backup_retention_days" {
  description = "Backup retention days"
  value       = var.backup_retention_days
}

# Service status not available in current provider
# output "api_service_status" {
#   description = "API service status"
#   value       = render_web_service.api.status
# }

# output "worker_service_status" {
#   description = "Worker service status"
#   value       = render_background_worker.celery.status
# }

# output "database_status" {
#   description = "Database status"
#   value       = render_postgres.main.status
# }

# output "redis_status" {
#   description = "Redis status"
#   value       = render_redis.main.status
# }