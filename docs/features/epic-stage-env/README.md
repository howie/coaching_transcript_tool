# Epic: Staging Environment Setup

**Status**: Planned
**Priority**: High
**Created**: 2025-10-03
**Related Epic**: Multi-Domain Support Migration (`docs/features/epic-new-domain/`)

---

## Overview

建立完整的 staging 環境，用於在部署到 production 前進行完整的功能測試和驗證。Staging 環境將採用新的 domain 架構（`coachly.tw` / `coachly.com.tw`），作為新 domain 遷移的先行測試環境。

---

## Problem Statement

### 當前痛點

1. **OAuth 測試困難**
   - Google OAuth redirect URIs 有嚴格限制
   - localhost 無法完整測試跨域 CSP 行為
   - 生產環境的 OAuth Client 不應包含開發用 URIs

2. **第三方服務整合風險**
   - ECPay 支付 webhooks 在本地無法測試
   - 需要公開 URL 才能接收外部 callbacks
   - 直接在 production 測試風險太高

3. **新 Domain 遷移測試需求**
   - 需要驗證新 domain (`coachly.tw`) 的完整功能
   - 測試 CORS、Cookie、OAuth 在新 domain 的行為
   - 在遷移到 production 前發現潛在問題

4. **環境差異導致的 Bug**
   - HTTP vs HTTPS 行為不同
   - CSP policies 在不同環境表現不一致
   - DNS、SSL 證書等基礎設施問題只在部署後才發現

---

## Goals

### Primary Goals

1. **建立完整的 staging 環境**
   - 使用新的 domain 架構: `staging.coachly.tw` 和 `api-staging.coachly.tw`
   - 與 production 相同的基礎架構配置
   - 獨立的數據庫和 Redis instance

2. **第三方服務整合測試**
   - 獨立的 Google OAuth Client (staging)
   - ECPay 測試環境配置
   - 獨立的 Google Cloud Storage buckets

3. **新 Domain 架構驗證**
   - 測試 `.coachly.tw` domain 的所有功能
   - 驗證 Cookie domain 設定 (`.coachly.tw`)
   - 確認 OAuth callbacks 在新 domain 正常運作

4. **自動化部署流程**
   - Git branch-based deployment
   - CI/CD pipeline for staging
   - 簡化的 promotion to production flow

---

## Architecture

### Domain Structure (New Brand Domains)

| Environment | Frontend | Backend API |
|-------------|----------|-------------|
| **Production (Current)** | `coachly.doxa.com.tw` | `api.doxa.com.tw` |
| **Production (Target)** | `coachly.tw` | `api.coachly.tw` |
| **Staging (New)** | `staging.coachly.tw` | `api-staging.coachly.tw` |
| **Development** | `localhost:3000` | `localhost:8000` |

### Infrastructure Overview

```
┌─────────────────────────────────────────────────────────────┐
│              Staging Environment (New Domains)               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend (Cloudflare Workers)                              │
│  ├─ Domain: staging.coachly.tw                              │
│  ├─ Workers: coachly-staging-tw                             │
│  ├─ SSL: Cloudflare Universal SSL                           │
│  └─ Cookie Domain: .coachly.tw                              │
│                                                              │
│  Backend (Render.com)                                       │
│  ├─ Service: coaching-assistant-api-staging                 │
│  ├─ Domain: api-staging.coachly.tw                          │
│  └─ Environment: staging                                     │
│                                                              │
│  Database (Render PostgreSQL)                               │
│  ├─ Instance: coaching-assistant-staging-db                 │
│  └─ Separate from production                                │
│                                                              │
│  Redis (Render Redis)                                       │
│  ├─ Instance: coaching-assistant-staging-redis              │
│  └─ Separate from production                                │
│                                                              │
│  Storage (Google Cloud Storage)                             │
│  ├─ Bucket: coaching-audio-staging-asia                     │
│  └─ Lifecycle: 7 days retention                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Domain Setup (Week 1)

#### 1.1 Domain Registration & DNS
- [ ] Verify `coachly.tw` domain ownership
- [ ] Create DNS records in Cloudflare:
  ```
  staging.coachly.tw → CNAME to Cloudflare Workers
  api-staging.coachly.tw → CNAME to Render.com
  ```
- [ ] Configure SSL certificates (via Cloudflare Universal SSL)
- [ ] Set up Cloudflare Zone for `coachly.tw`

#### 1.2 Backend Deployment (Render.com)
- [ ] Create new Render service: `coaching-assistant-api-staging`
- [ ] Add custom domain: `api-staging.coachly.tw`
- [ ] Configure environment variables (see Configuration section)
- [ ] Set up PostgreSQL database (separate instance)
- [ ] Set up Redis instance (separate instance)
- [ ] Deploy backend to staging

#### 1.3 Frontend Deployment (Cloudflare Workers)
- [ ] Create wrangler config: `wrangler.staging.toml`
- [ ] Configure custom domain: `staging.coachly.tw`
- [ ] Update API proxy routes to `api-staging.coachly.tw`
- [ ] Deploy frontend to staging

#### 1.4 Storage Setup (Google Cloud Storage)
- [ ] Create GCS bucket: `coaching-audio-staging-asia`
- [ ] Configure bucket lifecycle (7 days retention)
- [ ] Set up service account permissions
- [ ] Update backend config for staging bucket

---

### Phase 2: Third-Party Integration (Week 2)

#### 2.1 Google OAuth (Critical for CSP Testing)
- [ ] Create new OAuth Client in Google Cloud Console
  - **Name**: `Coaching Assistant - Staging (New Domain)`
  - **Application type**: Web application
  - **Authorized JavaScript origins**:
    - `https://staging.coachly.tw`
  - **Authorized redirect URIs**:
    - `https://api-staging.coachly.tw/api/v1/auth/google/callback`
    - `https://staging.coachly.tw/api/v1/auth/google/callback`
