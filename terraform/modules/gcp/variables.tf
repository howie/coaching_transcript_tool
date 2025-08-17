# Core Configuration
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "asia-southeast1"
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

# Storage Configuration
variable "storage_buckets" {
  description = "List of storage bucket names to create"
  type        = list(string)
  default     = []
}

variable "cors_origins" {
  description = "CORS allowed origins for storage buckets"
  type        = list(string)
  default     = []
}

# IAM Configuration
variable "service_accounts" {
  description = "Service accounts to create"
  type = map(object({
    display_name = string
    description  = string
    roles        = list(string)
  }))
  default = {}
}

variable "iam_roles" {
  description = "Custom IAM roles to create"
  type = map(object({
    title       = string
    description = string
    permissions = list(string)
  }))
  default = {}
}

# Speech-to-Text Configuration
variable "enable_speech_v2" {
  description = "Enable Speech-to-Text v2 API"
  type        = bool
  default     = true
}

# Secret Manager Configuration
variable "secrets" {
  description = "Secrets to store in Secret Manager"
  type        = map(string)
  default     = {}
  sensitive   = true
}

# Logging Configuration
variable "enable_audit_logs" {
  description = "Enable audit logs"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Log retention period in days"
  type        = number
  default     = 30
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Enable Cloud Monitoring"
  type        = bool
  default     = true
}

variable "notification_channels" {
  description = "Notification channels for alerts"
  type = list(object({
    type         = string
    display_name = string
    labels       = map(string)
  }))
  default = []
}