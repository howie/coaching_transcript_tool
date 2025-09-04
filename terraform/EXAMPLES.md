# Terraform Configuration Examples

This document provides practical examples for common infrastructure scenarios and customizations.

## 📚 Module Usage Examples

### Basic Cloudflare Setup

```hcl
module "cloudflare" {
  source = "../../modules/cloudflare"
  
  # Core Configuration
  zone_id     = "your-zone-id"
  account_id  = "your-account-id"
  domain      = "yourdomain.com"
  environment = "production"
  
  # DNS Configuration
  frontend_subdomain = "app"      # app.yourdomain.com
  api_subdomain     = "api"       # api.yourdomain.com
  
  # GitHub Integration
  github_owner = "your-username"
  github_repo  = "your-repo"
  
  # Render Service URLs
  render_api_url = "your-api-service.onrender.com"
  
  # Security Settings
  enable_firewall_rules = true
  allowed_countries    = ["US", "CA", "GB"]
}
```

### Basic Render Setup

```hcl
module "render" {
  source = "../../modules/render"
  
  # Core Configuration
  project_name     = "my-app"
  environment      = "production"
  github_repo_url  = "https://github.com/user/repo"
  
  # Service Plans
  api_plan      = "standard"
  worker_plan   = "standard"
  database_plan = "standard"
  redis_plan    = "standard"
  
  # Auto-scaling
  enable_auto_scaling = true
  min_instances      = 2
  max_instances      = 10
  
  # Environment Variables
  api_env_vars = {
    SECRET_KEY = var.api_secret_key
    DEBUG      = "false"
  }
}
```

### Basic GCP Setup

```hcl
module "gcp" {
  source = "../../modules/gcp"
  
  # Core Configuration
  project_id  = "my-gcp-project"
  region      = "us-central1"
  environment = "production"
  
  # Storage Buckets
  storage_buckets = [
    "my-app-audio-prod",
    "my-app-transcripts-prod"
  ]
  
  # CORS for web access
  cors_origins = [
    "https://app.yourdomain.com",
    "https://yourdomain.com"
  ]
  
  # Enable monitoring
  enable_monitoring = true
}
```

## 🏗️ Environment Configuration Examples

### Production Environment

```hcl
# environments/production/main.tf

terraform {
  backend "gcs" {
    bucket = "my-app-terraform-state"
    prefix = "production"
  }
}

module "cloudflare" {
  source = "../../modules/cloudflare"
  
  zone_id     = var.cloudflare_zone_id
  account_id  = var.cloudflare_account_id
  environment = "production"
  
  # Production-specific settings
  enable_firewall_rules = true
  allowed_countries    = ["US", "CA", "GB", "AU"]
  
  production_env_vars = {
    NEXT_PUBLIC_API_URL = "https://api.yourdomain.com"
    NEXT_PUBLIC_ENV     = "production"
  }
}

module "render" {
  source = "../../modules/render"
  
  environment = "production"
  
  # Production service plans
  api_plan      = "pro"
  worker_plan   = "pro"
  database_plan = "pro"
  
  # High availability
  enable_auto_scaling = true
  database_ha        = true
  backup_enabled     = true
  backup_retention_days = 30
  
  # Production monitoring
  monitoring_email = "alerts@yourdomain.com"
}
```

### Staging Environment

```hcl
# environments/staging/main.tf

module "cloudflare" {
  source = "../../modules/cloudflare"
  
  zone_id     = var.cloudflare_zone_id
  account_id  = var.cloudflare_account_id
  environment = "staging"
  
  # Staging-specific settings
  frontend_subdomain = "staging-app"
  api_subdomain     = "staging-api"
  
  # Relaxed security for testing
  enable_firewall_rules = false
  
  production_env_vars = {
    NEXT_PUBLIC_API_URL = "https://staging-api.yourdomain.com"
    NEXT_PUBLIC_ENV     = "staging"
  }
}

module "render" {
  source = "../../modules/render"
  
  environment = "staging"
  
  # Smaller service plans
  api_plan      = "starter"
  worker_plan   = "starter"
  database_plan = "starter"
  
  # Minimal configuration
  enable_auto_scaling = false
  database_ha        = false
  backup_retention_days = 7
}
```

### Development Environment

