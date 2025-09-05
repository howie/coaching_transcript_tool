# Configure Terraform backend
terraform {
  required_version = ">= 1.5"
  
  backend "gcs" {
    bucket = "coaching-assistant-terraform-state"
    prefix = "development"
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
  environment = "development"
  
  # Project Configuration
  project_name        = var.project_name
  frontend_subdomain  = "dev-${var.frontend_subdomain}"
  api_subdomain      = "dev-${var.api_subdomain}"
  
  # GitHub Configuration
  github_owner = var.github_owner
  github_repo  = var.github_repo
  
  # Render Service URLs
  render_api_url = module.render.api_service_url
  
  # Development Environment Variables for Pages
  production_env_vars = {
    NEXT_PUBLIC_API_URL                = "https://dev-${var.api_subdomain}.${var.domain}"
    NEXT_PUBLIC_ENVIRONMENT            = "development"
    NEXT_PUBLIC_APP_VERSION            = var.app_version
    NEXT_PUBLIC_RECAPTCHA_SITE_KEY     = ""  # Disabled for dev
    NEXT_PUBLIC_GOOGLE_CLIENT_ID       = var.google_client_id
  }
  
  preview_env_vars = {
    NEXT_PUBLIC_API_URL                = "http://localhost:8000"
    NEXT_PUBLIC_ENVIRONMENT            = "local"
    NEXT_PUBLIC_APP_VERSION            = var.app_version
    NEXT_PUBLIC_RECAPTCHA_SITE_KEY     = ""
    NEXT_PUBLIC_GOOGLE_CLIENT_ID       = var.google_client_id
  }
  
  # Security Configuration (Disabled for development)
  enable_firewall_rules = false
}

# Render Module
module "render" {
  source = "../../modules/render"
  
  # Core Configuration
  project_name     = var.project_name
  environment      = "development"
  region          = var.render_region
  github_repo_url = var.github_repo_url
  branch          = "develop"
  auto_deploy     = true
  
  # Service Plans (Minimal for development)
  api_plan      = "starter"
  worker_plan   = "starter"
  database_plan = "starter"
  redis_plan    = "starter"
  
  # Auto-scaling Configuration (Disabled)
  enable_auto_scaling    = false
  min_instances         = 1
  max_instances         = 1
  
  # Worker Configuration
  worker_concurrency           = 1
  enable_worker_auto_scaling   = false
  worker_min_instances        = 1
  worker_max_instances        = 1
  
  # Database Configuration
  postgres_version    = "15"
  database_ha        = false
  enable_read_replica = false
  
  # Backup Configuration (Minimal)
  backup_enabled        = false
  backup_retention_days = 1
  
  # Custom Domains
  api_custom_domains = ["dev-${var.api_subdomain}.${var.domain}"]
  
  # Environment Variables
  common_env_vars = {
    ENVIRONMENT = "development"
    APP_VERSION = var.app_version
    BUILD_ID    = var.build_id
    COMMIT_SHA  = var.commit_sha
  }
  
  api_env_vars = {
    SECRET_KEY      = var.api_secret_key
    ALLOWED_ORIGINS = "https://dev-${var.frontend_subdomain}.${var.domain},http://localhost:3000"
    DEBUG          = "true"
    LOG_LEVEL      = "DEBUG"
  }
  
  worker_env_vars = {
    WORKER_CONCURRENCY = "1"
    TASK_TIME_LIMIT   = "900"
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
  frontend_url         = "https://dev-${var.frontend_subdomain}.${var.domain}"
  
  # reCAPTCHA (Disabled for development)
  recaptcha_enabled   = "false"
  recaptcha_secret    = ""
  recaptcha_min_score = "0.0"
  
  # File Upload Configuration (Smallest limits)
  max_file_size      = "50"   # 50MB for development
  max_audio_duration = "30"   # 30 minutes
  
  # Monitoring (Disabled for development)
  monitoring_email = ""
  
  # Feature Flags
  enable_speaker_diarization = "true"
  enable_punctuation        = "true"
  
  # Enable Flower for development debugging
  enable_flower_monitoring = true
  flower_auth             = "dev:password"
}

# GCP Module
module "gcp" {
  source = "../../modules/gcp"
  
  # Core Configuration
  project_id  = var.gcp_project_id
  region      = var.gcp_region
  environment = "development"
  
  # Storage Configuration
  storage_buckets = [
    "${var.gcp_project_id}-audio-dev",
    "${var.gcp_project_id}-transcripts-dev"
  ]
  cors_origins = [
    "https://dev-${var.frontend_subdomain}.${var.domain}",
    "http://localhost:3000",
    "http://localhost:8000"
  ]
  
  # Secrets (Development keys)
  secrets = {
    api-secret-key-dev     = var.api_secret_key
    google-client-secret-dev = var.google_client_secret
  }
  
  # Monitoring (Disabled for development)
  enable_monitoring = false
  
  # Audit Logging (Disabled for development)
  enable_audit_logs = false
  log_retention_days = 1
}