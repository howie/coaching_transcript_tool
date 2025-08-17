# Main Service Account
output "main_service_account_email" {
  description = "Main service account email"
  value       = google_service_account.main.email
}

output "main_service_account_id" {
  description = "Main service account ID"
  value       = google_service_account.main.id
}

output "main_service_account_unique_id" {
  description = "Main service account unique ID"
  value       = google_service_account.main.unique_id
}

output "main_service_account_name" {
  description = "Main service account name"
  value       = google_service_account.main.name
}

# Service Account Key
output "main_service_account_key" {
  description = "Main service account private key"
  value       = google_service_account_key.main.private_key
  sensitive   = true
}

output "main_service_account_key_public" {
  description = "Main service account public key"
  value       = google_service_account_key.main.public_key
}

# Additional Service Accounts
output "service_accounts" {
  description = "Additional service accounts"
  value = {
    for k, v in google_service_account.additional : k => {
      email     = v.email
      id        = v.id
      unique_id = v.unique_id
      name      = v.name
    }
  }
}

# Custom Roles
output "custom_roles" {
  description = "Created custom roles"
  value = {
    for k, v in google_project_iam_custom_role.custom_roles : k => {
      id   = v.id
      name = v.name
    }
  }
}

# Workload Identity Information
output "workload_identity_enabled" {
  description = "Whether Workload Identity is enabled"
  value       = var.enable_workload_identity
}

# Service Account JSON (Base64 decoded for use in environment variables)
output "main_service_account_json" {
  description = "Main service account key as JSON string"
  value       = base64decode(google_service_account_key.main.private_key)
  sensitive   = true
}