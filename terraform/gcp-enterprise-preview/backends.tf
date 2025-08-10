terraform {
  backend "gcs" {
    bucket = "bucket-name-placeholder-UPDATE-ME"
    prefix = "terraform"
  }
}
