# User Story 030: CI/CD Integration & Automated Deployment

## Story Overview
**Epic**: Administrative Management & Analytics
**Story ID**: US-030  
**Priority**: Critical (Phase 1)
**Effort**: 15 Story Points

## User Story
**As a development team, I want automated CI/CD pipelines with comprehensive testing integration so that we can deploy payment system changes safely and efficiently to production.**

## Business Value
- **Deployment Safety**: Prevent payment system regressions through automated testing
- **Development Velocity**: 70% faster deployment cycles with automated pipelines  
- **Quality Assurance**: Comprehensive test suite execution before production deployment
- **Risk Reduction**: Automated rollback capabilities for failed deployments

## Acceptance Criteria

### ✅ Primary Criteria
- [ ] **AC-030.1**: GitHub Actions workflow integrating all payment QA test suites from `TESTING_QUALITY_ASSURANCE_COMPLETE.md`
- [ ] **AC-030.2**: Automated deployment to staging environment with full payment system testing
- [ ] **AC-030.3**: Production deployment pipeline with manual approval gates and automated rollback
- [ ] **AC-030.4**: Integration with existing test runner `tests/run_payment_qa_tests.py`
- [ ] **AC-030.5**: Environment-specific configuration management for staging and production

### 🔧 Technical Criteria
- [ ] **AC-030.6**: Database migration automation with rollback capabilities
- [ ] **AC-030.7**: ECPay configuration validation and connection testing in pipelines
- [ ] **AC-030.8**: Secrets management for API keys, database URLs, and webhook tokens
- [ ] **AC-030.9**: Performance testing integration with load testing and response time validation
- [ ] **AC-030.10**: Docker container builds with multi-stage optimization

### 📊 Quality Criteria
- [ ] **AC-030.11**: 100% test suite execution in CI pipeline with failure blocking deployment
- [ ] **AC-030.12**: Code coverage reporting with minimum 85% threshold enforcement
- [ ] **AC-030.13**: Security scanning for dependencies and container images

## UI/UX Requirements

### GitHub Actions Dashboard Integration
```
┌─────────────────────────────────────────────────────────┐
│ Payment System CI/CD Pipeline Status                   │
├─────────────────────────────────────────────────────────┤
│ Branch: feature/payment-updates                        │
│ ┌─ Test Suite Status ─────────────────────────────────┐ │
│ │ ✅ E2E Payment Tests         (2m 34s)              │ │
│ │ ✅ Regression Tests          (1m 12s)              │ │
│ │ ✅ Browser Compatibility     (4m 01s)              │ │
│ │ ✅ Webhook Integration       (1m 45s)              │ │
│ │ ✅ Monitoring Tests          (0m 58s)              │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ ┌─ Deployment Pipeline ───────────────────────────────┐ │
│ │ ✅ Build & Test     → ✅ Staging Deploy → 🔄 Prod   │ │
│ │                                           [Approve] │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Quality Gates:                                          │
│ • Code Coverage: 92.3% ✅ (target: 85%)               │
│ • Security Scan: No vulnerabilities ✅                 │
│ • Performance: API <500ms ✅                          │
│ • ECPay Connection: Validated ✅                       │
└─────────────────────────────────────────────────────────┘
```

### Deployment Dashboard
```
┌─────────────────────────────────────────────────────────┐
│ Production Deployment Management                        │
├─────────────────────────────────────────────────────────┤
│ Current Deployment:                                     │
│ Version: v2.1.3 | Deployed: 2025-08-30 14:23 UTC     │
│ Status: ✅ Healthy | Rollback Available: [v2.1.2]     │
├─────────────────────────────────────────────────────────┤
│ Pending Deployment:                                     │
│ Version: v2.1.4-rc.1 | Branch: feature/admin-dash     │
│ ┌─ Pre-deployment Checks ─────────────────────────────┐ │
│ │ ✅ All tests passing                                │ │
│ │ ✅ Staging validation complete                      │ │
│ │ ✅ Database migrations prepared                     │ │
│ │ ✅ ECPay configuration verified                     │ │
│ │ ⏳ Manual approval pending                          │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Actions: [Deploy to Production] [Schedule Deploy]      │
│         [View Changes] [Rollback Plan] [Cancel]       │
└─────────────────────────────────────────────────────────┘
```

