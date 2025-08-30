# User Story 031: Production Operations & Management

## Story Overview
**Epic**: Administrative Management & Analytics
**Story ID**: US-031
**Priority**: High (Phase 2)
**Effort**: 13 Story Points

## User Story
**As a system operations team, I want comprehensive production operations management tools so that I can maintain system reliability, perform maintenance tasks, and ensure business continuity.**

## Business Value
- **System Reliability**: Maintain 99.9% uptime through proactive operations management
- **Business Continuity**: Disaster recovery capabilities protecting revenue and user data
- **Operational Efficiency**: 60% reduction in manual maintenance tasks through automation
- **Compliance**: Meet data retention and security requirements for SaaS operations

## Acceptance Criteria

### ✅ Primary Criteria
- [ ] **AC-031.1**: Automated backup and recovery system for database and critical application data
- [ ] **AC-031.2**: System maintenance tools with scheduled maintenance windows and user notifications
- [ ] **AC-031.3**: Scaling configuration and load management for high-traffic periods
- [ ] **AC-031.4**: Data retention policy implementation with automated cleanup processes
- [ ] **AC-031.5**: Security audit and compliance reporting tools

### 🔧 Technical Criteria
- [ ] **AC-031.6**: Infrastructure as code with Terraform or similar tools
- [ ] **AC-031.7**: Container orchestration with Docker Compose or Kubernetes
- [ ] **AC-031.8**: Log aggregation and analysis system for troubleshooting
- [ ] **AC-031.9**: Performance optimization tools and resource monitoring
- [ ] **AC-031.10**: Emergency response procedures and incident management

### 📊 Quality Criteria
- [ ] **AC-031.11**: Backup integrity verification and recovery testing (monthly)
- [ ] **AC-031.12**: Disaster recovery procedures tested and documented (quarterly)
- [ ] **AC-031.13**: Security compliance audit trail with automated reporting

## UI/UX Requirements

### Operations Dashboard
```
┌─────────────────────────────────────────────────────────┐
│ Production Operations Management                        │
├─────────────────────────────────────────────────────────┤
│ System Status: 🟢 All Systems Operational              │
│ Last Maintenance: 2025-08-25 02:00 UTC | Next: 09-01  │
├─────────────────────────────────────────────────────────┤
│ Quick Actions:                                          │
│ [Schedule Maintenance] [Backup Now] [Scale Resources]  │
│ [View Logs] [Security Audit] [Emergency Procedures]   │
├─────────────────────────────────────────────────────────┤
│ Resource Usage (Live):                                 │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│ │CPU Usage    │ │Memory Usage │ │Disk Space   │        │
│ │ 🟡 68%      │ │ 🟢 45%      │ │ 🟢 23%      │        │
│ └─────────────┘ └─────────────┘ └─────────────┘        │
├─────────────────────────────────────────────────────────┤
│ Backup Status:                                          │
│ • Database: ✅ Completed 4h ago (847 MB)              │
│ • Application Files: ✅ Completed 4h ago (1.2 GB)    │
│ • User Uploads: ✅ Completed 12h ago (15.6 GB)       │
│ • Config & Secrets: ✅ Completed 4h ago (12 MB)      │
└─────────────────────────────────────────────────────────┘
```

### Maintenance Management Interface
```
┌─────────────────────────────────────────────────────────┐
│ Maintenance Window Management                           │
├─────────────────────────────────────────────────────────┤
│ Scheduled Maintenance:                                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Database Optimization & Index Rebuild              │ │
│ │ Scheduled: 2025-09-01 02:00 UTC (6h from now)      │ │
│ │ Duration: ~45 minutes | Impact: Read-only mode     │ │
│ │ [Edit] [Cancel] [Notify Users] [Start Early]       │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Maintenance History:                                    │
│ • 2025-08-25: Database backup & cleanup (✅ Success)   │
│ • 2025-08-20: Security patches applied (✅ Success)    │
│ • 2025-08-15: Certificate renewal (✅ Success)         │
├─────────────────────────────────────────────────────────┤
│ Emergency Maintenance:                                  │
│ [Critical Security Patch] [Emergency Rollback]         │
│ [Service Restart] [Database Recovery] [Scale Down]     │
└─────────────────────────────────────────────────────────┘
```

