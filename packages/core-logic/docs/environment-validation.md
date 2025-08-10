# Environment Variable Validation

The Coaching Assistant API includes comprehensive environment variable validation that runs automatically at startup. This ensures that all required configuration is present and valid before the application starts.

## 🚀 Overview

The environment validation system:
- **Validates required variables** - Blocks startup if critical config is missing
- **Checks optional variables** - Warns about missing recommended settings
- **Validates content format** - Ensures variables contain valid values
- **Environment-specific checks** - Applies stricter rules for production
- **Provides clear guidance** - Shows exactly what needs to be fixed

## 📋 Required Environment Variables

These variables are **mandatory** and the application will not start without them:

| Variable | Description | Validation |
|----------|-------------|------------|
| `DATABASE_URL` | PostgreSQL connection string | Must start with `postgresql://` |
| `SECRET_KEY` | JWT token signing key | Min 32 characters, no default in production |
| `GOOGLE_PROJECT_ID` | Google Cloud project ID | Must not be placeholder value |
| `GOOGLE_STORAGE_BUCKET` | GCS bucket name | Valid bucket name format (3-63 chars) |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | Service account credentials | Valid JSON with required fields |

## 🔧 Recommended Environment Variables

These variables are **optional** but enable important features:

| Variable | Description | Impact if Missing |
|----------|-------------|-------------------|
| `REDIS_URL` | Redis connection for Celery | Transcription features disabled |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Google login disabled |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret | Google login disabled |
| `RECAPTCHA_SECRET` | reCAPTCHA secret key | Spam protection disabled |
| `SENTRY_DSN` | Error tracking endpoint | No error monitoring |

## 🏭 Production-Specific Validation

In production environment (`ENVIRONMENT=production`), additional checks apply:
- `SECRET_KEY` cannot use the default development value
- `RECAPTCHA_SECRET` cannot use the test key
- Enhanced security warnings for missing monitoring tools

## 🧪 Validation Checks

### Google Credentials Validation
The validator checks that `GOOGLE_APPLICATION_CREDENTIALS_JSON` contains:
- Valid JSON structure (or valid base64-encoded JSON)
- Required fields: `type`, `project_id`, `private_key`, `client_email`
- `type` must be `"service_account"`
- No placeholder values (like `"your-project-id"`)

### Database URL Validation
- Must start with `postgresql://` or `postgres://`
- Should be accessible (connection validation happens later)

### Secret Key Security
- Minimum 32 characters for security
- Cannot use default development key in production
- Warns about weak or default keys

## 📤 Validation Output

### Successful Validation
```
🚀 Starting Coaching Transcript Tool Backend API...
🔍 Checking required environment variables...
✅ DATABASE_URL: Found
✅ SECRET_KEY: Found
✅ GOOGLE_PROJECT_ID: Found
✅ GOOGLE_STORAGE_BUCKET: Found
✅ GOOGLE_APPLICATION_CREDENTIALS_JSON: Found

🔍 Checking recommended environment variables...
✅ REDIS_URL: Found
⚠️  SENTRY_DSN: Not configured (Sentry DSN for error tracking)

============================================================
📊 ENVIRONMENT VALIDATION REPORT
============================================================
Environment: development
Status: ✅ VALID

⚠️  WARNINGS (Recommended to fix):
  ⚠️  SENTRY_DSN: Sentry DSN for error tracking (recommended for production)

✅ All environment variables validated successfully!
============================================================
```

### Failed Validation
```
🔍 Checking required environment variables...
❌ DATABASE_URL: PostgreSQL database connection URL
❌ GOOGLE_PROJECT_ID: Google Cloud project ID

============================================================
📊 ENVIRONMENT VALIDATION REPORT
============================================================
Environment: development
Status: ❌ INVALID

❌ ERRORS (Must fix before starting):
  ❌ DATABASE_URL: PostgreSQL database connection URL
  ❌ GOOGLE_PROJECT_ID: Google Cloud project ID

🛑 STARTUP BLOCKED: Please fix the errors above

📝 Quick Setup Guide:
1. Copy .env.example to .env
2. Fill in the required values
3. Run scripts/setup_env/setup-gcs.sh for Google Cloud setup
4. Restart the application
============================================================

💥 Application startup aborted due to missing configuration!
```

## 🛠️ How to Fix Common Issues

### Missing Required Variables
1. Copy `.env.example` to `.env`
2. Fill in all required values
3. Restart the application

### Invalid Google Credentials
1. Run the setup script: `./scripts/setup_env/setup-gcs.sh PROJECT_ID`
2. Copy the output to your `.env` file
3. Ensure no placeholder values remain

### Production Security Issues
1. Generate a strong secret key: `openssl rand -hex 32`
2. Get real reCAPTCHA keys from Google
3. Set up proper monitoring (Sentry)

## 🔍 Testing Validation

You can test the validation system:

```bash
# Run the validation test suite
python scripts/test_env_validation.py

# Test specific scenarios
python -c "
import os
del os.environ['DATABASE_URL']  # Remove a required var
from coaching_assistant.main import app  # This will fail
"
```

## 🚫 Disabling Validation (Not Recommended)

For development only, you can bypass validation by setting:
```bash
SKIP_ENV_VALIDATION=true
```

**Warning**: This is not recommended as it may lead to runtime errors.

## 🔧 Customizing Validation

To modify validation rules, edit `src/coaching_assistant/core/env_validator.py`:

```python
# Add new required variables
REQUIRED_VARS = {
    "NEW_REQUIRED_VAR": "Description of what this does",
    # ... existing vars
}

# Add custom validation logic
def _validate_var_content(self, var_name: str, value: str) -> Tuple[bool, str]:
    if var_name == "NEW_REQUIRED_VAR":
        # Custom validation logic
        if not value.startswith("expected_prefix"):
            return False, "Must start with expected_prefix"
        return True, ""
    # ... existing validations
```

## 📚 Related Documentation

- [Environment Setup Guide](../scripts/setup_env/README.md)
- [Configuration Options](configuration.md)
- [Deployment Guide](deployment.md)

## 💡 Best Practices

1. **Always validate locally** before deploying
2. **Use different configs** per environment
3. **Never commit secrets** to version control
4. **Set up monitoring** in production (Sentry)
5. **Rotate credentials** regularly (every 90 days)
6. **Test with minimal config** to catch missing variables early

---

*Last Updated: 2025-01-09*