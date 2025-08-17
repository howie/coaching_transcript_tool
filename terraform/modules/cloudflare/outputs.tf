# Zone Information
output "zone_id" {
  description = "Cloudflare Zone ID"
  value       = var.zone_id
}

# Pages Project Information
output "pages_project_name" {
  description = "Cloudflare Pages project name"
  value       = cloudflare_pages_project.frontend.name
}

output "pages_project_id" {
  description = "Cloudflare Pages project ID"
  value       = cloudflare_pages_project.frontend.id
}

output "pages_subdomain" {
  description = "Cloudflare Pages subdomain"
  value       = cloudflare_pages_project.frontend.subdomain
}

# URLs
output "frontend_url" {
  description = "Frontend URL"
  value       = "https://${cloudflare_record.frontend.name}.${var.domain}"
}

output "api_url" {
  description = "API URL"
  value       = "https://${cloudflare_record.api.name}.${var.domain}"
}

output "frontend_domain" {
  description = "Frontend domain name"
  value       = "${cloudflare_record.frontend.name}.${var.domain}"
}

output "api_domain" {
  description = "API domain name"
  value       = "${cloudflare_record.api.name}.${var.domain}"
}

# DNS Record IDs
output "frontend_record_id" {
  description = "Frontend DNS record ID"
  value       = cloudflare_record.frontend.id
}

output "api_record_id" {
  description = "API DNS record ID"
  value       = cloudflare_record.api.id
}

# Analytics
output "web_analytics_site_tag" {
  description = "Web Analytics site tag"
  value       = var.web_analytics_tag != "" ? cloudflare_web_analytics_site.frontend[0].site_tag : ""
  sensitive   = true
}

# Security Configuration
output "firewall_rules_enabled" {
  description = "Whether firewall rules are enabled"
  value       = var.enable_firewall_rules
}

output "waf_ruleset_id" {
  description = "WAF ruleset ID"
  value       = var.enable_firewall_rules ? cloudflare_ruleset.waf[0].id : ""
}