# IAM configuration for Coaching Assistant GCP resources

# IAM bindings for the service account
resource "google_project_iam_member" "coaching_storage_roles" {
  for_each = toset(var.service_account_roles)
  
  project = var.gcp_project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.coaching_storage.email}"
  
  depends_on = [google_service_account.coaching_storage]
}

# Storage bucket IAM for the service account
resource "google_storage_bucket_iam_member" "audio_storage_admin" {
  bucket = google_storage_bucket.audio_storage.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.coaching_storage.email}"
}

resource "google_storage_bucket_iam_member" "transcript_storage_admin" {
  bucket = google_storage_bucket.transcript_storage.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.coaching_storage.email}"
}

# Additional IAM binding for signed URL generation
resource "google_storage_bucket_iam_member" "audio_storage_legacy_owner" {
  bucket = google_storage_bucket.audio_storage.name
  role   = "roles/storage.legacyObjectOwner"
  member = "serviceAccount:${google_service_account.coaching_storage.email}"
}

# Custom IAM role for Speech-to-Text v2 specific permissions (optional)
resource "google_project_iam_custom_role" "speech_v2_user" {
  role_id     = "speechV2User"
  title       = "Custom Speech-to-Text v2 User"
  description = "Custom role for Speech-to-Text v2 API with minimal required permissions"
  project     = var.gcp_project_id
  
  permissions = [
    "speech.recognizers.recognize",
    "speech.recognizers.get",
    "speech.recognizers.list",
    "speech.operations.get",
    "speech.operations.list"
  ]
}

# Bind custom role to service account (alternative to roles/speech.user)
# Uncomment if you want to use the custom role instead of the built-in role
# resource "google_project_iam_member" "coaching_storage_custom_speech" {
#   project = var.gcp_project_id
#   role    = google_project_iam_custom_role.speech_v2_user.name
#   member  = "serviceAccount:${google_service_account.coaching_storage.email}"
#   
#   depends_on = [
#     google_service_account.coaching_storage,
#     google_project_iam_custom_role.speech_v2_user
#   ]
# }

# IAM policy for the project (for reference and documentation)
data "google_iam_policy" "project_policy" {
  # Speech-to-Text service access
  binding {
    role = "roles/speech.client"
    members = [
      "serviceAccount:${google_service_account.coaching_storage.email}"
    ]
  }
  
  # Storage access
  binding {
    role = "roles/storage.objectAdmin"
    members = [
      "serviceAccount:${google_service_account.coaching_storage.email}"
    ]
  }
  
  # Legacy object owner for signed URLs
  binding {
    role = "roles/storage.legacyObjectOwner"
    members = [
      "serviceAccount:${google_service_account.coaching_storage.email}"
    ]
  }
}

# Security: Condition-based IAM (example for future enhancement)
# This shows how to add conditions to IAM bindings for enhanced security
resource "google_project_iam_binding" "conditional_speech_access" {
  project = var.gcp_project_id
  role    = "roles/speech.client"
  members = [
    "serviceAccount:${google_service_account.coaching_storage.email}"
  ]

  # Example condition: restrict access by request time (optional)
  condition {
    title       = "Business Hours Access"
    description = "Allow Speech-to-Text access only during business hours"
    expression  = "request.time.getHours() >= 6 && request.time.getHours() <= 22"
  }
  
  # Note: This is commented out as it might be too restrictive for async processing
  count = 0  # Set to 1 to enable conditional access
}