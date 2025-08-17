variable "billing_account" {
  description = "The ID of the billing account to associate projects with"
  type        = string
  default     = "<please enter your billing account number here>"
}

variable "org_id" {
  description = "The organization id for the associated resources"
  type        = string
  default     = "682717358496"
}

variable "billing_project" {
  description = "The project id to use for billing"
  type        = string
  default     = "CLOUD_SETUP_HOST_PROJECT_ID"
}

variable "folders" {
  description = "Folder structure as a map"
  type        = map
}

variable "application_enabled_folder_paths" {
  description = "The folder paths to enable resource manager capability"
  type        = list
}
