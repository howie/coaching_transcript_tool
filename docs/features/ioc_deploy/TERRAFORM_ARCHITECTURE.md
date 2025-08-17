# Terraform 架構設計

## 目錄結構

```
terraform/
├── modules/                    # 可重用模組
│   ├── cloudflare/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── versions.tf
│   ├── render/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── versions.tf
│   └── gcp/
│       ├── storage/
│       ├── iam/
│       └── speech/
├── environments/               # 環境特定配置
│   ├── development/
│   │   ├── main.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   │   ├── main.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── production/
│       ├── main.tf
│       ├── terraform.tfvars
│       └── backend.tf
├── shared/                    # 共享資源
│   ├── dns/
│   └── certificates/
└── scripts/                   # 部署腳本
    ├── deploy.sh
    ├── destroy.sh
    └── init.sh
```

## 模組設計

### 1. Cloudflare 模組

```hcl
# modules/cloudflare/main.tf
terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

# DNS 記錄
resource "cloudflare_record" "api" {
  zone_id = var.zone_id
  name    = var.api_subdomain
  value   = var.api_target
  type    = "CNAME"
  proxied = var.proxied
  
  tags = [
    "terraform",
    "coaching-assistant",
    var.environment
  ]
}

resource "cloudflare_record" "frontend" {
  zone_id = var.zone_id
  name    = var.frontend_subdomain
  value   = var.frontend_target
  type    = "CNAME"
  proxied = var.proxied
}

# Pages 專案
resource "cloudflare_pages_project" "frontend" {
  account_id        = var.account_id
  name             = "${var.project_name}-${var.environment}"
  production_branch = var.production_branch
  
  source {
    type = "github"
    config {
      owner                         = var.github_owner
      repo_name                    = var.github_repo
      production_branch            = var.production_branch
      pr_comments_enabled          = true
      deployments_enabled          = true
      production_deployment_enabled = true
      preview_deployment_setting   = "custom"
      preview_branch_includes      = ["develop", "staging"]
    }
  }
  
  build_config {
    build_command       = "cd apps/web && npm ci && npm run build"
    destination_dir     = "apps/web/out"
    root_dir           = "/"
    web_analytics_tag  = var.web_analytics_tag
    web_analytics_token = var.web_analytics_token
  }
  
  deployment_configs {
    production {
      environment_variables = var.production_env_vars
      
      compatibility_date  = "2024-01-01"
      compatibility_flags = ["nodejs_compat"]
    }
    
    preview {
      environment_variables = var.preview_env_vars
      
      compatibility_date  = "2024-01-01"
      compatibility_flags = ["nodejs_compat"]
    }
  }
}

# 頁面規則
resource "cloudflare_page_rule" "api_cache" {
  zone_id = var.zone_id
  target  = "${var.api_subdomain}.${var.domain}/api/*"
  
  actions {
    cache_level = "bypass"
    ssl         = "strict"
  }
  
  priority = 1
}

# SSL 設定
resource "cloudflare_zone_settings_override" "ssl" {
  zone_id = var.zone_id
  
  settings {
    ssl                      = "strict"
    always_use_https        = "on"
    automatic_https_rewrites = "on"
    security_level          = "medium"
    browser_check           = "on"
  }
}
```

### 2. Render 模組

```hcl
# modules/render/main.tf
terraform {
  required_providers {
    render = {
      source  = "render-oss/render"
      version = "~> 1.0"
    }
  }
}

# API Web Service
resource "render_web_service" "api" {
  name               = "${var.project_name}-api-${var.environment}"
  runtime           = "docker"
  repo              = var.github_repo_url
  branch            = var.branch
  root_directory    = "apps/api-server"
  dockerfile_path   = "Dockerfile.api"
  
  service_details {
    env              = var.environment
    plan             = var.api_plan
    region           = var.region
    num_instances    = var.api_instances
    
    auto_deploy      = var.auto_deploy
    
    environment_variables = merge(
      var.common_env_vars,
      var.api_env_vars,
      {
        IS_CONTAINER = "true"
        ENVIRONMENT  = var.environment
        DATABASE_URL = render_postgres.main.connection_string
        REDIS_URL    = render_redis.main.connection_string
      }
    )
    
    secret_files = var.secret_files
  }
  
  custom_domains = var.api_custom_domains
  
  health_check_path = "/api/health"
}

# Celery Worker Service
resource "render_background_worker" "celery" {
  name               = "${var.project_name}-worker-${var.environment}"
  runtime           = "docker"
  repo              = var.github_repo_url
  branch            = var.branch
  root_directory    = "apps/worker"
  dockerfile_path   = "Dockerfile"
  
  service_details {
    env              = var.environment
    plan             = var.worker_plan
    region           = var.region
    
    auto_deploy      = var.auto_deploy
    
    environment_variables = merge(
      var.common_env_vars,
      var.worker_env_vars,
      {
        IS_CONTAINER = "true"
        ENVIRONMENT  = var.environment
        DATABASE_URL = render_postgres.main.connection_string
        REDIS_URL    = render_redis.main.connection_string
      }
    )
    
    secret_files = var.secret_files
  }
}

# PostgreSQL Database
resource "render_postgres" "main" {
  name                = "${var.project_name}-db-${var.environment}"
  plan               = var.database_plan
  region             = var.region
  version            = var.postgres_version
  
  high_availability  = var.database_ha
  
  tags = [
    "terraform",
    "coaching-assistant",
    var.environment
  ]
}

# Redis Instance
resource "render_redis" "main" {
  name   = "${var.project_name}-redis-${var.environment}"
  plan   = var.redis_plan
  region = var.region
  
  tags = [
    "terraform", 
    "coaching-assistant",
    var.environment
  ]
}

# Backup Policy (Enterprise plans only)
resource "render_postgres_backup_policy" "main" {
  count = var.backup_enabled ? 1 : 0
  
  postgres_id = render_postgres.main.id
  retention_days = var.backup_retention_days
  
  schedule {
    hour   = var.backup_hour
    minute = var.backup_minute
  }
}
```

