module "cs-folders-iam-0-computeinstanceAdminv1" {
  source  = "terraform-google-modules/iam/google//modules/folders_iam"
  version = "~> 8.0"

  folders = [
    local.folder_map["Non-Production"].id,
  ]
  bindings = {
    "roles/compute.instanceAdmin.v1" = [
      "group:gcp-developers@doxa.com.tw",
    ]
  }
}

module "cs-folders-iam-0-containeradmin" {
  source  = "terraform-google-modules/iam/google//modules/folders_iam"
  version = "~> 8.0"

  folders = [
    local.folder_map["Non-Production"].id,
  ]
  bindings = {
    "roles/container.admin" = [
      "group:gcp-developers@doxa.com.tw",
    ]
  }
}

module "cs-folders-iam-1-computeinstanceAdminv1" {
  source  = "terraform-google-modules/iam/google//modules/folders_iam"
  version = "~> 8.0"

  folders = [
    local.folder_map["Development"].id,
  ]
  bindings = {
    "roles/compute.instanceAdmin.v1" = [
      "group:gcp-developers@doxa.com.tw",
    ]
  }
}

module "cs-folders-iam-1-containeradmin" {
  source  = "terraform-google-modules/iam/google//modules/folders_iam"
  version = "~> 8.0"

  folders = [
    local.folder_map["Development"].id,
  ]
  bindings = {
    "roles/container.admin" = [
      "group:gcp-developers@doxa.com.tw",
    ]
  }
}

module "cs-projects-iam-2-loggingviewer" {
  source  = "terraform-google-modules/iam/google//modules/projects_iam"
  version = "~> 8.0"

  projects = [
    module.cs-project-logging-monitoring.project_id,
  ]
  bindings = {
    "roles/logging.viewer" = [
      "group:gcp-logging-monitoring-viewers@doxa.com.tw",
    ]
  }
}

module "cs-projects-iam-2-loggingprivateLogViewer" {
  source  = "terraform-google-modules/iam/google//modules/projects_iam"
  version = "~> 8.0"

  projects = [
    module.cs-project-logging-monitoring.project_id,
  ]
  bindings = {
    "roles/logging.privateLogViewer" = [
      "group:gcp-logging-monitoring-viewers@doxa.com.tw",
    ]
  }
}

module "cs-projects-iam-2-bigquerydataViewer" {
  source  = "terraform-google-modules/iam/google//modules/projects_iam"
  version = "~> 8.0"

  projects = [
    module.cs-project-logging-monitoring.project_id,
  ]
  bindings = {
    "roles/bigquery.dataViewer" = [
      "group:gcp-logging-monitoring-viewers@doxa.com.tw",
    ]
  }
}

module "cs-projects-iam-2-pubsubviewer" {
  source  = "terraform-google-modules/iam/google//modules/projects_iam"
  version = "~> 8.0"

  projects = [
    module.cs-project-logging-monitoring.project_id,
  ]
  bindings = {
    "roles/pubsub.viewer" = [
      "group:gcp-logging-monitoring-viewers@doxa.com.tw",
    ]
  }
}

module "cs-projects-iam-2-monitoringviewer" {
  source  = "terraform-google-modules/iam/google//modules/projects_iam"
  version = "~> 8.0"

  projects = [
    module.cs-project-logging-monitoring.project_id,
  ]
  bindings = {
    "roles/monitoring.viewer" = [
      "group:gcp-logging-monitoring-viewers@doxa.com.tw",
    ]
  }
}

module "cs-projects-iam-3-bigquerydataViewer" {
  source  = "terraform-google-modules/iam/google//modules/projects_iam"
  version = "~> 8.0"

  projects = [
    module.cs-project-logging-monitoring.project_id,
  ]
  bindings = {
    "roles/bigquery.dataViewer" = [
      "group:gcp-security-admins@doxa.com.tw",
    ]
  }
}

module "cs-projects-iam-3-pubsubviewer" {
  source  = "terraform-google-modules/iam/google//modules/projects_iam"
  version = "~> 8.0"

  projects = [
    module.cs-project-logging-monitoring.project_id,
  ]
  bindings = {
    "roles/pubsub.viewer" = [
      "group:gcp-security-admins@doxa.com.tw",
    ]
  }
}

module "cs-service-projects-iam-4-computeinstanceAdminv1" {
  source  = "terraform-google-modules/iam/google//modules/projects_iam"
  version = "~> 8.0"

  projects = [
    module.cs-svc-coachly-prod1-svc-6j2w.project_id,
  ]
  bindings = {
    "roles/compute.instanceAdmin.v1" = [
      "group:${module.cs-gg-coachly-prod1-service.id}",
    ]
  }
}

module "cs-service-projects-iam-5-computeinstanceAdminv1" {
  source  = "terraform-google-modules/iam/google//modules/projects_iam"
  version = "~> 8.0"

  projects = [
    module.cs-svc-coachly-prod2-svc-6j2w.project_id,
  ]
  bindings = {
    "roles/compute.instanceAdmin.v1" = [
      "group:${module.cs-gg-coachly-prod2-service.id}",
    ]
  }
}

module "cs-service-projects-iam-6-computeinstanceAdminv1" {
  source  = "terraform-google-modules/iam/google//modules/projects_iam"
  version = "~> 8.0"

  projects = [
    module.cs-svc-coachly-nonprod1-svc-6j2w.project_id,
  ]
  bindings = {
    "roles/compute.instanceAdmin.v1" = [
      "group:${module.cs-gg-coachly-nonprod1-service.id}",
    ]
  }
}

module "cs-service-projects-iam-7-computeinstanceAdminv1" {
  source  = "terraform-google-modules/iam/google//modules/projects_iam"
  version = "~> 8.0"

  projects = [
    module.cs-svc-coachly-nonprod2-svc-6j2w.project_id,
  ]
  bindings = {
    "roles/compute.instanceAdmin.v1" = [
      "group:${module.cs-gg-coachly-nonprod2-service.id}",
    ]
  }
}
