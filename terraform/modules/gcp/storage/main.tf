# Storage buckets for different purposes
resource "google_storage_bucket" "buckets" {
  for_each = toset(var.buckets)
  
  name          = each.value
  project       = var.project_id
  location      = var.region
  force_destroy = var.environment != "production"
  
  # Lifecycle management
  lifecycle_rule {
    condition {
      age = var.lifecycle_delete_age
    }
    action {
      type = "Delete"
    }
  }
  
  # Versioning
  versioning {
    enabled = var.enable_versioning
  }
  
  # CORS configuration for frontend access
  cors {
    origin          = var.cors_origins
    method          = ["GET", "POST", "PUT", "DELETE"]
    response_header = ["Content-Type", "Access-Control-Allow-Origin"]
    max_age_seconds = 3600
  }
  
  # Uniform bucket-level access
  uniform_bucket_level_access = true
  
  # Labels
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    purpose     = each.value
  }
}

# Specific buckets for audio and transcripts
resource "google_storage_bucket" "audio" {
  name          = "${var.project_id}-audio-${var.environment}"
  project       = var.project_id
  location      = var.region
  force_destroy = var.environment != "production"
  
  # Audio files should be deleted after processing
  lifecycle_rule {
    condition {
      age = 1  # 1 day
    }
    action {
      type = "Delete"
    }
  }
  
  # Versioning not needed for temporary audio files
  versioning {
    enabled = false
  }
  
  # CORS for upload functionality
  cors {
    origin          = var.cors_origins
    method          = ["GET", "POST", "PUT"]
    response_header = ["Content-Type", "Access-Control-Allow-Origin"]
    max_age_seconds = 3600
  }
  
  uniform_bucket_level_access = true
  
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    purpose     = "audio-storage"
  }
}

resource "google_storage_bucket" "transcripts" {
  name          = "${var.project_id}-transcripts-${var.environment}"
  project       = var.project_id
  location      = var.region
  force_destroy = var.environment != "production"
  
  # Transcripts have longer retention
  lifecycle_rule {
    condition {
      age = var.transcript_retention_days
    }
    action {
      type = "Delete"
    }
  }
  
  # Enable versioning for transcripts
  versioning {
    enabled = true
  }
  
  # CORS for download functionality
  cors {
    origin          = var.cors_origins
    method          = ["GET"]
    response_header = ["Content-Type"]
    max_age_seconds = 3600
  }
  
  uniform_bucket_level_access = true
  
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    purpose     = "transcript-storage"
  }
}

# Audit logs bucket (if audit logging is enabled)
resource "google_storage_bucket" "audit_logs" {
  name          = "${var.project_id}-audit-logs-${var.environment}"
  project       = var.project_id
  location      = var.region
  force_destroy = var.environment != "production"
  
  # Audit logs retention
  lifecycle_rule {
    condition {
      age = var.audit_log_retention_days
    }
    action {
      type = "Delete"
    }
  }
  
  # Versioning for audit logs
  versioning {
    enabled = true
  }
  
  uniform_bucket_level_access = true
  
  labels = {
    environment = var.environment
    managed_by  = "terraform"
    purpose     = "audit-logs"
  }
}

# IAM bindings for service accounts
resource "google_storage_bucket_iam_member" "audio_access" {
  bucket = google_storage_bucket.audio.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.service_account_email}"
}

resource "google_storage_bucket_iam_member" "transcript_access" {
  bucket = google_storage_bucket.transcripts.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.service_account_email}"
}