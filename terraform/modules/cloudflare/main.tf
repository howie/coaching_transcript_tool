# DNS Records Configuration
resource "cloudflare_record" "root" {
  zone_id = var.zone_id
  name    = "@"
  value   = "185.199.108.153"  # GitHub Pages IP
  type    = "A"
  proxied = var.proxied
  
  tags = ["terraform", var.project_name, var.environment]
}

resource "cloudflare_record" "www" {
  zone_id = var.zone_id
  name    = "www"
  value   = var.domain
  type    = "CNAME"
  proxied = var.proxied
  
  tags = ["terraform", var.project_name, var.environment]
}

# Frontend domain
resource "cloudflare_record" "frontend" {
  zone_id = var.zone_id
  name    = var.environment == "production" ? var.frontend_subdomain : "${var.environment}-${var.frontend_subdomain}"
  value   = "${cloudflare_pages_project.frontend.subdomain}.pages.dev"
  type    = "CNAME"
  proxied = var.proxied
  
  tags = ["terraform", "frontend", var.environment]
}

# API domain
resource "cloudflare_record" "api" {
  zone_id = var.zone_id
  name    = var.environment == "production" ? var.api_subdomain : "${var.environment}-${var.api_subdomain}"
  value   = var.render_api_url
  type    = "CNAME"
  proxied = var.proxied
  
  tags = ["terraform", "api", var.environment]
}

# MX Records for email
resource "cloudflare_record" "mx" {
  for_each = var.mx_records
  
  zone_id  = var.zone_id
  name     = "@"
  value    = each.value.server
  type     = "MX"
  priority = each.value.priority
  
  tags = ["terraform", "email"]
}

# Cloudflare Pages Project
resource "cloudflare_pages_project" "frontend" {
  account_id        = var.account_id
  name             = "${var.project_name}-frontend-${var.environment}"
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
      preview_branch_includes      = var.environment == "production" ? ["develop", "staging"] : ["feature/*", "develop"]
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
      environment_variables = merge(
        {
          NODE_VERSION            = "18"
          NEXT_PUBLIC_ENVIRONMENT = var.environment
          NEXT_PUBLIC_APP_VERSION = var.app_version
        },
        var.production_env_vars
      )
      
      compatibility_date  = "2024-08-01"
      compatibility_flags = ["nodejs_compat"]
      
      fail_open                     = false
      always_use_latest_compatibility_date = false
    }
    
    preview {
      environment_variables = merge(
        {
          NODE_VERSION            = "18"
          NEXT_PUBLIC_ENVIRONMENT = "${var.environment}-preview"
          NEXT_PUBLIC_APP_VERSION = var.app_version
        },
        var.preview_env_vars
      )
      
      compatibility_date  = "2024-08-01"
      compatibility_flags = ["nodejs_compat"]
    }
  }
}

# Custom domain for Pages project
resource "cloudflare_pages_domain" "frontend" {
  account_id   = var.account_id
  project_name = cloudflare_pages_project.frontend.name
  domain      = "${cloudflare_record.frontend.name}.${var.domain}"
}

# Zone Security Settings
resource "cloudflare_zone_settings_override" "security" {
  zone_id = var.zone_id
  
  settings {
    # SSL/TLS Configuration
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

# Firewall Rules (if enabled)
resource "cloudflare_filter" "api_rate_limit" {
  count = var.enable_firewall_rules ? 1 : 0
  
  zone_id     = var.zone_id
  description = "API Rate Limiting Filter"
  expression  = "(http.request.uri.path matches \"^/api/.*\" and http.request.method eq \"POST\")"
}

resource "cloudflare_firewall_rule" "api_rate_limit" {
  count = var.enable_firewall_rules ? 1 : 0
  
  zone_id     = var.zone_id
  description = "Rate limit API endpoints"
  filter_id   = cloudflare_filter.api_rate_limit[0].id
  action      = "block"
  priority    = 1
  
  action_parameters {
    response {
      status_code  = 429
      content_type = "application/json"
      content      = "{\"error\": \"Rate limit exceeded\"}"
    }
  }
}

# WAF Custom Rules
resource "cloudflare_ruleset" "waf" {
  count = var.enable_firewall_rules ? 1 : 0
  
  zone_id = var.zone_id
  name    = "${var.project_name}-waf-${var.environment}"
  kind    = "zone"
  phase   = "http_request_firewall_custom"
  
  rules {
    action = "block"
    expression = "(not ip.geoip.country in {${join(" ", formatlist("\"%s\"", var.allowed_countries))}}) and (http.request.uri.path contains \"/api/\")"
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

# Page Rules for Caching and Security
resource "cloudflare_page_rule" "api_bypass_cache" {
  zone_id  = var.zone_id
  target   = "${cloudflare_record.api.name}.${var.domain}/api/*"
  priority = 1
  
  actions {
    cache_level = "bypass"
    ssl         = "strict"
    
    # CORS headers for API
    response_headers_override {
      headers = {
        "Access-Control-Allow-Origin"  = "https://${cloudflare_record.frontend.name}.${var.domain}"
        "Access-Control-Allow-Methods" = "GET, POST, PUT, DELETE, OPTIONS"
        "Access-Control-Allow-Headers" = "Content-Type, Authorization"
      }
    }
  }
}

resource "cloudflare_page_rule" "static_cache" {
  zone_id  = var.zone_id
  target   = "${cloudflare_record.frontend.name}.${var.domain}/_next/static/*"
  priority = 2
  
  actions {
    cache_level       = "cache_everything"
    edge_cache_ttl    = 31536000  # 1 year
    browser_cache_ttl = 31536000
    ssl               = "strict"
  }
}

resource "cloudflare_page_rule" "frontend_security" {
  zone_id  = var.zone_id
  target   = "${cloudflare_record.frontend.name}.${var.domain}/*"
  priority = 3
  
  actions {
    cache_level      = "standard"
    ssl              = "strict"
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

# WWW redirect rule
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

# Web Analytics Site
resource "cloudflare_web_analytics_site" "frontend" {
  count = var.web_analytics_tag != "" ? 1 : 0
  
  account_id = var.account_id
  zone_tag   = var.zone_id
  host       = "${cloudflare_record.frontend.name}.${var.domain}"
  
  auto_install = true
}