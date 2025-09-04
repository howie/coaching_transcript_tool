# Core Configuration
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

# Bucket Configuration
variable "buckets" {
  description = "List of bucket names to create"
  type        = list(string)
  default     = []
}

variable "cors_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = []
}

# Lifecycle Configuration
variable "lifecycle_delete_age" {
  description = "Age in days after which objects are deleted"
  type        = number
  default     = 30
}

variable "transcript_retention_days" {
  description = "Transcript retention period in days"
  type        = number
  default     = 365
}

variable "audit_log_retention_days" {
  description = "Audit log retention period in days"
  type        = number
  default     = 90
}

# Versioning Configuration
variable "enable_versioning" {
  description = "Enable versioning for buckets"
  type        = bool
  default     = true
}

# Service Account
variable "service_account_email" {
  description = "Service account email for bucket access"
  type        = string
  default     = ""
}