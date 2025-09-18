# GCP Services and API configurations

# Speech-to-Text API v2 configuration
# Note: Speech-to-Text v2 doesn't require explicit recognizer resources for basic usage
# The service account permissions are sufficient for most use cases


# Monitoring and logging configuration
resource "google_project_service" "logging" {
  project = var.gcp_project_id
  service = "logging.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false
}

resource "google_project_service" "monitoring" {
  project = var.gcp_project_id
  service = "monitoring.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Cloud Functions API (if needed for serverless processing)
resource "google_project_service" "cloudfunctions" {
  project = var.gcp_project_id
  service = "cloudfunctions.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false

  count = var.enable_cloud_functions ? 1 : 0
}

# Cloud Pub/Sub (if needed for async processing)
resource "google_project_service" "pubsub" {
  project = var.gcp_project_id
  service = "pubsub.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false

  count = var.enable_pubsub ? 1 : 0
}

# Optional: Pub/Sub topics for async processing
resource "google_pubsub_topic" "transcription_tasks" {
  name    = "transcription-tasks"
  project = var.gcp_project_id

  count = var.enable_pubsub ? 1 : 0

  depends_on = [google_project_service.pubsub]
}

resource "google_pubsub_topic" "transcription_results" {
  name    = "transcription-results"
  project = var.gcp_project_id

  count = var.enable_pubsub ? 1 : 0

  depends_on = [google_project_service.pubsub]
}

# Cloud Scheduler (if needed for cleanup jobs)
resource "google_project_service" "cloudscheduler" {
  project = var.gcp_project_id
  service = "cloudscheduler.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false

  count = var.enable_scheduler ? 1 : 0
}

# Optional: Scheduled job for cleaning up old audio files (GDPR compliance)
resource "google_cloud_scheduler_job" "cleanup_old_files" {
  name        = "cleanup-old-audio-files"
  description = "Clean up audio files older than 24 hours for GDPR compliance"
  schedule    = "0 */6 * * *" # Every 6 hours
  time_zone   = "UTC"
  region      = var.gcp_region
  project     = var.gcp_project_id

  count = var.enable_scheduler ? 1 : 0

  http_target {
    http_method = "POST"
    uri         = "https://storage.googleapis.com/storage/v1/b/${google_storage_bucket.audio_storage.name}/o"

    headers = {
      "Content-Type" = "application/json"
    }

    # This would require a Cloud Function or Cloud Run service to handle the cleanup
    # The actual cleanup logic would be implemented in the application
  }

  depends_on = [google_project_service.cloudscheduler]
}

# Error Reporting API
resource "google_project_service" "errorreporting" {
  project = var.gcp_project_id
  service = "clouderrorreporting.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false
}