### Disaster Recovery Dashboard
```
┌─────────────────────────────────────────────────────────┐
│ Disaster Recovery & Business Continuity               │
├─────────────────────────────────────────────────────────┤
│ Recovery Point Objective (RPO): 4 hours               │
│ Recovery Time Objective (RTO): 2 hours                │
├─────────────────────────────────────────────────────────┤
│ Backup Locations:                                      │
│ ┌─ Primary Backup (AWS S3) ──────────────── 🟢 Healthy│
│ ├─ Secondary Backup (GCP Storage) ────────── 🟢 Healthy│
│ └─ Local Backup (NAS) ──────────────────── 🟡 Warning │
├─────────────────────────────────────────────────────────┤
│ Recovery Procedures:                                    │
│ • Database Recovery: [Test] [Execute] [Documentation]  │
│ • Application Recovery: [Test] [Execute] [Docs]        │
│ • Full System Recovery: [Test] [Execute] [Runbook]     │
├─────────────────────────────────────────────────────────┤
│ Last Recovery Test: 2025-08-15 (✅ Successful)        │
│ Next Scheduled Test: 2025-09-15                       │
│ [Schedule Test] [View Test Reports] [Update Procedures]│
└─────────────────────────────────────────────────────────┘
```

## Technical Implementation

### Backup and Recovery System
```python
# scripts/backup_manager.py
"""Comprehensive backup and recovery management system"""

import os
import subprocess
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class BackupConfig:
    name: str
    source_path: str
    destination: str
    retention_days: int
    compression: bool = True
    encryption: bool = True

class BackupManager:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.backup_configs = [
            BackupConfig(
                name="database",
                source_path="DATABASE_URL",
                destination="s3://coaching-backups/database/",
                retention_days=30
            ),
            BackupConfig(
                name="application_files", 
                source_path="/app/src/",
                destination="s3://coaching-backups/application/",
                retention_days=7
            ),
            BackupConfig(
                name="user_uploads",
                source_path="/app/uploads/",
                destination="s3://coaching-backups/uploads/",
                retention_days=90
            )
        ]
    
    def create_database_backup(self) -> Dict[str, Any]:
        """Create encrypted database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"database_backup_{timestamp}.sql.gz"
        
        try:
            # Create database dump
            subprocess.run([
                'pg_dump',
                '--no-owner',
                '--clean', 
                '--create',
                '--compress=9',
                '-f', f'/tmp/{backup_filename}',
                os.environ['DATABASE_URL']
            ], check=True)
            
            # Encrypt backup
            subprocess.run([
                'gpg', '--symmetric',
                '--cipher-algo', 'AES256',
                '--compress-algo', 'zip',
                '--output', f'/tmp/{backup_filename}.gpg',
                f'/tmp/{backup_filename}'
            ], check=True)
            
            # Upload to S3
            self.s3_client.upload_file(
                f'/tmp/{backup_filename}.gpg',
                'coaching-backups',
                f'database/{backup_filename}.gpg'
            )
            
            return {
                'status': 'success',
                'filename': backup_filename,
                'size_mb': os.path.getsize(f'/tmp/{backup_filename}.gpg') / 1024 / 1024,
                'timestamp': datetime.now().isoformat()
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_recovery(self, backup_name: str) -> bool:
        """Test backup recovery to staging environment"""
        try:
            # Download backup
            local_file = f'/tmp/recovery_test_{backup_name}'
            self.s3_client.download_file(
                'coaching-backups',
                f'database/{backup_name}',
                local_file
            )
            
            # Test restore to staging database
            staging_db_url = os.environ['STAGING_DATABASE_URL']
            subprocess.run([
                'psql',
                staging_db_url,
                '-f', local_file
            ], check=True)
            
            # Verify data integrity
            subprocess.run([
                'python', 'scripts/verify_database_integrity.py',
                '--database-url', staging_db_url
            ], check=True)
            
            return True
            
        except Exception as e:
            print(f"Recovery test failed: {e}")
            return False
    
    def cleanup_old_backups(self, retention_days: int = 30):
        """Remove backups older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        response = self.s3_client.list_objects_v2(
            Bucket='coaching-backups',
            Prefix='database/'
        )
        
        for obj in response.get('Contents', []):
            if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                self.s3_client.delete_object(
                    Bucket='coaching-backups',
                    Key=obj['Key']
                )
                print(f"Deleted old backup: {obj['Key']}")

# Maintenance window management
class MaintenanceManager:
    def __init__(self):
        self.notification_service = NotificationService()
    
    def schedule_maintenance(self, 
                           start_time: datetime,
                           duration_minutes: int,
                           description: str,
                           impact_level: str = "low") -> str:
        """Schedule maintenance window with user notifications"""
        
        maintenance_id = f"maint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Store maintenance schedule
        maintenance_record = {
            'id': maintenance_id,
            'start_time': start_time.isoformat(),
            'duration_minutes': duration_minutes,
            'description': description,
            'impact_level': impact_level,
            'status': 'scheduled'
        }
        
        # Store in database
        self.store_maintenance_record(maintenance_record)
        
        # Schedule notification
        notification_time = start_time - timedelta(hours=24)
        self.notification_service.schedule_notification(
            notification_time,
            f"Scheduled maintenance: {description}",
            f"System maintenance scheduled for {start_time.strftime('%Y-%m-%d %H:%M')} UTC"
        )
        
        return maintenance_id
    
    def enter_maintenance_mode(self, maintenance_id: str):
        """Put system into maintenance mode"""
        # Update load balancer to show maintenance page
        # Stop non-critical services
        # Set system status flags
        
        subprocess.run([
            'docker-compose', '-f', 'docker-compose.prod.yml',
            'up', '-d', 'maintenance-page'
        ])
        
        # Update maintenance status
        self.update_maintenance_status(maintenance_id, 'active')
    
    def exit_maintenance_mode(self, maintenance_id: str):
        """Exit maintenance mode and restore services"""
        # Restore normal services
        subprocess.run([
            'docker-compose', '-f', 'docker-compose.prod.yml',
            'up', '-d'
        ])
        
        # Health checks
        if self.verify_system_health():
            self.update_maintenance_status(maintenance_id, 'completed')
        else:
            self.handle_maintenance_failure(maintenance_id)
```

