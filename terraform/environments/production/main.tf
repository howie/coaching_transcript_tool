# Configure Terraform requirements
terraform {
  required_version = ">= 1.0"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
    render = {
      source  = "render-oss/render"
      version = "~> 1.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Configure providers
provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

provider "render" {
  api_key  = var.render_api_key
  owner_id = var.render_owner_id
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Cloudflare Module - Now enabled with fixed syntax
module "cloudflare" {
  source = "../../modules/cloudflare"
  
  # Core Configuration
  zone_id     = var.cloudflare_zone_id
  account_id  = var.cloudflare_account_id
  domain      = var.domain
  environment = "production"
  
  # Project Configuration
  project_name        = var.project_name
  frontend_subdomain  = var.frontend_subdomain
  api_subdomain      = var.api_subdomain
  
  # GitHub Configuration
  github_owner = var.github_owner
  github_repo  = var.github_repo
  
  # Render Service URLs
  render_api_url = module.render.api_service_url
  
  # Workers Environment Variables (managed through Cloudflare dashboard)
  # Current Workers setup handles environment variables directly
  # No need for Terraform-managed environment variables
  
  # Security Configuration
  recaptcha_site_key = var.recaptcha_site_key
  google_client_id   = var.google_client_id
  app_version       = var.app_version
  
  # Advanced Configuration
  enable_firewall_rules = true
  allowed_countries    = ["TW", "US", "JP", "SG", "HK"]
  
  # Analytics
  web_analytics_tag   = var.web_analytics_tag
  web_analytics_token = var.web_analytics_token
}

# Render Module
module "render" {
  source = "../../modules/render"

  # Core Configuration
  project_name    = var.project_name
  environment     = "production"
  region          = var.render_region
  github_repo_url = var.github_repo_url
  branch          = "main"
  auto_deploy     = true
  api_secret_key  = var.api_secret_key

  # Service Plans (Production)
  api_plan      = "standard"
  worker_plan   = "standard"
  database_plan = "basic_1gb"  # Match existing database plan
  redis_plan    = "free"  # Match existing Redis plan

  # Auto-scaling Configuration
  enable_auto_scaling   = true
  min_instances         = 2
  max_instances         = 10
  target_cpu_percent    = 70
  target_memory_percent = 80

  # Worker Configuration
  worker_concurrency         = 4
  enable_worker_auto_scaling = true
  worker_min_instances       = 1
  worker_max_instances       = 5

  # Database Configuration
  postgres_version    = "17"
  database_name       = "coachly"
  database_user       = "coachly_user"
  database_ha         = true
  enable_read_replica = true
  replica_region      = "virginia"

  # Backup Configuration
  backup_enabled        = true
  backup_retention_days = 30
  backup_hour           = 2
  backup_minute         = 0

  # Custom Domains
  api_custom_domains = ["${var.api_subdomain}.${var.domain}"]

  # Environment Variables
  common_env_vars = {
    ENVIRONMENT = "production"
    APP_VERSION = var.app_version
    BUILD_ID    = var.build_id
    COMMIT_SHA  = var.commit_sha
    SENTRY_DSN  = var.sentry_dsn
  }

  api_env_vars = {
    SECRET_KEY      = var.api_secret_key
    ALLOWED_ORIGINS = "https://${var.frontend_subdomain}.${var.domain}"
    DEBUG           = "false"
    LOG_LEVEL       = "INFO"
  }

  worker_env_vars = {
    WORKER_CONCURRENCY = "4"
    TASK_TIME_LIMIT    = "3600"
  }

  # GCP Configuration (using variables directly since GCP module is disabled)
  gcp_project_id            = var.gcp_project_id
  gcp_service_account_json  = ""  # Empty since GCP module disabled
  audio_storage_bucket      = "${var.gcp_project_id}-audio-production"
  transcript_storage_bucket = "${var.gcp_project_id}-transcripts-production"

  # STT Configuration
  stt_provider        = var.stt_provider
  google_stt_model    = var.google_stt_model
  google_stt_location = var.google_stt_location
  assemblyai_api_key  = var.assemblyai_api_key

  # Authentication
  google_client_id     = var.google_client_id
  google_client_secret = var.google_client_secret

  # reCAPTCHA
  recaptcha_enabled   = "true"
  recaptcha_secret    = var.recaptcha_secret
  recaptcha_min_score = "0.5"

  # ECPay Configuration
  ecpay_merchant_id = var.ecpay_merchant_id
  ecpay_hash_key    = var.ecpay_hash_key
  ecpay_hash_iv     = var.ecpay_hash_iv
  ecpay_environment = var.ecpay_environment

  # Admin Security
  admin_webhook_token = var.admin_webhook_token

  # File Upload Configuration
  max_file_size      = "500" # 500MB for production
  max_audio_duration = "120" # 2 hours

  # Monitoring
  monitoring_email = var.monitoring_email

  # Feature Flags
  enable_speaker_diarization = "true"
  enable_punctuation         = "true"

  # Optional: Enable Flower monitoring
  enable_flower_monitoring = var.enable_flower_monitoring
  flower_auth              = var.flower_auth
}

# GCP Module (temporarily commented out due to provider issues)
# module "gcp" {
#   source = "../../modules/gcp"
#   
#   # Core Configuration
#   project_id  = var.gcp_project_id
#   region      = var.gcp_region
#   environment = "production"

#   # Storage Configuration
#   storage_buckets = [
#     "${var.gcp_project_id}-audio-production",
#     "${var.gcp_project_id}-transcripts-production"
#   ]
#   cors_origins = [
#     "https://${var.frontend_subdomain}.${var.domain}",
#     "https://*.${var.domain}"
#   ]
#   
#   # Service Accounts
#   service_accounts = {
#     "coaching-assistant-worker" = {
#       display_name = "Coaching Assistant Worker"
#       description  = "Service account for background workers"
#       roles = [
#         "roles/storage.objectAdmin",
#         "roles/speech.editor"
#       ]
#     }
#   }
#   
#   # Application Secrets
#   secrets = {
#     api-secret-key       = var.api_secret_key
#     database-password    = var.database_password
#     google-client-secret = var.google_client_secret
#     recaptcha-secret     = var.recaptcha_secret
#     assemblyai-api-key   = var.assemblyai_api_key
#   }
#   
#   # Monitoring
#   enable_monitoring = true
#   notification_channels = [
#     {
#       type         = "email"
#       display_name = "Production Alerts"
#       labels = {
#         email_address = var.monitoring_email
#       }
#     }
#   ]

#   # Audit Logging
#   enable_audit_logs = true
#   log_retention_days = 90
# }