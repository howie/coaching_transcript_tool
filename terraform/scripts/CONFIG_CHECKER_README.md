# Configuration Environment Checker

A specialized subagent for checking and comparing local development configuration with production/staging environments in the coaching assistant platform.

## 📋 Overview

The Configuration Environment Checker provides comprehensive validation, comparison, and security auditing of environment configurations across development, staging, and production environments. It ensures consistency, identifies misconfigurations, and helps maintain security best practices.

## 🚀 Features

### 1. Configuration Validation
- ✅ **Required Variable Checking**: Validates all essential environment variables are present
- ✅ **Format Validation**: Ensures variables follow expected patterns (URLs, keys, IDs)
- ✅ **Environment-Specific Rules**: Different requirements for dev/staging/production
- ✅ **Dependency Verification**: Checks related configurations are consistent

### 2. Environment Consistency Checks
- 🔄 **Multi-Environment Comparison**: Compare configurations between environments
- 🔄 **Database Connection Validation**: Verify database settings across environments
- 🔄 **STT Provider Configuration**: Validate Speech-to-Text provider settings
- 🔄 **Authentication Settings**: Check Google OAuth and reCAPTCHA configurations
- 🔄 **Payment Gateway Validation**: Verify ECPay settings for different environments
- 🔄 **Storage Configuration**: Validate GCS bucket configurations and access

### 3. Security Auditing
- 🔒 **Secret Detection**: Identify hardcoded secrets or API keys in code
- 🔒 **Default Value Detection**: Find test/demo values in production configs
- 🔒 **Credential Strength**: Validate key and secret length/complexity
- 🔒 **Environment Separation**: Ensure production secrets aren't used in development
- 🔒 **Sensitive Data Exposure**: Check for secrets in logs or visible locations

### 4. Terraform Integration
- ⚙️ **Configuration Consistency**: Compare .env files with terraform.tfvars
- ⚙️ **Variable Mapping**: Automatic translation between env and terraform variables
- ⚙️ **Infrastructure Sync**: Ensure application config matches deployed infrastructure
- ⚙️ **Deployment Validation**: Pre-deployment configuration checks

## 📁 File Structure

```
terraform/scripts/
├── config-checker.py          # Main Python configuration checker
├── check-config.sh            # Shell wrapper for easy usage
├── CONFIG_CHECKER_README.md   # This documentation
└── env-to-tfvars.py          # Existing env-to-tfvars conversion tool
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- Bash shell
- Access to project configuration files

### Quick Setup

```bash
# Make the shell script executable (already done)
chmod +x terraform/scripts/check-config.sh

# Verify setup
./terraform/scripts/check-config.sh --help
```

## 📖 Usage Guide

### 1. Quick Start - Comprehensive Check

Run a full configuration audit across all environments:

```bash
# From project root
./terraform/scripts/check-config.sh comprehensive

# Or using the terraform Makefile
cd terraform/gcp && make config-check
```

### 2. Environment-Specific Checks

Check specific environments only:

```bash
# Check only development and production
./terraform/scripts/check-config.sh comprehensive -e development,production

# Validate single environment
./terraform/scripts/check-config.sh validate production
```

### 3. Security Auditing

Focus on security-related configuration issues:

```bash
# Security audit
./terraform/scripts/check-config.sh security-audit

# Or using Makefile
cd terraform/gcp && make config-check-security
```

### 4. Environment Comparison

Compare configurations between environments:

```bash
# Compare development vs production
./terraform/scripts/check-config.sh compare development production

# Compare staging vs production
./terraform/scripts/check-config.sh compare staging production
```

### 5. Terraform Consistency Check

Validate that environment variables match Terraform configurations:

```bash
# Check production Terraform consistency
./terraform/scripts/check-config.sh terraform-check production

# Or using Makefile
cd terraform/gcp && make config-check-terraform
```

### 6. Configuration Discovery

Find all configuration files in the project:

```bash
# Discover configurations
./terraform/scripts/check-config.sh discover

# Or using Makefile
cd terraform/gcp && make config-discover
```

### 7. Generate Reports

Create detailed markdown reports:

```bash
# Generate comprehensive report
./terraform/scripts/check-config.sh report

# Generate with custom filename
./terraform/scripts/check-config.sh report my-config-audit.md

