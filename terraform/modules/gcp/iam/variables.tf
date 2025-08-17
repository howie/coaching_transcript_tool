# Core Configuration
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

# Service Accounts Configuration
variable "service_accounts" {
  description = "Additional service accounts to create"
  type = map(object({
    display_name = string
    description  = string
    roles        = list(string)
  }))
  default = {}
}

# Custom Roles Configuration
variable "roles" {
  description = "Custom IAM roles to create"
  type = map(object({
    title       = string
    description = string
    permissions = list(string)
  }))
  default = {}
}

# Workload Identity Configuration (for future GKE integration)
variable "enable_workload_identity" {
  description = "Enable Workload Identity for service accounts"
  type        = bool
  default     = false
}

variable "workload_identity_namespace" {
  description = "Kubernetes namespace for Workload Identity"
  type        = string
  default     = "default"
}

variable "workload_identity_service_account" {
  description = "Kubernetes service account name for Workload Identity"
  type        = string
  default     = "coaching-assistant"
}