# Terraform Backend Configuration
terraform {
  backend "gcs" {
    bucket = "coaching-assistant-terraform-state"
    prefix = "production"
    
    # State locking is automatically enabled with GCS backend
    # No additional configuration needed for locking
  }
}
