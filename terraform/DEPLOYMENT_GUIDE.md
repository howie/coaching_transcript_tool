# Infrastructure Deployment Guide

This guide provides step-by-step instructions for deploying the Coaching Assistant Platform infrastructure using Terraform.

## 📋 Prerequisites Checklist

### 1. Software Requirements

- [ ] **Terraform** >= 1.5.0 (`terraform version`)
- [ ] **Google Cloud CLI** >= 450.0.0 (`gcloud version`)
- [ ] **jq** for JSON processing (`jq --version`)
- [ ] **curl** for connectivity tests (`curl --version`)

### 2. Account Setup

- [ ] **GCP Project** with billing enabled
- [ ] **Cloudflare Account** with domain added
- [ ] **Render Account** with payment method
- [ ] **GitHub Repository** with appropriate permissions

### 3. API Keys and Tokens

- [ ] Cloudflare API Token with Zone and Account permissions
- [ ] Render API Key from account settings
- [ ] GCP Service Account with required roles
- [ ] GitHub Personal Access Token (if using private repos)

## 🔧 Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-username/coaching_transcript_tool.git
cd coaching_transcript_tool/terraform
```

### 2. GCP Authentication

```bash
# Authenticate with Google Cloud
gcloud auth login

# Set default project
gcloud config set project YOUR_GCP_PROJECT_ID

# Create application default credentials
gcloud auth application-default login
```

### 3. Create Terraform State Bucket

```bash
# Create bucket for Terraform state
gsutil mb -p YOUR_GCP_PROJECT_ID -l asia-southeast1 gs://coaching-assistant-terraform-state

# Enable versioning
gsutil versioning set on gs://coaching-assistant-terraform-state
```

## 🌍 Environment Deployment

### Production Environment

#### Step 1: Initialize Terraform

```bash
./scripts/init.sh production
```

Expected output:
```
🚀 Terraform Initialization Script
==================================
ℹ️  Initializing Terraform for environment: production
✅ Prerequisites check completed
✅ Backend bucket created: coaching-assistant-terraform-state
✅ Terraform initialized
✅ Created new workspace: production
✅ Configuration is valid
✅ Terraform initialization completed for environment: production
```

#### Step 2: Configure Variables

```bash
cd environments/production
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your actual values:

```hcl
# Provider Credentials
cloudflare_api_token = "your-actual-cloudflare-api-token"
render_api_key       = "your-actual-render-api-key"

# Cloudflare Configuration
cloudflare_zone_id    = "your-actual-zone-id"
cloudflare_account_id = "your-actual-account-id"
domain                = "yourdomain.com"

# GitHub Configuration
github_owner    = "your-github-username"
github_repo     = "coaching_transcript_tool"
github_repo_url = "https://github.com/your-github-username/coaching_transcript_tool"

# GCP Configuration
gcp_project_id = "your-gcp-project-id"

# Application Secrets (generate secure values)
api_secret_key = "super-secure-secret-key-for-production"

# Continue with other required values...
```

#### Step 3: Validate Configuration

```bash
cd ../../  # Back to terraform root
./scripts/validate.sh production
```

#### Step 4: Generate Deployment Plan

```bash
./scripts/plan.sh production
```

Review the plan output carefully:
- Check resource counts
- Verify configurations
- Ensure no unexpected deletions

#### Step 5: Deploy Infrastructure

```bash
./scripts/deploy.sh production
```

Follow the interactive prompts to confirm deployment.

#### Step 6: Verify Deployment

```bash
# Check service status
cd environments/production
terraform output

# Test endpoints
curl -I https://your-frontend-url
curl https://your-api-url/api/health
```

### Staging Environment

Follow similar steps for staging with reduced resources:

```bash
# Initialize
./scripts/init.sh staging

# Configure variables (use staging values)
cd environments/staging
cp terraform.tfvars.example terraform.tfvars
# Edit with staging-specific values

# Deploy
cd ../../
./scripts/validate.sh staging
./scripts/plan.sh staging
./scripts/deploy.sh staging
```

### Development Environment

For development with minimal resources:

```bash
# Initialize
./scripts/init.sh development

# Configure variables (use development values)
cd environments/development
cp terraform.tfvars.example terraform.tfvars
# Edit with development-specific values

# Deploy
cd ../../
./scripts/validate.sh development
./scripts/plan.sh development
./scripts/deploy.sh development
```

## 🔄 Update Procedures

### Infrastructure Updates

1. **Make Changes**
   ```bash
   # Edit Terraform files
   vim modules/cloudflare/main.tf
   ```

2. **Validate Changes**
   ```bash
   ./scripts/validate.sh production
   ```

3. **Plan Updates**
   ```bash
   ./scripts/plan.sh production
   ```

