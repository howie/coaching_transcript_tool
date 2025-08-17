# General Buckets
output "buckets" {
  description = "Created storage buckets"
  value       = { for k, v in google_storage_bucket.buckets : k => v.name }
}

# Specific Bucket Names
output "audio_bucket_name" {
  description = "Audio storage bucket name"
  value       = google_storage_bucket.audio.name
}

output "transcript_bucket_name" {
  description = "Transcript storage bucket name"
  value       = google_storage_bucket.transcripts.name
}

output "audit_bucket_name" {
  description = "Audit logs bucket name"
  value       = google_storage_bucket.audit_logs.name
}

# Bucket URLs
output "audio_bucket_url" {
  description = "Audio storage bucket URL"
  value       = google_storage_bucket.audio.url
}

output "transcript_bucket_url" {
  description = "Transcript storage bucket URL"
  value       = google_storage_bucket.transcripts.url
}

output "audit_bucket_url" {
  description = "Audit logs bucket URL"
  value       = google_storage_bucket.audit_logs.url
}

# Bucket Self Links
output "audio_bucket_self_link" {
  description = "Audio storage bucket self link"
  value       = google_storage_bucket.audio.self_link
}

output "transcript_bucket_self_link" {
  description = "Transcript storage bucket self link"
  value       = google_storage_bucket.transcripts.self_link
}

output "audit_bucket_self_link" {
  description = "Audit logs bucket self link"
  value       = google_storage_bucket.audit_logs.self_link
}