```hcl
# environments/development/main.tf

module "cloudflare" {
  source = "../../modules/cloudflare"
  
  zone_id     = var.cloudflare_zone_id
  account_id  = var.cloudflare_account_id
  environment = "development"
  
  # Development settings
  frontend_subdomain = "dev-app"
  api_subdomain     = "dev-api"
  
  # No security restrictions
  enable_firewall_rules = false
  
  production_env_vars = {
    NEXT_PUBLIC_API_URL = "https://dev-api.yourdomain.com"
    NEXT_PUBLIC_ENV     = "development"
  }
}

module "render" {
  source = "../../modules/render"
  
  environment = "development"
  
  # Minimal resources
  api_plan      = "starter"
  worker_plan   = "starter"
  database_plan = "starter"
  
  # Development-friendly settings
  enable_auto_scaling = false
  backup_enabled     = false
  
  api_env_vars = {
    DEBUG     = "true"
    LOG_LEVEL = "DEBUG"
  }
}
```

## 🎛️ Advanced Configuration Examples

### Multi-Region Setup

```hcl
# Primary region
module "render_primary" {
  source = "../../modules/render"
  
  project_name = "my-app"
  environment  = "production"
  region      = "oregon"
  
  # Primary region configuration
  enable_read_replica = true
  replica_region     = "virginia"
}

# Secondary region (disaster recovery)
module "render_secondary" {
  source = "../../modules/render"
  
  project_name = "my-app-dr"
  environment  = "production"
  region      = "virginia"
  
  # Disaster recovery configuration
  api_plan      = "starter"  # Smaller for standby
  auto_deploy   = false      # Manual deployment
}
```

### Custom Domain Configuration

```hcl
module "cloudflare" {
  source = "../../modules/cloudflare"
  
  zone_id     = var.cloudflare_zone_id
  account_id  = var.cloudflare_account_id
  environment = "production"
  
  # Custom subdomains
  frontend_subdomain = "portal"     # portal.yourdomain.com
  api_subdomain     = "services"    # services.yourdomain.com
  
  # Additional MX records
  mx_records = {
    google = {
      server   = "aspmx.l.google.com"
      priority = 1
    }
    backup = {
      server   = "alt1.aspmx.l.google.com"
      priority = 5
    }
  }
}
```

### Enhanced Security Configuration

```hcl
module "cloudflare" {
  source = "../../modules/cloudflare"
  
  zone_id     = var.cloudflare_zone_id
  account_id  = var.cloudflare_account_id
  environment = "production"
  
  # Strict security settings
  enable_firewall_rules = true
  allowed_countries    = ["US"]  # US only
  
  # Additional security headers in page rules
  # (configured in main.tf)
}

module "render" {
  source = "../../modules/render"
  
  environment = "production"
  
  # Security environment variables
  api_env_vars = {
    # JWT security
    JWT_ALGORITHM               = "RS256"  # Use RSA instead of HMAC
    ACCESS_TOKEN_EXPIRE_MINUTES = "15"     # Shorter expiry
    
    # Rate limiting
    RATE_LIMIT_ENABLED = "true"
    RATE_LIMIT_MAX     = "100"
    
    # Security headers
    SECURE_HEADERS_ENABLED = "true"
  }
}
```

### Development with Local Integration

```hcl
module "cloudflare" {
  source = "../../modules/cloudflare"
  
  zone_id     = var.cloudflare_zone_id
  account_id  = var.cloudflare_account_id
  environment = "development"
  
  # Development settings
  frontend_subdomain = "dev-app"
  api_subdomain     = "dev-api"
  
  # CORS for local development
  production_env_vars = {
    NEXT_PUBLIC_API_URL = "http://localhost:8000"  # Local API
  }
  
  preview_env_vars = {
    NEXT_PUBLIC_API_URL = "https://dev-api.yourdomain.com"
  }
}

module "render" {
  source = "../../modules/render"
  
  environment = "development"
  
  # Allow local origins
  api_env_vars = {
    ALLOWED_ORIGINS = "http://localhost:3000,https://dev-app.yourdomain.com"
    DEBUG          = "true"
  }
}
```

## 🔧 Custom Module Examples

### Custom Storage Module

```hcl
# modules/custom-storage/main.tf

resource "google_storage_bucket" "custom_bucket" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = var.environment != "production"
  
  # Custom lifecycle rules
  lifecycle_rule {
    condition {
      age                   = var.delete_after_days
      matches_storage_class = ["NEARLINE"]
    }
    action {
      type = "Delete"
    }
  }
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}
```

### Custom Monitoring Module

```hcl
# modules/monitoring/main.tf

resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "High Error Rate - ${var.environment}"
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate > 5%"
    
    condition_threshold {
      filter         = "resource.type=\"gae_app\""
      comparison     = "COMPARISON_GREATER_THAN"
      threshold_value = 0.05
      duration       = "300s"
    }
  }
  
  notification_channels = var.notification_channels
}
```

## 📊 Variable Configuration Examples

### Environment-Specific Variables

