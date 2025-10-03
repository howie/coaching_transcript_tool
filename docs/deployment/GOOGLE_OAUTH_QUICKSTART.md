# Google OAuth Quick Start Guide

## ⚡ Quick Setup (5 Minutes)

### 1. Google Cloud Console
```
1. Go to: https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID
3. Add Authorized redirect URIs:
   - https://api.doxa.com.tw/api/v1/auth/google/callback
   - http://localhost:8000/api/v1/auth/google/callback
4. Copy Client ID and Client Secret
```

### 2. Backend Environment Variables
```bash
# Add to .env or production environment
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
FRONTEND_URL=https://coachly.doxa.com.tw
ENVIRONMENT=production
```

### 3. Deploy
```bash
# Format and lint
uv run ruff format . && uv run ruff check . --fix

# Deploy frontend (includes middleware)
make deploy-frontend

# Restart backend with new environment variables
# (via your deployment method)
```

## ✅ Test Checklist

- [ ] Visit https://coachly.doxa.com.tw/login
- [ ] Click "Sign in with Google"
- [ ] Opens Google login page (no CSP errors)
- [ ] Complete authentication
- [ ] Redirects to /dashboard successfully
- [ ] User logged in

## 🐛 Common Issues

### redirect_uri_mismatch
```
Fix: Ensure exact match in Google Console
✅ https://api.doxa.com.tw/api/v1/auth/google/callback
❌ https://api.doxa.com.tw/api/v1/auth/google/callback/
```

### CSP Violations
```
Fix: Ensure middleware.ts is deployed
Check: ls apps/web/middleware.ts
Redeploy: make deploy-frontend
```

### Wrong redirect domain
```
Fix: Check FRONTEND_URL environment variable
echo $FRONTEND_URL
Should be: https://coachly.doxa.com.tw
```

## 📝 Files Modified

- ✅ `apps/web/middleware.ts` (NEW)
- ✅ `src/coaching_assistant/api/v1/auth.py`
- ✅ Backend `.env` with GOOGLE_* vars

## 📚 Full Documentation

See: `docs/deployment/google-oauth-setup.md`
