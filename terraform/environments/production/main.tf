# Configure Terraform backend
terraform {
  required_version = ">= 1.5"
  
  backend "gcs" {
    bucket = "coaching-assistant-terraform-state"
    prefix = "production"
  }
  
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
  api_key = var.render_api_key
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Cloudflare Module
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
  
  # Production Environment Variables for Pages
  production_env_vars = {
    NEXT_PUBLIC_API_URL                = "https://${var.api_subdomain}.${var.domain}"
    NEXT_PUBLIC_ENVIRONMENT            = "production"
    NEXT_PUBLIC_APP_VERSION            = var.app_version
    NEXT_PUBLIC_RECAPTCHA_SITE_KEY     = var.recaptcha_site_key
    NEXT_PUBLIC_GOOGLE_CLIENT_ID       = var.google_client_id
  }
  
  preview_env_vars = {
    NEXT_PUBLIC_API_URL                = "https://staging-${var.api_subdomain}.${var.domain}"
    NEXT_PUBLIC_ENVIRONMENT            = "staging"
    NEXT_PUBLIC_APP_VERSION            = var.app_version
    NEXT_PUBLIC_RECAPTCHA_SITE_KEY     = var.recaptcha_site_key_staging
    NEXT_PUBLIC_GOOGLE_CLIENT_ID       = var.google_client_id_staging
  }
  
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
  project_name     = var.project_name
  environment      = "production"
  region          = var.render_region
  github_repo_url = var.github_repo_url
  branch          = "main"
  auto_deploy     = true
  
  # Service Plans (Production)
  api_plan      = "standard"
  worker_plan   = "standard"
  database_plan = "standard"
  redis_plan    = "standard"
  
  # Auto-scaling Configuration
  enable_auto_scaling    = true
  min_instances         = 2
  max_instances         = 10
  target_cpu_percent    = 70
  target_memory_percent = 80
  
  # Worker Configuration
  worker_concurrency           = 4
  enable_worker_auto_scaling   = true
  worker_min_instances        = 1
  worker_max_instances        = 5
  
  # Database Configuration
  postgres_version    = "15"
  database_ha        = true
  enable_read_replica = true
  replica_region     = "virginia"
  
  # Backup Configuration
  backup_enabled        = true
  backup_retention_days = 30
  backup_hour          = 2
  backup_minute        = 0
  
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
    DEBUG          = "false"
    LOG_LEVEL      = "INFO"
  }
  
  worker_env_vars = {
    WORKER_CONCURRENCY = "4"
    TASK_TIME_LIMIT   = "3600"
  }
  
  # GCP Configuration
  gcp_project_id           = var.gcp_project_id
  gcp_service_account_json = module.gcp.main_service_account_json
  audio_storage_bucket     = module.gcp.audio_bucket_name
  transcript_storage_bucket = module.gcp.transcript_bucket_name
  
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
  
  # File Upload Configuration
  max_file_size      = "500"  # 500MB for production
  max_audio_duration = "120"   # 2 hours
  
  # Monitoring
  monitoring_email = var.monitoring_email
  
  # Feature Flags
  enable_speaker_diarization = "true"
  enable_punctuation        = "true"
  
  # Optional: Enable Flower monitoring
  enable_flower_monitoring = var.enable_flower_monitoring
  flower_auth             = var.flower_auth
}

# GCP Module
module "gcp" {
  source = "../../modules/gcp"
  
  # Core Configuration
  project_id  = var.gcp_project_id
  region      = var.gcp_region
  environment = "production"
  
  # Storage Configuration
  storage_buckets = [
    "${var.gcp_project_id}-audio-production",
    "${var.gcp_project_id}-transcripts-production"
  ]
  cors_origins = [
    "https://${var.frontend_subdomain}.${var.domain}",
    "https://*.${var.domain}"
  ]
  
  # Service Accounts
  service_accounts = {
    "coaching-assistant-worker" = {
      display_name = "Coaching Assistant Worker"
      description  = "Service account for background workers"
      roles = [
        "roles/storage.objectAdmin",
        "roles/speech.editor"
      ]
    }
  }
  
  # Secrets
  secrets = {
    api-secret-key     = var.api_secret_key
    database-password  = var.database_password
    google-client-secret = var.google_client_secret
    recaptcha-secret   = var.recaptcha_secret
    assemblyai-api-key = var.assemblyai_api_key
  }
  
  # Monitoring
  enable_monitoring = true
  notification_channels = [
    {
      type         = "email"
      display_name = "Production Alerts"
      labels = {
        email_address = var.monitoring_email
      }
    }
  ]
  
  # Audit Logging
  enable_audit_logs = true
  log_retention_days = 90
}