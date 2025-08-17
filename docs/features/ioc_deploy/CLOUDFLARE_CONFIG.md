# Cloudflare 配置管理

## 概述

使用 Terraform 自動化管理 Cloudflare DNS、Pages 和安全設定，確保前端部署的一致性和可重現性。

## 當前配置問題

### 手動管理的挑戰
- ❌ DNS 記錄手動維護
- ❌ Pages 環境變數分散設定
- ❌ SSL/安全設定不一致
- ❌ 多環境配置容易出錯

### 目標狀態
- ✅ 所有 DNS 記錄透過 Terraform 管理
- ✅ Pages 專案自動化部署和配置
- ✅ 統一的安全和快取策略
- ✅ 環境間配置一致性

## DNS 記錄管理

### 1. 基礎 DNS 配置

```hcl
# DNS 記錄配置
resource "cloudflare_record" "root" {
  zone_id = var.zone_id
  name    = "@"
  value   = "185.199.108.153"  # GitHub Pages IP
  type    = "A"
  proxied = true
  
  tags = ["terraform", "coaching-assistant"]
}

resource "cloudflare_record" "www" {
  zone_id = var.zone_id
  name    = "www"
  value   = "doxa.com.tw"
  type    = "CNAME"
  proxied = true
}

# 前端域名
resource "cloudflare_record" "frontend" {
  zone_id = var.zone_id
  name    = var.frontend_subdomain  # "coachly"
  value   = "${var.pages_project_name}.pages.dev"
  type    = "CNAME"
  proxied = true
  
  tags = ["terraform", "frontend", var.environment]
}

# API 域名
resource "cloudflare_record" "api" {
  zone_id = var.zone_id
  name    = var.api_subdomain  # "api"
  value   = var.render_service_url  # "coaching-api-prod.onrender.com"
  type    = "CNAME"
  proxied = true
  
  tags = ["terraform", "api", var.environment]
}

# MX 記錄 (Email)
resource "cloudflare_record" "mx" {
  for_each = var.mx_records
  
  zone_id  = var.zone_id
  name     = "@"
  value    = each.value.server
  type     = "MX"
  priority = each.value.priority
  
  tags = ["terraform", "email"]
}
```

### 2. 環境特定 DNS

```hcl
# 開發環境
resource "cloudflare_record" "dev_frontend" {
  count = var.environment == "development" ? 1 : 0
  
  zone_id = var.zone_id
  name    = "dev-coachly"
  value   = "${var.pages_project_name}-dev.pages.dev"
  type    = "CNAME"
  proxied = true
}

# Staging 環境
resource "cloudflare_record" "staging_frontend" {
  count = var.environment == "staging" ? 1 : 0
  
  zone_id = var.zone_id
  name    = "staging-coachly"
  value   = "${var.pages_project_name}-staging.pages.dev"
  type    = "CNAME"
  proxied = true
}
```

## Pages 專案配置

### 1. 主要 Pages 專案

```hcl
resource "cloudflare_pages_project" "frontend" {
  account_id        = var.account_id
  name             = "coaching-assistant-frontend"
  production_branch = "main"
  
  source {
    type = "github"
    config {
      owner                         = var.github_owner
      repo_name                    = var.github_repo
      production_branch            = "main"
      pr_comments_enabled          = true
      deployments_enabled          = true
      production_deployment_enabled = true
      preview_deployment_setting   = "custom"
      preview_branch_includes      = ["develop", "staging", "feature/*"]
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
      environment_variables = {
        NODE_VERSION                = "18"
        NEXT_PUBLIC_API_URL        = "https://api.doxa.com.tw"
        NEXT_PUBLIC_ENVIRONMENT    = "production"
        NEXT_PUBLIC_APP_VERSION    = var.app_version
        NEXT_PUBLIC_RECAPTCHA_SITE_KEY = var.recaptcha_site_key
        NEXT_PUBLIC_GOOGLE_CLIENT_ID   = var.google_client_id
      }
      
      compatibility_date  = "2024-08-01"
      compatibility_flags = ["nodejs_compat"]
      
      fail_open                     = false
      always_use_latest_compatibility_date = false
    }
    
    preview {
      environment_variables = {
        NODE_VERSION                = "18"
        NEXT_PUBLIC_API_URL        = "https://api-staging.doxa.com.tw"
        NEXT_PUBLIC_ENVIRONMENT    = "staging"
        NEXT_PUBLIC_APP_VERSION    = var.app_version
        NEXT_PUBLIC_RECAPTCHA_SITE_KEY = var.recaptcha_site_key_staging
        NEXT_PUBLIC_GOOGLE_CLIENT_ID   = var.google_client_id_staging
      }
      
      compatibility_date  = "2024-08-01"
      compatibility_flags = ["nodejs_compat"]
    }
  }
}
```