- [ ] Configure OAuth credentials in staging environment
- [ ] Test OAuth flow end-to-end
- [ ] **Verify CSP middleware fix** - no CSP errors on Google login page

#### 2.2 ECPay Integration
- [ ] Configure ECPay test environment
- [ ] Set up webhook callback URLs:
  - `https://api-staging.coachly.tw/api/v1/webhooks/ecpay/payment`
- [ ] Test payment flow with ECPay sandbox

#### 2.3 Cookie Configuration
- [ ] Set cookie domain to `.coachly.tw`
- [ ] Verify cookie persistence across subdomains
- [ ] Test authentication with new cookie domain

---

### Phase 3: CI/CD Pipeline (Week 3)

#### 3.1 GitHub Actions Workflow

**File**: `.github/workflows/deploy-staging.yml`

```yaml
name: Deploy to Staging

on:
  push:
    branches:
      - staging

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      # Run tests
      - name: Run tests
        run: make test

      # Deploy backend
      - name: Deploy Backend to Render
        run: git push render-staging staging:main

      # Deploy frontend
      - name: Deploy Frontend to Cloudflare
        working-directory: apps/web
        run: |
          npm ci
          npm run build
          npm run build:cf -- --env staging
          npx wrangler deploy --env staging
```

#### 3.2 Branch Strategy
```
main (production: coachly.doxa.com.tw)
  ├─ staging (auto-deploy to staging.coachly.tw)
  ├─ hotfix/* (urgent fixes → main)
  └─ feature/* (PR to staging → test → PR to main)
```

---

## Configuration Details

### Environment Variables

#### Backend (Render.com)

```bash
# Environment
ENVIRONMENT=staging
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql://[staging-db-url]

# Redis
REDIS_URL=redis://[staging-redis-url]

# JWT
SECRET_KEY=[staging-secret-key]

# Google Cloud
GOOGLE_PROJECT_ID=coachingassistant
GCP_REGION=asia-east1
AUDIO_STORAGE_BUCKET=coaching-audio-staging-asia
GOOGLE_APPLICATION_CREDENTIALS_JSON=[staging-service-account-json]

# Google OAuth (New Staging Client)
GOOGLE_CLIENT_ID=[staging-new-domain-client-id].apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=[staging-new-domain-client-secret]

# CORS (New Domain)
ALLOWED_ORIGINS=["https://staging.coachly.tw"]

# Frontend/Backend URLs (New Domain)
FRONTEND_URL=https://staging.coachly.tw
API_BASE_URL=https://api-staging.coachly.tw

# ECPay (Test Environment)
ECPAY_ENVIRONMENT=sandbox
ECPAY_MERCHANT_ID=3002607
ECPAY_HASH_KEY=pwFHCqoQZGmho4w6
ECPAY_HASH_IV=EkRm7iFT261dpevs

# Cookie Configuration (New Domain)
COOKIE_DOMAIN=.coachly.tw
COOKIE_SECURE=true
COOKIE_SAMESITE=lax

# Monitoring
SENTRY_DSN=[staging-sentry-dsn]
SENTRY_ENVIRONMENT=staging
```

#### Frontend (Cloudflare Workers)

**File**: `apps/web/wrangler.staging.toml`

```toml
name = "coachly-staging-tw"
compatibility_date = "2024-01-01"
main = "src/index.ts"

[env.staging]
name = "coachly-staging-tw"
route = "staging.coachly.tw/*"

[env.staging.vars]
NEXT_PUBLIC_API_BASE_URL = "https://api-staging.coachly.tw"
NEXT_PUBLIC_ENVIRONMENT = "staging"
NEXT_PUBLIC_DOMAIN = "coachly.tw"
```

---

## Testing Guide

### Critical: CSP Middleware Fix Verification

這是建立 staging 環境的主要動機之一 - 驗證 Google OAuth CSP fix。