### Deployment Monitoring Interface
```
┌─────────────────────────────────────────────────────────┐
│ Live Deployment Monitoring                              │
├─────────────────────────────────────────────────────────┤
│ Deployment: v2.1.4 → Production (In Progress)          │
│ Started: 2025-08-30 16:45 UTC | ETA: 16:52 UTC        │
├─────────────────────────────────────────────────────────┤
│ Progress:                                               │
│ ✅ Database Migration    (1/3)                         │
│ 🔄 Application Deploy   (2/3) [████████░░] 80%        │
│ ⏳ Health Check         (3/3)                         │
├─────────────────────────────────────────────────────────┤
│ Health Metrics (Live):                                 │
│ • Payment Success Rate: 98.7% ✅                      │
│ • API Response Time: 234ms ✅                         │
│ • Error Rate: 0.1% ✅                                 │
│ • Database Connections: 78/100 ✅                     │
├─────────────────────────────────────────────────────────┤
│ [Emergency Rollback] [View Logs] [Monitor Dashboard]   │
└─────────────────────────────────────────────────────────┘
```

## Technical Implementation

### GitHub Actions Workflow Configuration
```yaml
# .github/workflows/payment-system-ci.yml
name: Payment System CI/CD

on:
  pull_request:
    paths:
      - 'src/coaching_assistant/api/v1/subscriptions/**'
      - 'src/coaching_assistant/core/services/payment/**'
      - 'apps/web/components/billing/**'
      - 'tests/e2e/test_payment_**'
  push:
    branches: [main, develop]
    
env:
  NODE_VERSION: '18'
  PYTHON_VERSION: '3.11'
  
jobs:
  test-payment-system:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: coaching_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
          
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
        
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        
    - name: Install Frontend dependencies
      run: |
        cd apps/web
        npm ci
        
    - name: Run Payment QA Test Suite
      env:
        DATABASE_URL: postgresql://postgres:test_password@localhost/coaching_test
        REDIS_URL: redis://localhost:6379
        ECPAY_MERCHANT_ID: ${{ secrets.ECPAY_TEST_MERCHANT_ID }}
        ECPAY_HASH_KEY: ${{ secrets.ECPAY_TEST_HASH_KEY }}
        ADMIN_WEBHOOK_TOKEN: ${{ secrets.ADMIN_WEBHOOK_TOKEN }}
      run: |
        # Run comprehensive payment test suite
        python tests/run_payment_qa_tests.py --suite all --coverage --report
        
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: payment-test-results
        path: |
          htmlcov/
          test-reports/
          
    - name: Comment Test Results on PR
      uses: marocchino/sticky-pull-request-comment@v2
      if: github.event_name == 'pull_request'
      with:
        message: |
          ## 🧪 Payment System Test Results
          
          **Test Suite Status**: ${{ job.status == 'success' && '✅ All tests passed' || '❌ Some tests failed' }}
          
          **Coverage**: See detailed report in artifacts
          
          **Test Categories**:
          - E2E Payment Tests
          - Regression Tests  
          - Browser Compatibility Tests
          - Webhook Integration Tests
          - Monitoring & Performance Tests

  deploy-staging:
    needs: test-payment-system
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to Staging
      env:
        STAGING_DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
        STAGING_DEPLOY_KEY: ${{ secrets.STAGING_DEPLOY_KEY }}
      run: |
        # Deploy to staging environment
        ./scripts/deploy-staging.sh
        
    - name: Run Post-deployment Tests
      env:
        STAGING_API_URL: ${{ secrets.STAGING_API_URL }}
      run: |
        # Verify staging deployment
        python tests/integration/test_staging_deployment.py
        
  deploy-production:
    needs: [test-payment-system, deploy-staging]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Production Pre-deployment Checks
      env:
        PROD_DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}
        ECPAY_PROD_MERCHANT_ID: ${{ secrets.ECPAY_PROD_MERCHANT_ID }}
      run: |
        # Validate production configuration
        ./scripts/validate-prod-config.sh
        
    - name: Database Migration (Dry Run)
      run: |
        # Test database migrations
        alembic upgrade head --sql > migration.sql
        echo "Migration SQL generated successfully"
        
    - name: Deploy to Production
      env:
        PROD_DEPLOY_KEY: ${{ secrets.PROD_DEPLOY_KEY }}
      run: |
        # Production deployment with rollback capability
        ./scripts/deploy-production.sh
        
    - name: Post-deployment Health Check
      run: |
        # Verify production deployment health
        python tests/monitoring/test_production_health.py
```