```hcl
# environments/production/terraform.tfvars

# Core Configuration
project_name = "coaching-assistant"
environment  = "production"

# Cloudflare
cloudflare_zone_id    = "abc123..."
cloudflare_account_id = "def456..."
domain               = "yourdomain.com"

# GitHub
github_owner = "your-org"
github_repo  = "coaching-app"

# GCP
gcp_project_id = "coaching-prod-123"
gcp_region     = "us-central1"

# Render
render_region = "oregon"

# Security
api_secret_key = "production-secret-key"
google_client_id = "123-abc.apps.googleusercontent.com"

# Monitoring
monitoring_email = "alerts@yourdomain.com"
sentry_dsn      = "https://key@sentry.io/project"
```

### Feature Flags Configuration

```hcl
# Feature flags for gradual rollout
api_env_vars = {
  # Features
  ENABLE_NEW_FEATURE_X = "true"
  ENABLE_BETA_FEATURE  = "false"
  
  # Performance
  ENABLE_CACHING      = "true"
  CACHE_TTL_SECONDS   = "3600"
  
  # Integrations
  ENABLE_SLACK_NOTIFICATIONS = "true"
  ENABLE_EMAIL_NOTIFICATIONS = "true"
}
```

### Conditional Resource Creation

```hcl
# Create read replica only for production
resource "render_postgres_read_replica" "main_replica" {
  count = var.environment == "production" ? 1 : 0
  
  name               = "${var.project_name}-replica"
  primary_postgres_id = render_postgres.main.id
  region             = var.replica_region
}

# Enable monitoring only for staging and production
resource "google_monitoring_alert_policy" "api_errors" {
  count = contains(["staging", "production"], var.environment) ? 1 : 0
  
  display_name = "API Errors - ${var.environment}"
  # ... configuration
}
```

## 🚀 Deployment Script Examples

### Custom Deployment with Validation

```bash
#!/bin/bash
# scripts/custom-deploy.sh

set -e

ENVIRONMENT=$1
APP_VERSION=$2

# Validate inputs
if [[ -z "$ENVIRONMENT" ]] || [[ -z "$APP_VERSION" ]]; then
    echo "Usage: $0 <environment> <app_version>"
    exit 1
fi

# Pre-deployment checks
echo "Running pre-deployment checks..."
./scripts/validate.sh $ENVIRONMENT

# Update version in terraform.tfvars
sed -i "s/app_version = .*/app_version = \"$APP_VERSION\"/" environments/$ENVIRONMENT/terraform.tfvars

# Deploy
echo "Deploying version $APP_VERSION to $ENVIRONMENT..."
./scripts/plan.sh $ENVIRONMENT
./scripts/deploy.sh $ENVIRONMENT

# Post-deployment verification
echo "Running post-deployment tests..."
sleep 30  # Wait for services to start

FRONTEND_URL=$(cd environments/$ENVIRONMENT && terraform output -raw frontend_url)
API_URL=$(cd environments/$ENVIRONMENT && terraform output -raw api_url)

# Health checks
curl -f "$FRONTEND_URL" || exit 1
curl -f "$API_URL/api/health" || exit 1

echo "Deployment successful!"
```

### Blue-Green Deployment Example

```bash
#!/bin/bash
# scripts/blue-green-deploy.sh

ENVIRONMENT=$1
COLOR=$2  # blue or green

# Deploy to specific color environment
./scripts/deploy.sh $ENVIRONMENT-$COLOR

# Run smoke tests
if ./scripts/test-deployment.sh $ENVIRONMENT-$COLOR; then
    # Switch traffic
    echo "Switching traffic to $COLOR environment..."
    # Update DNS or load balancer configuration
    
    # Clean up old environment
    echo "Cleaning up old environment..."
    OTHER_COLOR=$([ "$COLOR" = "blue" ] && echo "green" || echo "blue")
    ./scripts/destroy.sh $ENVIRONMENT-$OTHER_COLOR --force
else
    echo "Deployment failed, keeping current environment"
    exit 1
fi
```

## 🔍 Monitoring and Alerting Examples

### Custom Dashboards

```hcl
resource "google_monitoring_dashboard" "app_dashboard" {
  dashboard_json = jsonencode({
    displayName = "Coaching Assistant - ${title(var.environment)}"
    mosaicLayout = {
      tiles = [
        {
          width = 6
          height = 4
          widget = {
            title = "API Response Time"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"http_load_balancer\""
                  }
                }
              }]
            }
          }
        }
      ]
    }
  })
}
```

### Slack Alerting Integration

```hcl
resource "google_monitoring_notification_channel" "slack" {
  display_name = "Slack Alerts"
  type         = "slack"
  
  labels = {
    channel_name = "#alerts"
    url          = var.slack_webhook_url
  }
}
```

These examples provide a comprehensive starting point for customizing your infrastructure deployment. Mix and match these patterns based on your specific requirements.