# Or using Makefile
cd terraform/gcp && make config-report
```

## 📊 Understanding the Output

### Exit Codes

The checker uses specific exit codes to indicate the severity of issues found:

- **0**: ✅ No issues found, configuration is healthy
- **1**: ⚠️ High priority issues found (should be addressed)
- **2**: 🔴 Critical issues found (must be fixed before deployment)

### Issue Severity Levels

- **🔴 Critical**: Missing required configuration, system will fail
- **🟠 High**: Security risks, major functionality issues
- **🟡 Medium**: Inconsistencies, deprecated configurations
- **🔵 Low**: Recommendations, minor issues
- **ℹ️ Info**: Informational notices, best practices

### Report Sections

Generated reports include:

1. **📊 Executive Summary**: High-level overview of configuration health
2. **🌍 Environment Status**: Per-environment configuration status
3. **🔧 Detailed Analysis**: Specific issues and recommendations per environment
4. **🔒 Security Recommendations**: Security best practices and warnings
5. **🛠️ Next Steps**: Actionable items prioritized by importance

## ⚙️ Configuration Variables Checked

### Required Variables by Environment

#### All Environments (Development, Staging, Production)

**Database & Cache:**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection for caching and task queue

**Application Security:**
- `SECRET_KEY` - JWT and cryptography secret (32+ characters)

**Google Cloud Platform:**
- `GCP_PROJECT_ID` - GCP project identifier
- `GOOGLE_APPLICATION_CREDENTIALS_JSON` - Service account credentials

**Storage Configuration:**
- `AUDIO_STORAGE_BUCKET` - GCS bucket for audio files
- `TRANSCRIPT_STORAGE_BUCKET` - GCS bucket for transcripts

**Authentication:**
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `RECAPTCHA_SITE_KEY` - reCAPTCHA public key
- `RECAPTCHA_SECRET` - reCAPTCHA private key

**Speech-to-Text:**
- `STT_PROVIDER` - Provider selection (google|assemblyai|auto)
- `GOOGLE_STT_MODEL` - STT model (chirp_2, latest_long, etc.)
- `GOOGLE_STT_LOCATION` - Processing region (asia-southeast1, etc.)

#### Production-Only Variables

**Payment Processing:**
- `ECPAY_MERCHANT_ID` - ECPay merchant identifier
- `ECPAY_HASH_KEY` - ECPay hash key for transactions
- `ECPAY_HASH_IV` - ECPay initialization vector
- `ECPAY_ENVIRONMENT` - Should be "production"

### Deprecated Variables

The checker will flag these deprecated variables and suggest replacements:

- `GOOGLE_STORAGE_BUCKET` → `AUDIO_STORAGE_BUCKET`
- `STORAGE_BUCKET` → `AUDIO_STORAGE_BUCKET`

### Sensitive Variables

These variables are subject to additional security checks:

- All `*SECRET*`, `*KEY*`, `*PASSWORD*` variables
- `GOOGLE_APPLICATION_CREDENTIALS_JSON`
- `ADMIN_WEBHOOK_TOKEN`
- `SENTRY_DSN`

## 🔧 Advanced Configuration

### Custom Project Root

Specify a different project root directory:

```bash
./terraform/scripts/check-config.sh comprehensive --project-root /path/to/project
```

### Environment-Specific Configurations

The checker automatically discovers configuration files using these patterns:

**Development:**
- `.env`, `.env.local`, `.env.development`, `.env.dev`

**Staging:**
- `.env.staging`, `.env.test`

**Production:**
- `.env.production`, `.env.prod`

**Terraform:**
- `terraform/environments/*/terraform.tfvars`
- `terraform/gcp/terraform.tfvars.*`

### Custom Validation Rules

The checker uses regex patterns to validate configuration values. Key patterns include:

```python
# Database URLs
DATABASE_URL: r'^postgresql://.+'

# GCP Project IDs
GCP_PROJECT_ID: r'^[a-z][-a-z0-9]{5,29}$'

# Google OAuth Client IDs
GOOGLE_CLIENT_ID: r'^.+\.apps\.googleusercontent\.com$'

# Storage Buckets
AUDIO_STORAGE_BUCKET: r'^coaching-audio-(dev|staging|prod)(-[a-z0-9-]+)?$'

# STT Providers
STT_PROVIDER: r'^(google|assemblyai|auto)$'
```

## 🔄 Integration with Existing Tools

### With env-to-tfvars.py

The configuration checker reuses the variable mapping from the existing `env-to-tfvars.py` tool:

```bash
# Convert environment to terraform variables
python terraform/scripts/env-to-tfvars.py --env-file .env.prod --environment production

# Then validate the consistency
./terraform/scripts/check-config.sh terraform-check production
```

### With Terraform Makefile

All config checking commands are integrated into the terraform Makefile:

```bash
cd terraform/gcp

# Quick checks
make config-check              # Comprehensive check
make config-check-security     # Security audit
make config-check-terraform    # Terraform consistency
make config-discover          # Find config files
make config-report            # Generate report
```

### With CI/CD Pipeline

Add configuration validation to your deployment pipeline:

```yaml
# Example GitHub Action step
- name: Validate Configuration
  run: |
    ./terraform/scripts/check-config.sh comprehensive
  env:
    PROJECT_ROOT: ${{ github.workspace }}
```

## 🚨 Common Issues and Solutions

### Missing Required Variables

**Problem**: Critical variables are missing from environment configuration.

**Solution**:
1. Check the error message for specific missing variables
2. Add the missing variables to your `.env` file
3. Ensure values follow the expected format patterns
4. Re-run the validation

### Configuration Drift

**Problem**: Environment variables don't match Terraform configuration.

**Solution**:
1. Use `terraform-check` command to identify differences
2. Update either the `.env` file or `terraform.tfvars` to match
3. Use `env-to-tfvars.py` to sync if needed
4. Verify with another check

### Security Warnings

**Problem**: Default or weak values detected in production.

**Solution**:
1. Generate strong, unique values for production secrets
2. Ensure test/demo values aren't used in production
3. Rotate any exposed or weak credentials
4. Implement proper secret management

### Environment Inconsistencies

**Problem**: Same variables have different values between environments when they shouldn't.

**Solution**:
1. Review the comparison report
2. Determine if differences are intentional
3. Standardize common configuration values
4. Document environment-specific requirements

## 🔍 Troubleshooting

### Permission Issues

```bash
# Make sure script is executable
chmod +x ./terraform/scripts/check-config.sh

# Check file permissions
ls -la ./terraform/scripts/
```

### Python Dependencies

The checker uses only Python standard library, but ensure Python 3.8+ is available:

```bash
python3 --version
which python3
```

### Configuration File Discovery

If files aren't found:

```bash
# Use discovery mode to see what's detected
./terraform/scripts/check-config.sh discover

# Check file naming patterns
find . -name ".env*" -o -name "terraform.tfvars*"
```

### Report Generation Issues

```bash
# Check write permissions in target directory
ls -la
touch test-report.md && rm test-report.md

# Specify full path for output
./terraform/scripts/check-config.sh report /full/path/to/report.md
```

## 📚 Related Documentation

- **Environment Variables Guide**: `/terraform/ENVIRONMENT_VARIABLES.md`
- **Deployment Guide**: `/terraform/DEPLOYMENT_GUIDE.md`
- **Terraform Documentation**: `/terraform/README.md`
- **Project Configuration**: `/CLAUDE.md`

## 🤝 Contributing

To extend the configuration checker:

1. **Add New Variables**: Update `REQUIRED_VARIABLES` dictionary in `config-checker.py`
2. **Add Validation Patterns**: Include regex patterns for new variable types
3. **Add Security Rules**: Extend `SENSITIVE_VARIABLES` and security check logic
4. **Update Documentation**: Keep this README current with new features

## 📝 Example Reports

### Healthy Configuration Output

```
✅ Configuration check completed!
📊 Environments: 3
📊 Total Issues: 0
📊 Critical: 0 | High: 0
```

### Issues Found Output

```
⚠️ Configuration check completed with issues
📊 Environments: 3
📊 Total Issues: 5
📊 Critical: 1 | High: 2

Critical Issues:
🔴 production: SECRET_KEY is missing
🔴 production: DATABASE_URL format invalid

High Issues:
🟠 production: RECAPTCHA_SECRET appears to use test value
🟠 staging: GOOGLE_CLIENT_SECRET too short for security
```

---

*This tool helps ensure consistent, secure, and properly validated configuration across all environments of the coaching assistant platform.*