### Infrastructure as Code
```hcl
# terraform/main.tf
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Database instance with automated backups
resource "google_sql_database_instance" "coaching_db" {
  name             = "coaching-assistant-db"
  database_version = "POSTGRES_15"
  region           = var.region
  
  settings {
    tier = var.database_tier
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 30
        retention_unit   = "COUNT"
      }
    }
    
    maintenance_window {
      day          = 7  # Sunday
      hour         = 4  # 4 AM UTC
      update_track = "stable"
    }
    
    disk_autoresize       = true
    disk_autoresize_limit = 500
    
    insights_config {
      query_insights_enabled  = true
      record_application_tags = true
      record_client_address   = true
    }
  }
  
  deletion_protection = true
}

# Redis instance for caching and session storage
resource "google_redis_instance" "coaching_cache" {
  name           = "coaching-cache"
  memory_size_gb = var.redis_memory_gb
  region         = var.region
  
  redis_version     = "REDIS_7_0"
  display_name      = "Coaching Assistant Cache"
  
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 4
        minutes = 0
      }
    }
  }
}

# Load balancer for high availability
resource "google_compute_global_address" "coaching_ip" {
  name = "coaching-assistant-ip"
}

resource "google_compute_global_forwarding_rule" "coaching_https" {
  name                  = "coaching-assistant-https"
  target                = google_compute_target_https_proxy.coaching_proxy.id
  port_range            = "443"
  ip_address            = google_compute_global_address.coaching_ip.address
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

# Auto-scaling compute instances
resource "google_compute_instance_template" "coaching_template" {
  name_prefix  = "coaching-assistant-"
  machine_type = var.instance_type
  
  disk {
    source_image = "projects/cos-cloud/global/images/family/cos-stable"
    auto_delete  = true
    boot         = true
    disk_type    = "pd-ssd"
    disk_size_gb = 50
  }
  
  network_interface {
    network = "default"
    access_config {}
  }
  
  metadata_startup_script = file("scripts/startup.sh")
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_region_instance_group_manager" "coaching_group" {
  name               = "coaching-assistant-group"
  base_instance_name = "coaching-assistant"
  region             = var.region
  
  version {
    instance_template = google_compute_instance_template.coaching_template.id
  }
  
  auto_healing_policies {
    health_check      = google_compute_health_check.coaching_health.id
    initial_delay_sec = 300
  }
}

# Auto-scaling policy
resource "google_compute_region_autoscaler" "coaching_autoscaler" {
  name   = "coaching-assistant-autoscaler"
  region = var.region
  target = google_compute_region_instance_group_manager.coaching_group.id
  
  autoscaling_policy {
    min_replicas    = var.min_instances
    max_replicas    = var.max_instances
    cooldown_period = 300
    
    cpu_utilization {
      target = 0.7
    }
    
    metric {
      name   = "custom.googleapis.com/payment_queue_size"
      target = 10
      type   = "GAUGE"
    }
  }
}
```

