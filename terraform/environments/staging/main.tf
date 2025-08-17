# Configure Terraform backend
terraform {
  required_version = ">= 1.5"
  
  backend "gcs" {
    bucket = "coaching-assistant-terraform-state"
    prefix = "staging"
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
  environment = "staging"
  
  # Project Configuration
  project_name        = var.project_name
  frontend_subdomain  = "staging-${var.frontend_subdomain}"
  api_subdomain      = "staging-${var.api_subdomain}"
  
  # GitHub Configuration
  github_owner = var.github_owner
  github_repo  = var.github_repo
  
  # Render Service URLs
  render_api_url = module.render.api_service_url
  
  # Staging Environment Variables for Pages
  production_env_vars = {
    NEXT_PUBLIC_API_URL                = "https://staging-${var.api_subdomain}.${var.domain}"
    NEXT_PUBLIC_ENVIRONMENT            = "staging"
    NEXT_PUBLIC_APP_VERSION            = var.app_version
    NEXT_PUBLIC_RECAPTCHA_SITE_KEY     = var.recaptcha_site_key
    NEXT_PUBLIC_GOOGLE_CLIENT_ID       = var.google_client_id
  }
  
  preview_env_vars = {
    NEXT_PUBLIC_API_URL                = "https://dev-${var.api_subdomain}.${var.domain}"
    NEXT_PUBLIC_ENVIRONMENT            = "development"
    NEXT_PUBLIC_APP_VERSION            = var.app_version
    NEXT_PUBLIC_RECAPTCHA_SITE_KEY     = var.recaptcha_site_key
    NEXT_PUBLIC_GOOGLE_CLIENT_ID       = var.google_client_id
  }
  
  # Security Configuration (more relaxed for staging)
  enable_firewall_rules = false
  allowed_countries    = ["TW", "US", "JP", "SG", "HK"]
}

# Render Module
module "render" {
  source = "../../modules/render"
  
  # Core Configuration
  project_name     = var.project_name
  environment      = "staging"
  region          = var.render_region
  github_repo_url = var.github_repo_url
  branch          = "staging"
  auto_deploy     = true
  
  # Service Plans (Smaller for staging)
  api_plan      = "starter"
  worker_plan   = "starter"
  database_plan = "starter"
  redis_plan    = "starter"
  
  # Auto-scaling Configuration (Disabled for staging)
  enable_auto_scaling    = false
  min_instances         = 1
  max_instances         = 2
  
  # Worker Configuration
  worker_concurrency           = 2
  enable_worker_auto_scaling   = false
  worker_min_instances        = 1
  worker_max_instances        = 1
  
  # Database Configuration
  postgres_version    = "15"
  database_ha        = false
  enable_read_replica = false
  
  # Backup Configuration (Reduced for staging)
  backup_enabled        = true
  backup_retention_days = 7
  backup_hour          = 3
  backup_minute        = 0
  
  # Custom Domains
  api_custom_domains = ["staging-${var.api_subdomain}.${var.domain}"]
  
  # Environment Variables
  common_env_vars = {
    ENVIRONMENT = "staging"
    APP_VERSION = var.app_version
    BUILD_ID    = var.build_id
    COMMIT_SHA  = var.commit_sha
    SENTRY_DSN  = var.sentry_dsn
  }
  
  api_env_vars = {
    SECRET_KEY      = var.api_secret_key
    ALLOWED_ORIGINS = "https://staging-${var.frontend_subdomain}.${var.domain}"
    DEBUG          = "false"
    LOG_LEVEL      = "DEBUG"
  }
  
  worker_env_vars = {
    WORKER_CONCURRENCY = "2"
    TASK_TIME_LIMIT   = "1800"
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
  
  # reCAPTCHA (Disabled for staging)
  recaptcha_enabled   = "false"
  recaptcha_secret    = var.recaptcha_secret
  recaptcha_min_score = "0.3"
  
  # File Upload Configuration (Smaller limits)
  max_file_size      = "100"  # 100MB for staging
  max_audio_duration = "60"   # 1 hour
  
  # Monitoring
  monitoring_email = var.monitoring_email
  
  # Feature Flags
  enable_speaker_diarization = "true"
  enable_punctuation        = "true"
}

# GCP Module
module "gcp" {
  source = "../../modules/gcp"
  
  # Core Configuration
  project_id  = var.gcp_project_id
  region      = var.gcp_region
  environment = "staging"
  
  # Storage Configuration
  storage_buckets = [
    "${var.gcp_project_id}-audio-staging",
    "${var.gcp_project_id}-transcripts-staging"
  ]
  cors_origins = [
    "https://staging-${var.frontend_subdomain}.${var.domain}",
    "https://dev-${var.frontend_subdomain}.${var.domain}",
    "http://localhost:3000"
  ]
  
  # Secrets (Shared with production but different keys)
  secrets = {
    api-secret-key-staging     = var.api_secret_key
    google-client-secret-staging = var.google_client_secret
    recaptcha-secret-staging   = var.recaptcha_secret
  }
  
  # Monitoring (Reduced for staging)
  enable_monitoring = true
  notification_channels = [
    {
      type         = "email"
      display_name = "Staging Alerts"
      labels = {
        email_address = var.monitoring_email
      }
    }
  ]
  
  # Audit Logging (Disabled for staging)
  enable_audit_logs = false
  log_retention_days = 7
}