#### Test Plan

1. **Deploy CSP Fix to Staging**
   ```bash
   # After merging CSP fix
   git checkout staging
   git merge main
   git push origin staging
   # Wait for auto-deployment
   ```

2. **Manual Testing**
   ```bash
   # Visit staging login page
   open https://staging.coachly.tw/login

   # Open DevTools Console (⌘+Option+J)
   # Click "Login with Google"

   # EXPECTED: No CSP errors
   # EXPECTED: Google OAuth page loads correctly
   # EXPECTED: Can complete OAuth flow and login
   ```

3. **Verify CSP Headers**
   ```bash
   # Google OAuth route should NOT have CSP header
   curl -I https://staging.coachly.tw/api/proxy/v1/auth/google/login
   # Expected: No Content-Security-Policy header

   # Other routes SHOULD have CSP header
   curl -I https://staging.coachly.tw/
   # Expected: Content-Security-Policy header present
   ```

### Additional Testing

#### OAuth Flow Testing
```bash
# Full OAuth flow
1. Visit https://staging.coachly.tw/login
2. Click "Login with Google"
3. Select Google account
4. Grant permissions
5. Verify redirect to https://staging.coachly.tw/dashboard
6. Verify user logged in correctly
```

#### Payment Testing (ECPay Sandbox)
```bash
# Test payment
1. Navigate to subscription page
2. Select a plan
3. Complete payment with ECPay test credentials
4. Verify webhook callback received
5. Verify subscription activated
```

#### New Domain Cookie Testing
```bash
# Test cookie domain
1. Login at staging.coachly.tw
2. Check browser cookies
3. Verify cookie domain is .coachly.tw
4. Test cookie persistence across page navigation
```

---

## Success Criteria

- [ ] Staging accessible at `staging.coachly.tw`
- [ ] Backend API accessible at `api-staging.coachly.tw`
- [ ] **Google OAuth works without CSP errors**
- [ ] ECPay payment flow testable with sandbox
- [ ] Cookies set with `.coachly.tw` domain
- [ ] Transcription feature works with staging GCS bucket
- [ ] CI/CD pipeline deploys to staging automatically
- [ ] All features work identically to production
- [ ] New domain architecture validated for production migration

---

## Benefits for New Domain Migration

1. **Risk Mitigation**
   - Test new domain (`coachly.tw`) before production cutover
   - Identify domain-specific issues early
   - Validate SSL/DNS configuration

2. **OAuth Validation**
   - Verify OAuth clients work with new domain
   - Test CSP middleware fix in production-like environment
   - Ensure redirect URIs configured correctly

3. **Cookie Testing**
   - Validate `.coachly.tw` cookie domain settings
   - Test cross-subdomain authentication
   - Verify secure cookie flags

4. **Confidence Building**
   - Complete feature parity testing
   - Performance baseline on new domain
   - User acceptance testing before migration

---

## Cost Estimation

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| Render Web Service (Backend) | Starter | $7 |
| Render PostgreSQL | Starter | $7 |
| Render Redis | Free | $0 |
| Cloudflare Workers | Free tier | $0 |
| Google Cloud Storage | Standard (100GB) | ~$2 |
| Domain (`coachly.tw`) | Already owned | $0 |
| **Total** | | **~$16/month** |

---

## Rollout Timeline

### Week 1: Infrastructure & Domains
- Day 1: DNS setup, domain verification
- Day 2-3: Render services deployment
- Day 4: Cloudflare Workers setup
- Day 5: Initial staging deployment

### Week 2: Integration & Testing
- Day 1-2: Google OAuth configuration
- Day 3: ECPay setup
- Day 4-5: CSP fix verification and OAuth testing

### Week 3: Automation
- Day 1-2: GitHub Actions workflows
- Day 3-4: Documentation
- Day 5: Team training

### Week 4: Validation
- Day 1-3: Comprehensive testing
- Day 4: Bug fixes
- Day 5: Production readiness review

---

## Maintenance

### Regular Tasks
- **Weekly**: Review staging logs for errors
- **Monthly**: Update dependencies and redeploy
- **Quarterly**: Rotate secrets and credentials

### Data Lifecycle
- **Retention**: 7 days for audio files
- **Reset**: Fresh test data as needed
- **Backups**: Not required (test data only)

---

## Related Documents

- **Multi-Domain Migration**: `docs/features/epic-new-domain/README.md`
- **CSP Fix Issue**: `docs/issues/google-oauth-csp-conflict.md`
- **Deployment Guide**: `docs/deployment/README.md`
- **Terraform Config**: `terraform/environments/`

---

## Next Steps

1. **Immediate**: Merge and deploy CSP fix to production
2. **Week 1**: Begin staging environment setup
3. **Week 2**: Deploy CSP fix to staging for validation
4. **Week 3-4**: Complete staging implementation
5. **Future**: Use staging for new domain migration testing