### Deployment Scripts
```bash
#!/bin/bash
# scripts/deploy-production.sh

set -e

echo "🚀 Starting production deployment..."

# Pre-deployment backup
echo "📦 Creating deployment backup..."
./scripts/backup-production.sh

# Database migration
echo "🗄️ Running database migrations..."
alembic upgrade head

# Deploy application
echo "🔧 Deploying application..."
docker-compose -f docker-compose.prod.yml up -d --build

# Health check with retry
echo "🏥 Performing health checks..."
for i in {1..10}; do
  if curl -f http://localhost:8000/health; then
    echo "✅ Health check passed"
    break
  else
    echo "⏳ Health check failed, retrying in 10s..."
    sleep 10
  fi
  
  if [ $i -eq 10 ]; then
    echo "❌ Health checks failed, rolling back..."
    ./scripts/rollback-production.sh
    exit 1
  fi
done

# Payment system validation
echo "💳 Validating payment system..."
python scripts/validate-payment-system.py

# Success notification
echo "🎉 Deployment completed successfully!"
./scripts/notify-deployment-success.sh
```

### Database Migration Automation
```python
# scripts/automated_migration.py
"""Automated database migration with rollback capabilities"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

class AutomatedMigration:
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.backup_name = f"pre_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def create_backup(self) -> bool:
        """Create database backup before migration"""
        try:
            subprocess.run([
                "pg_dump", 
                "--no-owner", 
                "--clean",
                "--create",
                "-f", f"backups/{self.backup_name}.sql",
                os.environ["DATABASE_URL"]
            ], check=True)
            print(f"✅ Database backup created: {self.backup_name}.sql")
            return True
        except subprocess.CalledProcessError:
            print("❌ Database backup failed")
            return False
    
    def run_migration(self) -> bool:
        """Execute database migration"""
        try:
            # Dry run first
            result = subprocess.run([
                "alembic", "upgrade", "head", "--sql"
            ], capture_output=True, text=True, check=True)
            
            print(f"Migration SQL preview:\n{result.stdout[:500]}...")
            
            # Actual migration
            subprocess.run(["alembic", "upgrade", "head"], check=True)
            print("✅ Database migration completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Migration failed: {e}")
            return False
    
    def validate_migration(self) -> bool:
        """Validate migration success"""
        try:
            # Run basic health checks
            subprocess.run([
                "python", "-c", 
                "from src.coaching_assistant.core.database import engine; "
                "engine.connect().execute('SELECT 1')"
            ], check=True)
            print("✅ Migration validation passed")
            return True
        except subprocess.CalledProcessError:
            print("❌ Migration validation failed")
            return False
    
    def rollback_if_needed(self) -> bool:
        """Rollback migration if validation fails"""
        print(f"🔄 Rolling back to backup: {self.backup_name}")
        try:
            subprocess.run([
                "psql", 
                os.environ["DATABASE_URL"],
                "-f", f"backups/{self.backup_name}.sql"
            ], check=True)
            print("✅ Rollback completed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Rollback failed - manual intervention required")
            return False

if __name__ == "__main__":
    migration = AutomatedMigration()
    
    # Execute migration with safety checks
    if not migration.create_backup():
        sys.exit(1)
    
    if not migration.run_migration():
        sys.exit(1)
        
    if not migration.validate_migration():
        migration.rollback_if_needed()
        sys.exit(1)
    
    print("🎉 Migration completed successfully!")
```