### Monitoring and Logging Infrastructure
```python
# scripts/system_monitor.py
"""Comprehensive system monitoring and alerting"""

import psutil
import docker
import logging
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class SystemHealth:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_connections: int
    service_status: Dict[str, str]

class SystemMonitor:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.logger = logging.getLogger(__name__)
        
    def collect_system_metrics(self) -> SystemHealth:
        """Collect comprehensive system health metrics"""
        
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network connections
        connections = len(psutil.net_connections())
        
        # Service status
        service_status = {}
        try:
            containers = self.docker_client.containers.list()
            for container in containers:
                service_status[container.name] = container.status
        except Exception as e:
            self.logger.error(f"Failed to get container status: {e}")
        
        return SystemHealth(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            active_connections=connections,
            service_status=service_status
        )
    
    def check_service_health(self) -> Dict[str, Any]:
        """Check health of critical services"""
        health_status = {}
        
        # Database connectivity
        try:
            from src.coaching_assistant.core.database import engine
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            health_status['database'] = 'healthy'
        except Exception as e:
            health_status['database'] = f'unhealthy: {e}'
        
        # Redis connectivity
        try:
            import redis
            r = redis.from_url(os.environ['REDIS_URL'])
            r.ping()
            health_status['redis'] = 'healthy'
        except Exception as e:
            health_status['redis'] = f'unhealthy: {e}'
        
        # ECPay connectivity
        try:
            import requests
            response = requests.get('https://payment-stage.ecpay.com.tw/Cashier/QueryTradeInfo/V5', timeout=10)
            if response.status_code == 200:
                health_status['ecpay'] = 'healthy'
            else:
                health_status['ecpay'] = f'unhealthy: HTTP {response.status_code}'
        except Exception as e:
            health_status['ecpay'] = f'unhealthy: {e}'
        
        return health_status
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        metrics = self.collect_system_metrics()
        services = self.check_service_health()
        
        # Determine overall health
        critical_issues = []
        if metrics.cpu_percent > 90:
            critical_issues.append("High CPU usage")
        if metrics.memory_percent > 85:
            critical_issues.append("High memory usage")
        if metrics.disk_percent > 80:
            critical_issues.append("Low disk space")
        
        unhealthy_services = [k for k, v in services.items() if 'unhealthy' in v]
        if unhealthy_services:
            critical_issues.extend([f"Service down: {s}" for s in unhealthy_services])
        
        overall_status = "critical" if critical_issues else "healthy"
        
        return {
            'overall_status': overall_status,
            'timestamp': metrics.timestamp.isoformat(),
            'system_metrics': {
                'cpu_percent': metrics.cpu_percent,
                'memory_percent': metrics.memory_percent,
                'disk_percent': metrics.disk_percent,
                'active_connections': metrics.active_connections
            },
            'service_status': services,
            'critical_issues': critical_issues
        }
```

## Success Metrics

### Operational Excellence KPIs
- **System Uptime**: 99.9% availability maintained
- **Backup Success Rate**: 100% successful automated backups
- **Recovery Time**: <2 hours for full system recovery (RTO)
- **Data Loss**: <4 hours maximum data loss (RPO)

### Maintenance Efficiency KPIs
- **Maintenance Window Compliance**: 95% maintenance completed within scheduled windows
- **Automated Task Success**: 90% maintenance tasks automated
- **Mean Time to Repair**: <30 minutes for common issues
- **Emergency Response Time**: <15 minutes for critical incidents

### Business Continuity KPIs
- **Disaster Recovery Test Success**: 100% successful quarterly DR tests
- **Security Compliance**: 100% compliance with data retention policies
- **Incident Resolution**: 95% incidents resolved without customer impact
- **Cost Optimization**: 20% reduction in operational costs through automation

## Dependencies
- ✅ Production environment infrastructure
- ✅ Database and application deployment
- ⏳ Cloud provider accounts and permissions
- ⏳ Backup storage and disaster recovery infrastructure
- ⏳ Monitoring and alerting tools integration

## Risk Mitigation
- **Data Loss Risk**: Multi-location backups with encryption and integrity verification
- **Service Disruption Risk**: Auto-scaling and health checks with automatic recovery
- **Security Risk**: Regular security audits and compliance monitoring
- **Human Error Risk**: Automated procedures with approval gates for critical operations

## Implementation Phases

### Phase 1: Core Operations (Week 1)
- Backup and recovery system implementation
- Basic monitoring and health checks
- Infrastructure as code setup
- Emergency procedures documentation

### Phase 2: Automation & Scaling (Week 2)
- Maintenance window automation
- Auto-scaling configuration
- Log aggregation and analysis
- Performance optimization tools

### Phase 3: Advanced Operations (Week 3)
- Disaster recovery testing
- Security audit automation
- Advanced monitoring and alerting
- Business continuity procedures

## Definition of Done
- [ ] Automated backup system creating daily encrypted backups
- [ ] Recovery procedures tested and documented with <2 hour RTO
- [ ] Maintenance tools with scheduling and user notification
- [ ] Auto-scaling configuration handling traffic spikes
- [ ] Data retention policies with automated cleanup
- [ ] Infrastructure as code managing all resources
- [ ] Log aggregation system for troubleshooting
- [ ] Security audit tools with compliance reporting
- [ ] Emergency response procedures documented and tested
- [ ] Backup integrity verification running monthly
- [ ] Disaster recovery procedures tested quarterly
- [ ] Performance monitoring with resource optimization
- [ ] Documentation for all operational procedures
- [ ] Team training on all operational tools and procedures

---

**Implementation Priority**: High - Critical for production system reliability
**Estimated Development Time**: 3-4 weeks with infrastructure and operations focus
**Testing Requirements**: Disaster recovery testing, backup restoration, and failover procedures