### 2. 自定義域名

```hcl
resource "cloudflare_pages_domain" "frontend" {
  account_id   = var.account_id
  project_name = cloudflare_pages_project.frontend.name
  domain      = "${var.frontend_subdomain}.${var.domain}"
}
```

## 安全設定

### 1. Zone 安全設定

```hcl
resource "cloudflare_zone_settings_override" "security" {
  zone_id = var.zone_id
  
  settings {
    # SSL/TLS
    ssl                      = "strict"
    always_use_https        = "on"
    automatic_https_rewrites = "on"
    min_tls_version         = "1.2"
    
    # Security
    security_level          = "medium"
    challenge_ttl           = 1800
    browser_check           = "on"
    privacy_pass            = "on"
    
    # Performance
    brotli                  = "on"
    minify {
      css  = "on"
      html = "on"
      js   = "on"
    }
    
    # Bot Management
    bot_management {
      enable_js                = true
      suppress_session_score   = false
      auto_update_model       = true
    }
  }
}
```

### 2. Firewall 規則

```hcl
resource "cloudflare_filter" "api_rate_limit" {
  zone_id     = var.zone_id
  description = "API Rate Limiting Filter"
  expression  = "(http.request.uri.path matches \"^/api/.*\" and http.request.method eq \"POST\")"
}

resource "cloudflare_firewall_rule" "api_rate_limit" {
  zone_id     = var.zone_id
  description = "Rate limit API endpoints"
  filter_id   = cloudflare_filter.api_rate_limit.id
  action      = "block"
  priority    = 1
  
  action_parameters {
    response {
      status_code = 429
      content_type = "application/json"
      content = "{\"error\": \"Rate limit exceeded\"}"
    }
  }
}

# WAF 規則
resource "cloudflare_ruleset" "waf" {
  zone_id = var.zone_id
  name    = "Coaching Assistant WAF"
  kind    = "zone"
  phase   = "http_request_firewall_custom"
  
  rules {
    action = "block"
    expression = "(not ip.geoip.country in {\"TW\" \"US\" \"JP\" \"SG\" \"HK\"}) and (http.request.uri.path contains \"/api/\")"
    description = "Block API access from unauthorized countries"
    enabled = true
  }
  
  rules {
    action = "challenge"
    expression = "(http.request.uri.path contains \"/login\" or http.request.uri.path contains \"/signup\") and cf.threat_score gt 10"
    description = "Challenge suspicious login attempts"
    enabled = true
  }
}
```

## Page Rules

### 1. 快取策略

```hcl
resource "cloudflare_page_rule" "api_bypass_cache" {
  zone_id  = var.zone_id
  target   = "api.${var.domain}/api/*"
  priority = 1
  
  actions {
    cache_level = "bypass"
    ssl         = "strict"
    
    # CORS headers for API
    response_headers_override {
      headers = {
        "Access-Control-Allow-Origin"  = "https://coachly.${var.domain}"
        "Access-Control-Allow-Methods" = "GET, POST, PUT, DELETE, OPTIONS"
        "Access-Control-Allow-Headers" = "Content-Type, Authorization"
      }
    }
  }
}

resource "cloudflare_page_rule" "static_cache" {
  zone_id  = var.zone_id
  target   = "coachly.${var.domain}/_next/static/*"
  priority = 2
  
  actions {
    cache_level = "cache_everything"
    edge_cache_ttl = 31536000  # 1 year
    browser_cache_ttl = 31536000
    ssl = "strict"
  }
}

resource "cloudflare_page_rule" "frontend_cache" {
  zone_id  = var.zone_id
  target   = "coachly.${var.domain}/*"
  priority = 3
  
  actions {
    cache_level = "standard"
    ssl = "strict"
    always_use_https = "on"
    
    # Security headers
    response_headers_override {
      headers = {
        "X-Frame-Options"         = "DENY"
        "X-Content-Type-Options"  = "nosniff"
        "X-XSS-Protection"        = "1; mode=block"
        "Referrer-Policy"         = "strict-origin-when-cross-origin"
        "Permissions-Policy"      = "camera=(), microphone=(), geolocation=()"
      }
    }
  }
}
```

### 2. 重定向規則

```hcl
resource "cloudflare_page_rule" "www_redirect" {
  zone_id  = var.zone_id
  target   = "www.${var.domain}/*"
  priority = 1
  
  actions {
    forwarding_url {
      url         = "https://${var.domain}/$1"
      status_code = 301
    }
  }
}
```

## 分析和監控

### 1. Web Analytics

