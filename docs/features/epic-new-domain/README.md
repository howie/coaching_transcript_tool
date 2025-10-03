# Epic: Multi-Domain Support Migration

## Overview

Gradual migration from current production domains to new brand domains, supporting multiple domains simultaneously during the transition period.

## Current State

**Production Domains:**
- Frontend: `coachly.doxa.com.tw`
- Backend API: `api.doxa.com.tw`

## Target State

**New Brand Domains:**
- Primary: `coachly.tw`
- Alternative: `coachly.com.tw`
- Backend API: TBD (e.g., `api.coachly.tw` or `api.coachly.com.tw`)

## Migration Strategy

### Phase 1: Multi-Domain Support
- Add new domains to infrastructure configuration
- Update CORS settings to allow both old and new domains
- Configure SSL certificates for new domains
- Ensure authentication works across all domains

### Phase 2: Gradual Transition
- Run both domains in parallel
- Monitor traffic and analytics
- Communicate migration plan to users
- Update marketing materials progressively

### Phase 3: Deprecation
- Redirect old domains to new domains
- Sunset timeline for `*.doxa.com.tw` domains
- Archive old domain configurations

## Technical Considerations

### Infrastructure Changes

**Frontend (Cloudflare Workers):**
- Update DNS records
- Configure custom domains in Cloudflare
- SSL/TLS certificate provisioning
- Update environment-specific configurations

**Backend (Render.com):**
- Add custom domain to Render service
- Update CORS allowed origins
- Configure API domain routing
- Update health check endpoints

### Application Changes

**Authentication & Sessions:**
- Cookie domain configuration (`.coachly.tw` vs `.doxa.com.tw`)
- JWT token validation
- Session persistence across domains
- OAuth callback URLs

**Frontend Configuration:**
- Environment variable updates (`NEXT_PUBLIC_API_URL`)
- API endpoint references
- Hardcoded domain references audit
- CDN and asset URLs

**Backend Configuration:**
- `ALLOWED_ORIGINS` environment variable
- CORS middleware configuration
- Absolute URL generation (emails, webhooks)
- Third-party service callbacks (ECPay, etc.)

### Security Considerations

- Ensure secure cookie settings (`SameSite`, `Secure` flags)
- HTTPS enforcement on all domains
- HSTS headers configuration
- CSP (Content Security Policy) updates

## Rollback Strategy

- Keep old domains active during migration
- DNS TTL configuration for quick rollback
- Feature flag for domain-specific behavior
- Monitoring and alerting on domain-specific errors

## Success Metrics

- Zero downtime during migration
- No authentication errors across domains
- All third-party integrations functional
- User experience seamless during transition

## Related Documentation

- Terraform configuration: `terraform/environments/production/`
- Frontend deployment: `apps/web/README.md`
- Backend deployment: `docs/deployment/`
- Environment variables: `.env.example`

## Tasks & Timeline

See individual task documents in this directory for detailed implementation plans.