### Environment Configuration Management
```python
# scripts/environment_config.py
"""Environment-specific configuration validation"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class EnvironmentConfig:
    name: str
    required_vars: List[str]
    optional_vars: List[str]
    validation_rules: Dict[str, Any]

class ConfigurationManager:
    def __init__(self):
        self.environments = {
            "staging": EnvironmentConfig(
                name="staging",
                required_vars=[
                    "DATABASE_URL",
                    "REDIS_URL", 
                    "ECPAY_MERCHANT_ID",
                    "ECPAY_HASH_KEY",
                    "ADMIN_WEBHOOK_TOKEN"
                ],
                optional_vars=[
                    "SENTRY_DSN",
                    "LOG_LEVEL"
                ],
                validation_rules={
                    "ECPAY_MERCHANT_ID": lambda x: x.startswith("3002"),
                    "DATABASE_URL": lambda x: "staging" in x
                }
            ),
            "production": EnvironmentConfig(
                name="production",
                required_vars=[
                    "DATABASE_URL",
                    "REDIS_URL",
                    "ECPAY_MERCHANT_ID", 
                    "ECPAY_HASH_KEY",
                    "ECPAY_HASH_IV",
                    "ADMIN_WEBHOOK_TOKEN",
                    "SENTRY_DSN"
                ],
                optional_vars=[
                    "BACKUP_SCHEDULE",
                    "ALERT_WEBHOOK_URL"
                ],
                validation_rules={
                    "ECPAY_MERCHANT_ID": lambda x: not x.startswith("3002"),
                    "DATABASE_URL": lambda x: "production" in x or "render.com" in x
                }
            )
        }
    
    def validate_environment(self, env_name: str) -> bool:
        """Validate environment configuration"""
        config = self.environments.get(env_name)
        if not config:
            print(f"❌ Unknown environment: {env_name}")
            return False
        
        # Check required variables
        missing_vars = []
        for var in config.required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing required variables: {missing_vars}")
            return False
        
        # Validate configuration rules
        for var, rule in config.validation_rules.items():
            value = os.environ.get(var)
            if value and not rule(value):
                print(f"❌ Invalid configuration for {var}")
                return False
        
        print(f"✅ Environment {env_name} configuration valid")
        return True
    
    def setup_environment(self, env_name: str):
        """Setup environment-specific configuration"""
        if not self.validate_environment(env_name):
            raise ValueError(f"Invalid environment configuration: {env_name}")
        
        # Environment-specific setup
        if env_name == "production":
            os.environ["LOG_LEVEL"] = "INFO"
            os.environ["DEBUG"] = "false"
        elif env_name == "staging":  
            os.environ["LOG_LEVEL"] = "DEBUG"
            os.environ["DEBUG"] = "true"
```

## Success Metrics

### Deployment Efficiency KPIs
- **Deployment Frequency**: 5+ successful deployments per week
- **Deployment Time**: <10 minutes from approval to live
- **Pipeline Success Rate**: >95% pipeline success rate
- **Rollback Time**: <2 minutes emergency rollback capability

### Quality Assurance KPIs  
- **Test Coverage**: 85%+ code coverage maintained in CI
- **Test Execution Time**: Complete test suite runs in <15 minutes
- **Failed Deployment Rate**: <2% deployments require rollback
- **Security Scan**: 0 critical vulnerabilities in production deployments

### Business Impact KPIs
- **Development Velocity**: 70% faster release cycles
- **Bug Prevention**: 90% reduction in production payment issues
- **Developer Productivity**: 60% less time spent on deployment tasks
- **Customer Impact**: <0.1% of users affected by deployment issues

## Dependencies
- ✅ Existing payment test suite (`TESTING_QUALITY_ASSURANCE_COMPLETE.md`)
- ✅ Payment system implementation and database schema
- ✅ ECPay integration and configuration
- ⏳ Production environment setup and access
- ⏳ Secrets management infrastructure

## Risk Mitigation
- **Deployment Failure**: Automated rollback with database restoration
- **Configuration Errors**: Environment validation and configuration testing
- **Service Disruption**: Blue-green deployment strategy with health checks
- **Data Loss**: Automated backups before each deployment

## Implementation Phases

### Phase 1: CI Pipeline Setup (Week 1)
- GitHub Actions workflow configuration
- Integration with existing test suite
- Basic deployment to staging environment
- Secrets management setup

### Phase 2: Production Deployment (Week 2)
- Production deployment pipeline with manual approval
- Database migration automation
- Health check and rollback mechanisms
- Environment configuration management

### Phase 3: Advanced Features (Week 3)
- Blue-green deployment strategy
- Performance testing integration
- Automated notifications and reporting
- Deployment monitoring dashboard

## Definition of Done
- [ ] GitHub Actions workflow integrating all payment QA test suites
- [ ] Automated staging deployment with comprehensive testing
- [ ] Production deployment pipeline with manual approval gates
- [ ] Database migration automation with rollback capabilities
- [ ] ECPay configuration validation in deployment pipelines
- [ ] Environment-specific configuration management working
- [ ] Secrets management for all API keys and tokens
- [ ] Performance testing integration with response time validation
- [ ] 100% test suite execution blocking failed deployments
- [ ] Code coverage reporting with 85% minimum threshold
- [ ] Security scanning for dependencies and containers
- [ ] Automated rollback capabilities tested and verified
- [ ] Deployment monitoring with health checks and alerts
- [ ] Documentation for deployment processes and troubleshooting
- [ ] Pipeline tested with successful production deployment

---

**Implementation Priority**: Critical - Essential for safe production deployments
**Estimated Development Time**: 2-3 weeks with DevOps and testing coordination
**Testing Requirements**: End-to-end deployment testing and rollback verification