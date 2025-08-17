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
  description = "Environment name"
  type        = string
  default     = "production"
}

# Speech API Configuration
variable "enable_speech_v2" {
  description = "Enable Speech-to-Text v2 API"
  type        = bool
  default     = true
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Enable monitoring dashboards and alerts"
  type        = bool
  default     = true
}

variable "notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}

# Custom Phrase Sets (for future use)
variable "custom_phrases" {
  description = "Custom phrases to improve recognition accuracy"
  type = list(object({
    value = string
    boost = number
  }))
  default = [
    {
      value = "coaching session"
      boost = 10.0
    },
    {
      value = "client goals"
      boost = 10.0
    },
    {
      value = "action items"
      boost = 10.0
    }
  ]
}