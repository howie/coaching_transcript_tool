# Enable Speech-to-Text API
resource "google_project_service" "speech_api" {
  project = var.project_id
  service = "speech.googleapis.com"
  
  disable_on_destroy = false
}

# Enable Speech-to-Text v2 API (if enabled)
resource "google_project_service" "speech_v2_api" {
  count = var.enable_speech_v2 ? 1 : 0
  
  project = var.project_id
  service = "speech.googleapis.com"  # v2 uses the same API endpoint
  
  disable_on_destroy = false
  
  depends_on = [google_project_service.speech_api]
}

# Create a custom Speech model configuration (if needed in future)
# This is a placeholder for when custom models are supported
# resource "google_speech_phrase_set" "custom_phrases" {
#   phrase_set_id = "coaching-phrases-${var.environment}"
#   
#   phrases {
#     value = "coaching session"
#     boost = 10.0
#   }
#   
#   phrases {
#     value = "client goals"
#     boost = 10.0
#   }
#   
#   phrases {
#     value = "action items"
#     boost = 10.0
#   }
# }

# Set up Cloud Monitoring for Speech API usage
resource "google_monitoring_dashboard" "speech_dashboard" {
  count = var.enable_monitoring ? 1 : 0
  
  project        = var.project_id
  dashboard_json = jsonencode({
    displayName = "Speech-to-Text API Monitoring - ${title(var.environment)}"
    mosaicLayout = {
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "Speech API Requests"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"consumed_api\" AND metric.type=\"serviceruntime.googleapis.com/api/request_count\" AND resource.label.service=\"speech.googleapis.com\""
                    }
                    unitOverride = "1"
                  }
                  plotType = "LINE"
                }
              ]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Requests"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width  = 6
          height = 4
          widget = {
            title = "Speech API Errors"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"consumed_api\" AND metric.type=\"serviceruntime.googleapis.com/api/request_count\" AND resource.label.service=\"speech.googleapis.com\" AND metric.label.response_code!=\"200\""
                    }
                    unitOverride = "1"
                  }
                  plotType = "LINE"
                }
              ]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Errors"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width  = 12
          height = 4
          widget = {
            title = "Speech API Quota Usage"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"consumer_quota\" AND metric.type=\"serviceruntime.googleapis.com/quota/allocation/usage\" AND resource.label.service=\"speech.googleapis.com\""
                    }
                    unitOverride = "1"
                  }
                  plotType = "LINE"
                }
              ]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Quota Usage"
                scale = "LINEAR"
              }
            }
          }
        }
      ]
    }
  })
}

# Create alert policy for Speech API quota usage
resource "google_monitoring_alert_policy" "speech_quota_alert" {
  count = var.enable_monitoring ? 1 : 0
  
  project      = var.project_id
  display_name = "Speech API Quota Alert - ${var.environment}"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Speech API quota usage high"
    
    condition_threshold {
      filter          = "resource.type=\"consumer_quota\" AND metric.type=\"serviceruntime.googleapis.com/quota/allocation/usage\" AND resource.label.service=\"speech.googleapis.com\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8  # Alert at 80% quota usage
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MAX"
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  alert_strategy {
    auto_close = "1800s"  # Auto-close after 30 minutes
  }
}

# Create alert policy for Speech API errors
resource "google_monitoring_alert_policy" "speech_error_alert" {
  count = var.enable_monitoring ? 1 : 0
  
  project      = var.project_id
  display_name = "Speech API Error Rate Alert - ${var.environment}"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Speech API error rate high"
    
    condition_threshold {
      filter          = "resource.type=\"consumed_api\" AND metric.type=\"serviceruntime.googleapis.com/api/request_count\" AND resource.label.service=\"speech.googleapis.com\" AND metric.label.response_code!=\"200\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5  # Alert if more than 5 errors in 5 minutes
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  alert_strategy {
    auto_close = "1800s"
  }
}