module "cs-svc-coachly-prod1-svc-6j2w" {
  source  = "terraform-google-modules/project-factory/google//modules/svpc_service_project"
  version = "~> 18.0"

  name            = "coachly-prod-service"
  project_id      = "coachly-prod1-svc-6j2w"
  org_id          = var.org_id
  billing_account = var.billing_account
  folder_id       = local.folder_map["Production"].id

  shared_vpc = module.cs-project-vpc-host-prod.project_id

  domain     = data.google_organization.org.domain
  group_name = module.cs-gg-coachly-prod1-service.name
  group_role = "roles/viewer"
}

module "cs-svc-coachly-prod2-svc-6j2w" {
  source  = "terraform-google-modules/project-factory/google//modules/svpc_service_project"
  version = "~> 18.0"

  name            = "coachly-prod2-service"
  project_id      = "coachly-prod2-svc-6j2w"
  org_id          = var.org_id
  billing_account = var.billing_account
  folder_id       = local.folder_map["Production"].id

  shared_vpc = module.cs-project-vpc-host-prod.project_id

  domain     = data.google_organization.org.domain
  group_name = module.cs-gg-coachly-prod2-service.name
  group_role = "roles/viewer"
}

module "cs-svc-coachly-nonprod1-svc-6j2w" {
  source  = "terraform-google-modules/project-factory/google//modules/svpc_service_project"
  version = "~> 18.0"

  name            = "coachly-nonprod1-service"
  project_id      = "coachly-nonprod1-svc-6j2w"
  org_id          = var.org_id
  billing_account = var.billing_account
  folder_id       = local.folder_map["Non-Production"].id

  shared_vpc = module.cs-project-vpc-host-nonprod.project_id

  domain     = data.google_organization.org.domain
  group_name = module.cs-gg-coachly-nonprod1-service.name
  group_role = "roles/viewer"
}

module "cs-svc-coachly-nonprod2-svc-6j2w" {
  source  = "terraform-google-modules/project-factory/google//modules/svpc_service_project"
  version = "~> 18.0"

  name            = "coachly-nonprod2-service"
  project_id      = "coachly-nonprod2-svc-6j2w"
  org_id          = var.org_id
  billing_account = var.billing_account
  folder_id       = local.folder_map["Non-Production"].id

  shared_vpc = module.cs-project-vpc-host-nonprod.project_id

  domain     = data.google_organization.org.domain
  group_name = module.cs-gg-coachly-nonprod2-service.name
  group_role = "roles/viewer"
}