4. **Apply Updates**
   ```bash
   ./scripts/deploy.sh production
   ```

### Configuration Updates

1. **Update Variables**
   ```bash
   # Edit terraform.tfvars
   vim environments/production/terraform.tfvars
   ```

2. **Plan and Apply**
   ```bash
   ./scripts/plan.sh production
   ./scripts/deploy.sh production
   ```

## 🚨 Emergency Procedures

### Rollback Deployment

If a deployment fails or causes issues:

1. **Check Previous State**
   ```bash
   cd environments/production
   terraform state list
   terraform show
   ```

2. **Revert to Previous Configuration**
   ```bash
   git checkout HEAD~1 -- .
   terraform plan
   terraform apply
   ```

3. **Restore from Backup**
   ```bash
   # If state is corrupted
   cp backups/latest/terraform.tfstate.backup terraform.tfstate
   terraform refresh
   ```

### Service Recovery

1. **Database Issues**
   ```bash
   # Check database status
   terraform output database_host
   
   # Restore from backup if needed (through Render dashboard)
   ```

2. **DNS Issues**
   ```bash
   # Check DNS propagation
   dig your-domain.com
   
   # Force refresh Cloudflare
   terraform apply -replace=module.cloudflare.cloudflare_record.api
   ```

3. **Service Downtime**
   ```bash
   # Restart services
   terraform apply -replace=module.render.render_web_service.api
   ```

## 🔍 Monitoring and Maintenance

### Regular Maintenance Tasks

1. **Weekly Checks**
   ```bash
   # Validate configuration
   ./scripts/validate.sh
   
   # Check for drift
   terraform plan -detailed-exitcode
   ```

2. **Monthly Tasks**
   - Review and rotate API keys
   - Check backup retention
   - Update provider versions
   - Review cost optimization

3. **Quarterly Tasks**
   - Security audit
   - Disaster recovery testing
   - Performance optimization
   - Documentation updates

### Monitoring Checklist

- [ ] Cloudflare Analytics dashboard
- [ ] Render service metrics
- [ ] GCP monitoring alerts
- [ ] Cost tracking and budgets
- [ ] Security event logs

## 🐛 Troubleshooting Guide

### Common Error Solutions

#### Authentication Errors

**Error**: `Error: could not find default credentials`
```bash
# Solution
gcloud auth application-default login
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
```

**Error**: `Error: Invalid Cloudflare API token`
```bash
# Verify token permissions
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
     -H "Authorization: Bearer YOUR_TOKEN"
```

#### State Lock Issues

**Error**: `Error acquiring the state lock`
```bash
# Find lock info
terraform state list

# Force unlock (use carefully)
terraform force-unlock LOCK_ID
```

#### Resource Conflicts

**Error**: `Resource already exists`
```bash
# Import existing resource
terraform import module.cloudflare.cloudflare_record.api RECORD_ID

# Or remove from state
terraform state rm module.cloudflare.cloudflare_record.api
```

#### Provider Version Issues

**Error**: `Provider version constraint not met`
```bash
# Update providers
terraform init -upgrade

# Check versions
terraform version
```

### Getting Support

1. **Check Logs**
   ```bash
   # Enable debug logging
   export TF_LOG=DEBUG
   terraform plan
   ```

2. **Validate Configuration**
   ```bash
   ./scripts/validate.sh
   ```

3. **Community Resources**
   - Terraform Documentation
   - Provider GitHub Issues
   - Stack Overflow
   - HashiCorp Community Forum

## 📊 Performance Optimization

### Resource Optimization

1. **Right-sizing Services**
   - Monitor resource utilization
   - Adjust instance sizes based on usage
   - Use auto-scaling appropriately

2. **Cost Optimization**
   - Review unused resources
   - Optimize storage lifecycle policies
   - Use appropriate service tiers

3. **Security Hardening**
   - Regular security scans
   - Update provider versions
   - Review IAM permissions

### Scaling Considerations

1. **Horizontal Scaling**
   - Configure auto-scaling policies
   - Use load balancing
   - Optimize database connections

2. **Geographic Distribution**
   - Consider multi-region deployment
   - CDN optimization
   - Edge computing

## 📝 Documentation Updates

When making infrastructure changes:

1. Update this deployment guide
2. Update module documentation
3. Update environment-specific README files
4. Document breaking changes
5. Update troubleshooting sections

## 🔗 Next Steps

After successful deployment:

1. **Application Deployment**
   - Configure CI/CD pipelines
   - Deploy application code
   - Run integration tests

2. **Monitoring Setup**
   - Configure alerting rules
   - Set up dashboards
   - Test incident response

3. **Security Review**
   - Run security scans
   - Review access controls
   - Document security procedures

4. **Documentation**
   - Update operational runbooks
   - Create incident response procedures
   - Train team members