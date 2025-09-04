# DNS Records Configuration
# Note: Root domain (@) and www subdomain are managed externally
# This module only manages coaching assistant related records

# Removed root and www records to avoid conflicts with:
# - www.doxa.com.tw → doxa-offical-web
# - @ → external management

# Frontend domain (Workers)
resource "cloudflare_record" "frontend" {
  zone_id = var.zone_id
  name    = var.environment == "production" ? var.frontend_subdomain : "${var.environment}-${var.frontend_subdomain}"
  content = "coachly-web"  # Match existing CNAME record
  type    = "CNAME"  
  proxied = true  # Essential for Workers to work
  
  comment = "Managed by Terraform - frontend Workers ${var.environment}"
}

# API domain
resource "cloudflare_record" "api" {
  zone_id = var.zone_id
  name    = var.environment == "production" ? var.api_subdomain : "${var.environment}-${var.api_subdomain}"
  content = "coaching-transcript-tool.onrender.com"  # Match existing CNAME
  type    = "CNAME"
  proxied = var.proxied
  
  comment = "Managed by Terraform - API ${var.environment}"
}

# MX Records for email (if needed by coaching assistant)
resource "cloudflare_record" "mx" {
  for_each = var.mx_records
  
  zone_id  = var.zone_id
  name     = "@"
  content  = each.value.server
  type     = "MX"
  priority = each.value.priority
  
  comment = "Managed by Terraform - MX records"
}

# Workers Routes (managed externally via Cloudflare dashboard)
# Current Workers setup:
# - coachly.doxa.com.tw/* -> coachly-doxa-com-tw script
# - www.doxa.com.tw/* -> doxa-offical-web script
# 
# Workers scripts and routes are managed through the Cloudflare dashboard
# This Terraform configuration focuses on DNS records and zone settings

# Workers custom domains are managed through the Cloudflare dashboard
# Current setup handles custom domains automatically through DNS records

# Zone Security Settings
resource "cloudflare_zone_settings_override" "security" {
  zone_id = var.zone_id
  
  settings {
    # SSL/TLS Configuration
    ssl                      = "strict"
    # always_use_https        = true  # Temporarily disabled - configuration issue
    automatic_https_rewrites = "on"
    min_tls_version         = "1.2"
    
    # Security
    security_level          = "medium"
    challenge_ttl           = 1800
    browser_check           = "on"
    privacy_pass            = "on"
    
    # Performance
    brotli                  = "on"
    # minify {  # Temporarily disabled - configuration issue
    #   css  = "on"
    #   html = "on"
    #   js   = "on"
    # }
    
    # Bot Management
    # bot_management removed - not supported in current provider version
  }
}

# Firewall Rules (temporarily disabled - deprecated cloudflare_filter needs migration to cloudflare_ruleset)
# resource "cloudflare_filter" "api_rate_limit" {
#   count = var.enable_firewall_rules ? 1 : 0
#   
#   zone_id     = var.zone_id
#   description = "API Rate Limiting Filter"
#   expression  = "(http.request.uri.path matches \"^/api/.*\" and http.request.method eq \"POST\")"
# }

# resource "cloudflare_firewall_rule" "api_rate_limit" {
#   count = var.enable_firewall_rules ? 1 : 0
#   
#   zone_id     = var.zone_id
#   description = "Rate limit API endpoints"
#   filter_id   = cloudflare_filter.api_rate_limit[0].id
#   action      = "block"
#   priority    = 1
#   
#   # action_parameters removed - not supported in current provider version
#   # Rate limiting now handled via ruleset
# }

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
    # response_headers_override removed - not supported in current provider version
    # CORS headers now handled via Transform Rules
  }
}

# Static caching for Workers is handled through Workers KV or Cache API
# No page rules needed for Workers static assets

# Security headers for Workers are handled within the Worker script itself
# SSL and HTTPS redirects are configured at the zone level

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

# Web Analytics for Workers (temporarily disabled due to permissions)
# resource "cloudflare_web_analytics_site" "frontend" {
#   count = var.web_analytics_tag != "" ? 1 : 0
#   
#   account_id = var.account_id
#   host       = "${cloudflare_record.frontend.name}.${var.domain}"
#   
#   auto_install = false  # Workers handle analytics integration manually
# }