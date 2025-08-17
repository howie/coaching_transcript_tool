# In order to create google groups, the calling identity should have at least the
# Group Admin role in Google Admin. More info: https://support.google.com/a/answer/2405986

module "cs-gg-coachly-prod1-service" {
  source  = "terraform-google-modules/group/google"
  version = "~> 0.6"

  id           = "coachly-prod1-service@doxa.com.tw"
  display_name = "coachly-prod1-service"
  customer_id  = data.google_organization.org.directory_customer_id
  types = [
    "default",
    "security",
  ]
}

module "cs-gg-coachly-prod2-service" {
  source  = "terraform-google-modules/group/google"
  version = "~> 0.6"

  id           = "coachly-prod2-service@doxa.com.tw"
  display_name = "coachly-prod2-service"
  customer_id  = data.google_organization.org.directory_customer_id
  types = [
    "default",
    "security",
  ]
}

module "cs-gg-coachly-nonprod1-service" {
  source  = "terraform-google-modules/group/google"
  version = "~> 0.6"

  id           = "coachly-nonprod1-service@doxa.com.tw"
  display_name = "coachly-nonprod1-service"
  customer_id  = data.google_organization.org.directory_customer_id
  types = [
    "default",
    "security",
  ]
}

module "cs-gg-coachly-nonprod2-service" {
  source  = "terraform-google-modules/group/google"
  version = "~> 0.6"

  id           = "coachly-nonprod2-service@doxa.com.tw"
  display_name = "coachly-nonprod2-service"
  customer_id  = data.google_organization.org.directory_customer_id
  types = [
    "default",
    "security",
  ]
}
