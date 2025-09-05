# Variables for GCP Terraform configuration

variable "gcp_project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "coachingassistant"
}

variable "gcp_region" {
  description = "The GCP region for resources"
  type        = string
  default     = "asia-southeast1"
}

variable "environment" {
  description = "The environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "frontend_url" {
  description = "Frontend URL for OAuth redirects"
  type        = string
  default     = "https://coachly.doxa.com.tw"
}

variable "required_apis" {
  description = "List of required Google Cloud APIs"
  type        = list(string)
  default = [
    "speech.googleapis.com",           # Speech-to-Text API v2
    "storage-api.googleapis.com",      # Cloud Storage API
    "storage-component.googleapis.com", # Cloud Storage JSON API
    "iam.googleapis.com",              # IAM API
    "cloudresourcemanager.googleapis.com", # Cloud Resource Manager API
    "serviceusage.googleapis.com"      # Service Usage API
  ]
}

variable "allowed_origins" {
  description = "Allowed CORS origins for storage buckets"
  type        = list(string)
  default = [
    "https://coachly.doxa.com.tw",                 # Production frontend (new domain)
    "https://coaching-transcript-tool.pages.dev",  # Production frontend (legacy)
    "https://*.pages.dev",                         # Cloudflare Pages preview
    "https://*.doxa.com.tw",                       # Doxa domain wildcards
    "http://localhost:3000",                       # Local development
    "https://localhost:3000"                       # Local development (HTTPS)
  ]
}

variable "service_account_roles" {
  description = "IAM roles to assign to the service account"
  type        = list(string)
  default = [
    "roles/speech.client",            # Speech-to-Text Client (correct role)  
    "roles/storage.objectAdmin"       # Cloud Storage Object Admin
    # Note: legacy permissions are assigned at bucket level, not project level
  ]
}

variable "enable_cloud_functions" {
  description = "Enable Cloud Functions API"
  type        = bool
  default     = false
}

variable "enable_pubsub" {
  description = "Enable Pub/Sub API and create topics"
  type        = bool
  default     = false
}

variable "enable_scheduler" {
  description = "Enable Cloud Scheduler API and create cleanup jobs"
  type        = bool
  default     = false
}