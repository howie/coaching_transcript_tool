# Core Configuration
variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "coaching-assistant"
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "region" {
  description = "Render region"
  type        = string
  default     = "oregon"
}

# Repository Configuration
variable "github_repo_url" {
  description = "GitHub repository URL"
  type        = string
}

variable "branch" {
  description = "Git branch to deploy"
  type        = string
  default     = "main"
}

variable "auto_deploy" {
  description = "Enable auto-deploy on git push"
  type        = bool
  default     = true
}

# Service Plans
variable "api_plan" {
  description = "API service plan"
  type        = string
  default     = "standard"
}

variable "worker_plan" {
  description = "Worker service plan"
  type        = string
  default     = "standard"
}

variable "database_plan" {
  description = "Database plan"
  type        = string
  default     = "standard"
}

variable "redis_plan" {
  description = "Redis plan"
  type        = string
  default     = "standard"
}

# Instance Configuration
variable "api_instances" {
  description = "Number of API instances"
  type        = number
  default     = 1
}

# Auto-scaling Configuration
variable "enable_auto_scaling" {
  description = "Enable auto-scaling for API service"
  type        = bool
  default     = true
}

variable "min_instances" {
  description = "Minimum number of API instances"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum number of API instances"
  type        = number
  default     = 5
}

variable "target_cpu_percent" {
  description = "Target CPU percentage for auto-scaling"
  type        = number
  default     = 70
}

variable "target_memory_percent" {
  description = "Target memory percentage for auto-scaling"
  type        = number
  default     = 80
}

# Worker Configuration
variable "worker_concurrency" {
  description = "Worker concurrency level"
  type        = number
  default     = 4
}

variable "task_time_limit" {
  description = "Task time limit in seconds"
  type        = number
  default     = 3600
}

variable "enable_worker_auto_scaling" {
  description = "Enable auto-scaling for worker service"
  type        = bool
  default     = false
}

variable "worker_min_instances" {
  description = "Minimum number of worker instances"
  type        = number
  default     = 1
}

variable "worker_max_instances" {
  description = "Maximum number of worker instances"
  type        = number
  default     = 3
}

variable "worker_target_cpu_percent" {
  description = "Target CPU percentage for worker auto-scaling"
  type        = number
  default     = 80
}

variable "worker_target_memory_percent" {
  description = "Target memory percentage for worker auto-scaling"
  type        = number
  default     = 85
}

# Database Configuration
variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15"
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "coaching_assistant"
}

variable "database_user" {
  description = "Database user"
  type        = string
  default     = "coaching_user"
}

variable "database_ha" {
  description = "Enable high availability for database"
  type        = bool
  default     = false
}

# Backup Configuration
variable "backup_enabled" {
  description = "Enable database backups"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Backup retention in days"
  type        = number
  default     = 7
}

variable "backup_hour" {
  description = "Backup hour (0-23)"
  type        = number
  default     = 2
}

variable "backup_minute" {
  description = "Backup minute (0-59)"
  type        = number
  default     = 0
}

variable "redis_backup_retention_days" {
  description = "Redis backup retention in days"
  type        = number
  default     = 3
}

# Maintenance Configuration
variable "maintenance_day" {
  description = "Maintenance day of week"
  type        = string
  default     = "sunday"
}

variable "maintenance_time" {
  description = "Maintenance time (HH:MM)"
  type        = string
  default     = "02:00"
}

variable "maintenance_duration" {
  description = "Maintenance duration"
  type        = string
  default     = "1h"
}

# Read Replica Configuration
variable "enable_read_replica" {
  description = "Enable database read replica (production only)"
  type        = bool
  default     = false
}

variable "replica_region" {
  description = "Read replica region"
  type        = string
  default     = "virginia"
}

# Custom Domains
variable "api_custom_domains" {
  description = "Custom domains for API service"
  type        = list(string)
  default     = []
}

# Environment Variables
variable "common_env_vars" {
  description = "Common environment variables for all services"
  type        = map(string)
  default     = {}
}

variable "api_env_vars" {
  description = "API-specific environment variables"
  type        = map(string)
  default     = {}
}

variable "worker_env_vars" {
  description = "Worker-specific environment variables"
  type        = map(string)
  default     = {}
}

# Secrets
variable "secret_files" {
  description = "Secret files to mount"
  type        = list(object({
    name    = string
    content = string
  }))
  default   = []
  sensitive = true
}

# Application Configuration
variable "api_secret_key" {
  description = "API secret key"
  type        = string
  sensitive   = true
}

variable "allowed_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = []
}

# GCP Configuration
variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_service_account_json" {
  description = "GCP service account JSON"
  type        = string
  sensitive   = true
}

variable "audio_storage_bucket" {
  description = "Audio storage bucket name"
  type        = string
}

variable "transcript_storage_bucket" {
  description = "Transcript storage bucket name"
  type        = string
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
  default     = ""
  sensitive   = true
}

# Authentication
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

# reCAPTCHA
variable "recaptcha_enabled" {
  description = "Enable reCAPTCHA"
  type        = string
  default     = "true"
}

variable "recaptcha_secret" {
  description = "reCAPTCHA secret key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "recaptcha_min_score" {
  description = "reCAPTCHA minimum score"
  type        = string
  default     = "0.5"
}

# File Upload Configuration
variable "max_file_size" {
  description = "Maximum file size in MB"
  type        = string
  default     = "200"
}

variable "max_audio_duration" {
  description = "Maximum audio duration in minutes"
  type        = string
  default     = "120"
}

# Logging
variable "log_level" {
  description = "Logging level"
  type        = string
  default     = "INFO"
}

# Monitoring Configuration
variable "monitoring_email" {
  description = "Email for monitoring alerts"
  type        = string
  default     = ""
}

# Feature Flags
variable "enable_speaker_diarization" {
  description = "Enable speaker diarization"
  type        = string
  default     = "true"
}

variable "enable_punctuation" {
  description = "Enable punctuation"
  type        = string
  default     = "true"
}

# Flower Monitoring
variable "enable_flower_monitoring" {
  description = "Enable Flower monitoring for Celery"
  type        = bool
  default     = false
}

variable "flower_auth" {
  description = "Flower basic auth (username:password)"
  type        = string
  default     = ""
  sensitive   = true
}

# Version Information
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

# External Services
variable "sentry_dsn" {
  description = "Sentry DSN for error tracking"
  type        = string
  default     = ""
  sensitive   = true
}