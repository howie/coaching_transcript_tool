# Storage Module
module "storage" {
  source = "./storage"
  
  project_id   = var.project_id
  region       = var.region
  environment  = var.environment
  
  buckets      = var.storage_buckets
  cors_origins = var.cors_origins
}

# IAM Module
module "iam" {
  source = "./iam"
  
  project_id = var.project_id
  
  service_accounts = var.service_accounts
  roles           = var.iam_roles
  environment     = var.environment
}

# Speech-to-Text Module
module "speech" {
  source = "./speech"
  
  project_id = var.project_id
  region     = var.region
  
  enable_speech_v2 = var.enable_speech_v2
}

# Local values to handle sensitive for_each limitation
locals {
  secret_keys = keys(var.secrets)
}

# Secret Manager for sensitive data
resource "google_secret_manager_secret" "api_secrets" {
  for_each = toset(local.secret_keys)
  
  project   = var.project_id
  secret_id = each.key
  
  replication {
    auto {}
  }
  
  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "google_secret_manager_secret_version" "api_secrets" {
  for_each = toset(local.secret_keys)
  
  secret      = google_secret_manager_secret.api_secrets[each.key].id
  secret_data = var.secrets[each.key]
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "storage.googleapis.com",
    "speech.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudbuild.googleapis.com"
  ])
  
  project = var.project_id
  service = each.value
  
  disable_on_destroy = false
}

# Audit Logs Configuration
resource "google_project_iam_audit_config" "audit_logs" {
  count = var.enable_audit_logs ? 1 : 0
  
  project = var.project_id
  service = "allServices"
  
  audit_log_config {
    log_type = "ADMIN_READ"
  }
  
  audit_log_config {
    log_type = "DATA_READ"
  }
  
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

# Log Sink for audit logs (if needed)
resource "google_logging_project_sink" "audit_sink" {
  count = var.enable_audit_logs ? 1 : 0
  
  name        = "coaching-assistant-audit-sink-${var.environment}"
  project     = var.project_id
  destination = "storage.googleapis.com/${module.storage.audit_bucket_name}"
  
  filter = "logName:\"projects/${var.project_id}/logs/cloudaudit.googleapis.com\""
  
  unique_writer_identity = true
}

# Grant the sink writer access to the audit bucket
resource "google_storage_bucket_iam_member" "audit_sink_writer" {
  count = var.enable_audit_logs ? 1 : 0
  
  bucket = module.storage.audit_bucket_name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.audit_sink[0].writer_identity
}

# Monitoring notification channels
resource "google_monitoring_notification_channel" "channels" {
  count = var.enable_monitoring ? length(var.notification_channels) : 0
  
  project      = var.project_id
  display_name = var.notification_channels[count.index].display_name
  type         = var.notification_channels[count.index].type
  labels       = var.notification_channels[count.index].labels
  
  enabled = true
}

# Basic monitoring alerts
resource "google_monitoring_alert_policy" "storage_errors" {
  count = var.enable_monitoring ? 1 : 0
  
  project      = var.project_id
  display_name = "Storage API Errors - ${var.environment}"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Storage API error rate"
    
    condition_threshold {
      filter          = "resource.type=\"gcs_bucket\" AND metric.type=\"storage.googleapis.com/api/request_count\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = var.enable_monitoring && length(var.notification_channels) > 0 ? [google_monitoring_notification_channel.channels[0].id] : []
}

resource "google_monitoring_alert_policy" "speech_quota" {
  count = var.enable_monitoring ? 1 : 0
  
  project      = var.project_id
  display_name = "Speech API Quota Usage - ${var.environment}"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Speech API quota usage"
    
    condition_threshold {
      filter          = "resource.type=\"consumed_api\" AND metric.type=\"serviceruntime.googleapis.com/quota/allocation/usage\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8  # 80% of quota
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MAX"
      }
    }
  }
  
  notification_channels = var.enable_monitoring && length(var.notification_channels) > 0 ? [google_monitoring_notification_channel.channels[0].id] : []
}