### 3. GCP 增強模組

```hcl
# modules/gcp/main.tf
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# 擴展現有的 GCP 配置
module "storage" {
  source = "./storage"
  
  project_id   = var.project_id
  region       = var.region
  environment  = var.environment
  
  buckets = var.storage_buckets
  cors_origins = var.cors_origins
}

module "iam" {
  source = "./iam"
  
  project_id = var.project_id
  
  service_accounts = var.service_accounts
  roles           = var.iam_roles
}

module "speech" {
  source = "./speech"
  
  project_id = var.project_id
  region     = var.region
  
  enable_speech_v2 = var.enable_speech_v2
}

# Secret Manager (for sensitive data)
resource "google_secret_manager_secret" "api_secrets" {
  for_each = var.secrets
  
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
  for_each = var.secrets
  
  secret      = google_secret_manager_secret.api_secrets[each.key].id
  secret_data = each.value
}
```

## 狀態管理

### Remote Backend 配置

```hcl
# environments/production/backend.tf
terraform {
  backend "gcs" {
    bucket = "coaching-assistant-terraform-state"
    prefix = "production"
  }
}
```

### 狀態鎖定

```hcl
# 使用 GCS + Cloud Build 進行狀態鎖定
resource "google_storage_bucket" "terraform_state" {
  name          = "coaching-assistant-terraform-state"
  location      = "ASIA-SOUTHEAST1"
  force_destroy = false
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}
```

## 環境配置

### Production Environment

```hcl
# environments/production/main.tf
module "cloudflare" {
  source = "../../modules/cloudflare"
  
  zone_id            = var.cloudflare_zone_id
  account_id         = var.cloudflare_account_id
  domain             = "doxa.com.tw"
  api_subdomain      = "api"
  frontend_subdomain = "coachly"
  
  production_env_vars = {
    NEXT_PUBLIC_API_URL = "https://api.doxa.com.tw"
    ENVIRONMENT         = "production"
  }
  
  github_owner = "your-username"
  github_repo  = "coaching_transcript_tool"
  
  environment = "production"
}

module "render" {
  source = "../../modules/render"
  
  project_name     = "coaching-assistant"
  environment      = "production"
  github_repo_url  = "https://github.com/your-username/coaching_transcript_tool"
  branch          = "main"
  
  api_plan         = "standard"
  worker_plan      = "standard"
  database_plan    = "standard"
  redis_plan       = "standard"
  
  api_custom_domains = ["api.doxa.com.tw"]
  
  common_env_vars = {
    ENVIRONMENT = "production"
    GCP_PROJECT_ID = module.gcp.project_id
  }
  
  api_env_vars = {
    ALLOWED_ORIGINS = "https://coachly.doxa.com.tw"
    SECRET_KEY      = var.api_secret_key
  }
}

module "gcp" {
  source = "../../modules/gcp"
  
  project_id  = var.gcp_project_id
  region      = "asia-southeast1"
  environment = "production"
  
  storage_buckets = [
    "coaching-audio-prod",
    "coaching-transcript-prod"
  ]
  
  cors_origins = [
    "https://coachly.doxa.com.tw",
    "https://*.doxa.com.tw"
  ]
}
```

### Variables

```hcl
# environments/production/terraform.tfvars
# Cloudflare
cloudflare_zone_id    = "your-zone-id"
cloudflare_account_id = "your-account-id"

# GCP
gcp_project_id = "coachingassistant"

# Render
api_secret_key = "your-production-secret-key"

# Environment
environment = "production"
```

## 部署腳本

### 初始化腳本

```bash
#!/bin/bash
# scripts/init.sh

set -e

ENVIRONMENT=${1:-production}

echo "🚀 Initializing Terraform for environment: $ENVIRONMENT"

cd "environments/$ENVIRONMENT"

# Initialize Terraform
terraform init

# Create workspace if it doesn't exist
terraform workspace new "$ENVIRONMENT" 2>/dev/null || terraform workspace select "$ENVIRONMENT"

# Validate configuration
terraform validate

echo "✅ Terraform initialized for $ENVIRONMENT"
```

### 部署腳本

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=${1:-production}
AUTO_APPROVE=${2:-false}

echo "🚀 Deploying to environment: $ENVIRONMENT"

cd "environments/$ENVIRONMENT"

# Select workspace
terraform workspace select "$ENVIRONMENT"

# Plan
terraform plan -var-file="terraform.tfvars" -out="tfplan"

# Apply
if [ "$AUTO_APPROVE" = "true" ]; then
    terraform apply -auto-approve "tfplan"
else
    echo "Review the plan above. Do you want to apply? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        terraform apply "tfplan"
    else
        echo "Deployment cancelled"
        exit 1
    fi
fi

echo "✅ Deployment to $ENVIRONMENT completed"
```

## 最佳實踐

### 1. 模組化
- 每個雲端供應商使用獨立模組
- 可重用的組件設計
- 清晰的輸入/輸出介面

### 2. 安全性
- 使用 Secret Manager 管理敏感資料
- 最小權限原則
- 狀態檔案加密

### 3. 版本控制
- 鎖定 Provider 版本
- 使用語義化版本
- 變更記錄追蹤

### 4. 監控
- 資源標記策略
- 成本追蹤
- 部署後驗證

---

**最後更新**: 2025-08-17  
**版本**: v1.0