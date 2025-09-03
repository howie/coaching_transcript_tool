# Provider Credentials
variable "cloudflare_api_token" {
  description = "Cloudflare API token"
  type        = string
  sensitive   = true
}

variable "render_api_key" {
  description = "Render API key"
  type        = string
  sensitive   = true
}

variable "render_owner_id" {
  description = "Render owner ID (username)"
  type        = string
}

# Cloudflare Configuration
variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID"
  type        = string
}

variable "cloudflare_account_id" {
  description = "Cloudflare Account ID"
  type        = string
}

variable "domain" {
  description = "Base domain name"
  type        = string
  default     = "doxa.com.tw"
}

variable "frontend_subdomain" {
  description = "Frontend subdomain"
  type        = string
  default     = "coachly"
}

variable "api_subdomain" {
  description = "API subdomain"
  type        = string
  default     = "api"
}

# Project Configuration
variable "project_name" {
  description = "Project name"
  type        = string
  default     = "coaching-assistant"
}

variable "app_version" {
  description = "Application version"
  type        = string
  default     = "1.0.0"
}

variable "build_id" {
  description = "Build ID"
  type        = string
  default     = ""
}

variable "commit_sha" {
  description = "Git commit SHA"
  type        = string
  default     = ""
}

# GitHub Configuration
variable "github_owner" {
  description = "GitHub repository owner"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}

variable "github_repo_url" {
  description = "GitHub repository URL"
  type        = string
}

# GCP Configuration
variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "asia-southeast1"
}

# Render Configuration
variable "render_region" {
  description = "Render region"
  type        = string
  default     = "oregon"
}

# Application Secrets
variable "api_secret_key" {
  description = "API secret key"
  type        = string
  sensitive   = true
}

variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true
  default     = ""
}

# Google OAuth Configuration
variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth client secret"
  type        = string
  sensitive   = true
}

variable "google_client_id_staging" {
  description = "Google OAuth client ID for staging"
  type        = string
  sensitive   = true
}

# reCAPTCHA Configuration
variable "recaptcha_site_key" {
  description = "reCAPTCHA site key for production"
  type        = string
  sensitive   = true
}

variable "recaptcha_site_key_staging" {
  description = "reCAPTCHA site key for staging"
  type        = string
  sensitive   = true
}

variable "recaptcha_secret" {
  description = "reCAPTCHA secret key"
  type        = string
  sensitive   = true
}

# STT Configuration
variable "stt_provider" {
  description = "Speech-to-Text provider"
  type        = string
  default     = "google"
}

variable "google_stt_model" {
  description = "Google STT model"
  type        = string
  default     = "chirp_2"
}

variable "google_stt_location" {
  description = "Google STT location"
  type        = string
  default     = "asia-southeast1"
}

variable "assemblyai_api_key" {
  description = "AssemblyAI API key"
  type        = string
  sensitive   = true
  default     = ""
}

# Analytics Configuration
variable "web_analytics_tag" {
  description = "Web Analytics tag"
  type        = string
  default     = ""
}

variable "web_analytics_token" {
  description = "Web Analytics token"
  type        = string
  sensitive   = true
  default     = ""
}

# Monitoring Configuration
variable "monitoring_email" {
  description = "Email for monitoring alerts"
  type        = string
}

variable "sentry_dsn" {
  description = "Sentry DSN for error tracking"
  type        = string
  sensitive   = true
  default     = ""
}

# Feature Flags
variable "enable_flower_monitoring" {
  description = "Enable Flower monitoring for Celery"
  type        = bool
  default     = false
}

variable "flower_auth" {
  description = "Flower basic auth (username:password)"
  type        = string
  sensitive   = true
  default     = ""
}

# ECPay Configuration
variable "ecpay_merchant_id" {
  description = "ECPay merchant ID"
  type        = string
  sensitive   = true
}

variable "ecpay_hash_key" {
  description = "ECPay hash key"
  type        = string
  sensitive   = true
}

variable "ecpay_hash_iv" {
  description = "ECPay hash IV"
  type        = string
  sensitive   = true
}

variable "ecpay_environment" {
  description = "ECPay environment (sandbox, production)"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["sandbox", "production"], var.ecpay_environment)
    error_message = "ECPay environment must be sandbox or production."
  }
}

variable "admin_webhook_token" {
  description = "Admin webhook token for secure management endpoints"
  type        = string
  sensitive   = true
}

# API Server Configuration
variable "database_url" {
  description = "PostgreSQL database URL"
  type        = string
  sensitive   = true
}

variable "redis_url" {
  description = "Redis connection URL"
  type        = string
  sensitive   = true
}

variable "audio_storage_bucket" {
  description = "GCS bucket for audio file storage"
  type        = string
}

variable "transcript_storage_bucket" {
  description = "GCS bucket for transcript storage"
  type        = string
}

variable "google_application_credentials_json" {
  description = "Google Cloud service account credentials in JSON format (base64 encoded)"
  type        = string
  sensitive   = true
}