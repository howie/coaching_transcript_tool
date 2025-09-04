# Core Configuration
variable "zone_id" {
  description = "Cloudflare Zone ID"
  type        = string
}

variable "account_id" {
  description = "Cloudflare Account ID"
  type        = string
}

variable "domain" {
  description = "Base domain name"
  type        = string
  default     = "doxa.com.tw"
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

# Project Configuration
variable "project_name" {
  description = "Project name"
  type        = string
  default     = "coaching-assistant"
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

# GitHub Configuration
variable "github_owner" {
  description = "GitHub repository owner"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}

variable "production_branch" {
  description = "Production branch name"
  type        = string
  default     = "main"
}

# Render Service URLs
variable "render_api_url" {
  description = "Render API service URL"
  type        = string
}

# MX Records Configuration
variable "mx_records" {
  description = "MX records configuration"
  type = map(object({
    server   = string
    priority = number
  }))
  default = {}
}

# Analytics
variable "web_analytics_tag" {
  description = "Web Analytics tag"
  type        = string
  default     = ""
}

variable "web_analytics_token" {
  description = "Web Analytics token"
  type        = string
  default     = ""
  sensitive   = true
}

# Workers Configuration (managed externally)
# Workers environment variables and routes are managed through Cloudflare dashboard
# This module focuses on DNS records and zone-level settings

# Security Configuration
variable "recaptcha_site_key" {
  description = "reCAPTCHA site key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "app_version" {
  description = "Application version"
  type        = string
  default     = "1.0.0"
}

# Advanced Configuration
variable "proxied" {
  description = "Whether DNS records should be proxied through Cloudflare"
  type        = bool
  default     = true
}

variable "enable_firewall_rules" {
  description = "Enable custom firewall rules"
  type        = bool
  default     = true
}

variable "allowed_countries" {
  description = "List of allowed country codes for API access"
  type        = list(string)
  default     = ["TW", "US", "JP", "SG", "HK"]
}