```hcl
resource "cloudflare_web_analytics_site" "frontend" {
  account_id = var.account_id
  zone_tag   = var.zone_id
  host       = "coachly.${var.domain}"
  
  auto_install = true
}
```

### 2. Log Push

```hcl
resource "cloudflare_logpush_job" "http_requests" {
  enabled         = true
  zone_id         = var.zone_id
  name           = "coaching-assistant-http-logs"
  logpull_options = "fields=ClientIP,ClientRequestHost,ClientRequestMethod,ClientRequestURI,EdgeEndTimestamp,EdgeResponseStatus,EdgeStartTimestamp,RayID&timestamps=rfc3339"
  destination_conf = "gs://coaching-assistant-logs/cloudflare-logs/{DATE}?bucket=coaching-assistant-logs"
  dataset         = "http_requests"
  frequency       = "high"
}
```

## 變數定義

### 1. 必要變數

```hcl
# variables.tf
variable "zone_id" {
  description = "Cloudflare Zone ID"
  type        = string
}

variable "account_id" {
  description = "Cloudflare Account ID"
  type        = string
}

variable "domain" {
  description = "Base domain name"
  type        = string
  default     = "doxa.com.tw"
}

variable "frontend_subdomain" {
  description = "Frontend subdomain"
  type        = string
  default     = "coachly"
}

variable "api_subdomain" {
  description = "API subdomain"
  type        = string
  default     = "api"
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
}

variable "github_owner" {
  description = "GitHub repository owner"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}

variable "render_service_url" {
  description = "Render service URL for API"
  type        = string
}

variable "app_version" {
  description = "Application version"
  type        = string
}

# Security
variable "recaptcha_site_key" {
  description = "reCAPTCHA site key for production"
  type        = string
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  sensitive   = true
}
```

### 2. 輸出值

```hcl
# outputs.tf
output "zone_id" {
  description = "Cloudflare Zone ID"
  value       = var.zone_id
}

output "pages_project_name" {
  description = "Cloudflare Pages project name"
  value       = cloudflare_pages_project.frontend.name
}

output "pages_subdomain" {
  description = "Cloudflare Pages subdomain"
  value       = cloudflare_pages_project.frontend.subdomain
}

output "frontend_url" {
  description = "Frontend URL"
  value       = "https://${var.frontend_subdomain}.${var.domain}"
}

output "api_url" {
  description = "API URL"
  value       = "https://${var.api_subdomain}.${var.domain}"
}

output "web_analytics_site_tag" {
  description = "Web Analytics site tag"
  value       = cloudflare_web_analytics_site.frontend.site_tag
  sensitive   = true
}
```

## 部署驗證

### 1. DNS 驗證腳本

```bash
#!/bin/bash
# scripts/verify-dns.sh

DOMAIN=${1:-doxa.com.tw}

echo "🔍 Verifying DNS configuration for $DOMAIN"

# Check A records
echo "Checking A records..."
dig +short A $DOMAIN

# Check CNAME records
echo "Checking frontend CNAME..."
dig +short CNAME coachly.$DOMAIN

echo "Checking API CNAME..."
dig +short CNAME api.$DOMAIN

# Check SSL
echo "Checking SSL certificate..."
openssl s_client -connect coachly.$DOMAIN:443 -servername coachly.$DOMAIN < /dev/null 2>/dev/null | openssl x509 -noout -subject

echo "✅ DNS verification completed"
```

### 2. 部署後測試

```bash
#!/bin/bash
# scripts/test-deployment.sh

FRONTEND_URL=${1:-https://coachly.doxa.com.tw}
API_URL=${2:-https://api.doxa.com.tw}

echo "🧪 Testing deployment..."

# Test frontend
echo "Testing frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $FRONTEND_URL)
if [ $FRONTEND_STATUS -eq 200 ]; then
    echo "✅ Frontend accessible"
else
    echo "❌ Frontend not accessible (HTTP $FRONTEND_STATUS)"
fi

# Test API health
echo "Testing API health..."
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/api/health)
if [ $API_HEALTH -eq 200 ]; then
    echo "✅ API health check passed"
else
    echo "❌ API health check failed (HTTP $API_HEALTH)"
fi

# Test CORS
echo "Testing CORS..."
CORS_RESULT=$(curl -s -H "Origin: $FRONTEND_URL" -H "Access-Control-Request-Method: GET" -H "Access-Control-Request-Headers: Content-Type" -X OPTIONS $API_URL/api/v1/clients)
if [[ $CORS_RESULT == *"Access-Control-Allow-Origin"* ]]; then
    echo "✅ CORS configured correctly"
else
    echo "❌ CORS configuration issue"
fi

echo "🏁 Deployment testing completed"
```

---

**最後更新**: 2025-08-17  
**版本**: v1.0