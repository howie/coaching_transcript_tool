# Main service account for the application
resource "google_service_account" "main" {
  account_id   = "coaching-assistant-${var.environment}"
  display_name = "Coaching Assistant Service Account - ${title(var.environment)}"
  description  = "Service account for Coaching Assistant application in ${var.environment} environment"
  project      = var.project_id
}

# Service account key
resource "google_service_account_key" "main" {
  service_account_id = google_service_account.main.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}

# Additional service accounts based on configuration
resource "google_service_account" "additional" {
  for_each = var.service_accounts
  
  account_id   = each.key
  display_name = each.value.display_name
  description  = each.value.description
  project      = var.project_id
}

# Custom roles
resource "google_project_iam_custom_role" "custom_roles" {
  for_each = var.roles
  
  role_id     = each.key
  title       = each.value.title
  description = each.value.description
  permissions = each.value.permissions
  project     = var.project_id
}

# IAM bindings for main service account
resource "google_project_iam_member" "main_service_account_roles" {
  for_each = toset([
    "roles/storage.objectAdmin",
    "roles/speech.editor",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.main.email}"
}

# IAM bindings for additional service accounts
resource "google_project_iam_member" "additional_service_account_roles" {
  for_each = {
    for pair in flatten([
      for sa_key, sa_config in var.service_accounts : [
        for role in sa_config.roles : {
          sa_key = sa_key
          role   = role
        }
      ]
    ]) : "${pair.sa_key}-${pair.role}" => pair
  }
  
  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.additional[each.value.sa_key].email}"
}

# Workload Identity bindings (for GKE if needed in future)
resource "google_service_account_iam_member" "workload_identity" {
  count = var.enable_workload_identity ? 1 : 0
  
  service_account_id = google_service_account.main.name
  role              = "roles/iam.workloadIdentityUser"
  member            = "serviceAccount:${var.project_id}.svc.id.goog[${var.workload_identity_namespace}/${var.workload_identity_service_account}]"
}

# IAM policy for storage bucket access
data "google_iam_policy" "storage_policy" {
  binding {
    role = "roles/storage.objectAdmin"
    members = [
      "serviceAccount:${google_service_account.main.email}",
    ]
  }
  
  binding {
    role = "roles/storage.legacyBucketReader"
    members = [
      "serviceAccount:${google_service_account.main.email}",
    ]
  }
}

# Conditional IAM bindings for production
resource "google_project_iam_member" "production_roles" {
  for_each = var.environment == "production" ? toset([
    "roles/cloudsql.client",
    "roles/redis.editor"
  ]) : toset([])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.main.email}"
}