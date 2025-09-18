# Terraform configuration for Coaching Assistant GCP resources

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Data source for the existing project
data "google_project" "project" {
  project_id = var.gcp_project_id
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset(var.required_apis)

  project = var.gcp_project_id
  service = each.value

  # Prevent accidental deletion of APIs
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Service Account for the application (import existing)
resource "google_service_account" "coaching_storage" {
  account_id   = "coaching-storage"
  display_name = "Coaching Assistant Storage Account"
  description  = "Service account for audio file storage operations"
  project      = var.gcp_project_id
}

# Service Account Key (JSON)
resource "google_service_account_key" "coaching_storage_key" {
  service_account_id = google_service_account.coaching_storage.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}

# Cloud Storage bucket for audio files
resource "google_storage_bucket" "audio_storage" {
  name          = "coaching-audio-${var.environment}-asia"
  location      = var.gcp_region
  project       = var.gcp_project_id
  force_destroy = false

  # Enable versioning
  versioning {
    enabled = true
  }

  # Lifecycle rules for GDPR compliance (auto-delete after 24 hours)
  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "Delete"
    }
  }

  # CORS configuration for frontend uploads
  cors {
    origin          = var.allowed_origins
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  # Public access prevention
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
}

# Transcript data is now stored in PostgreSQL database
# STT batch results are temporarily stored in audio bucket under batch-results/

# Production Cloud Storage bucket for audio files
resource "google_storage_bucket" "audio_storage_prod" {
  name          = "coaching-audio-prod"
  location      = var.gcp_region
  project       = var.gcp_project_id
  force_destroy = false

  # Enable versioning
  versioning {
    enabled = true
  }

  # Lifecycle rules for GDPR compliance (auto-delete after 24 hours)
  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "Delete"
    }
  }

  # CORS configuration for frontend uploads
  cors {
    origin          = var.allowed_origins
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  # Public access prevention
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
}

# Production transcript storage: Database only (no separate GCS bucket needed)