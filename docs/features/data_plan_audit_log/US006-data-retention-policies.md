# US006: Data Retention Policies

## 📋 User Story

**As a** data protection officer and business stakeholder  
**I want** automated data retention policies with configurable rules for different data types  
**So that** we maintain compliance with legal requirements while optimizing storage costs and protecting user privacy

## 💼 Business Value

### Current Problem
- Manual data retention processes are error-prone and time-consuming
- No automated lifecycle management for different types of data (personal, usage, system logs)
- Risk of retaining personal data longer than legally required (GDPR violations)
- Storage costs increase unnecessarily due to lack of automated cleanup

### Business Impact
- **Compliance Risk**: GDPR Article 5 requires data minimization and storage limitation
- **Storage Costs**: Unnecessary data retention increases infrastructure costs
- **Operational Overhead**: Manual data lifecycle management requires staff resources
- **Legal Liability**: Retaining data beyond legal requirements increases exposure

### Value Delivered
- **Automated Compliance**: Systematic enforcement of data retention requirements
- **Cost Optimization**: Automatic cleanup reduces storage and processing costs  
- **Risk Reduction**: Minimal data retention reduces legal and security exposure
- **Operational Efficiency**: Automated processes eliminate manual intervention

## 🎯 Acceptance Criteria

### Configurable Retention Policies
1. **Data Category Classification**
   - [ ] Different retention periods for personal data, usage analytics, audit logs
   - [ ] Configurable retention policies per data category and jurisdiction
   - [ ] Support for legal hold and litigation preservation requirements
   - [ ] Policy inheritance and override capabilities

2. **Automated Policy Execution**
   - [ ] Daily automated jobs to check and enforce retention policies
   - [ ] Graduated data lifecycle: active → archived → anonymized → deleted
   - [ ] Safe deletion with verification and rollback capabilities
   - [ ] Batch processing for efficient large-scale data operations

3. **Policy Management Interface**
   - [ ] Admin interface to configure and modify retention policies
   - [ ] Policy simulation and impact analysis before implementation
   - [ ] Audit trail for all policy changes and executions
   - [ ] Override capabilities for special circumstances (legal holds)

### Compliance and Safety
4. **GDPR Article 5 Compliance**
   - [ ] Data minimization: automatic removal of unnecessary data
   - [ ] Storage limitation: enforce maximum retention periods
   - [ ] Purpose limitation: different retention for different processing purposes
   - [ ] Transparency: clear documentation of retention practices

5. **Safety Mechanisms**  
   - [ ] Confirmation requirements for permanent deletion operations
   - [ ] Data backup verification before deletion
   - [ ] Recovery mechanisms for accidental policy execution
   - [ ] Comprehensive logging of all retention activities

### Monitoring and Reporting
6. **Retention Monitoring**
   - [ ] Real-time dashboard showing data retention status
   - [ ] Alerts for policy violations or execution failures
   - [ ] Compliance reports for audits and regulatory reviews
   - [ ] Storage optimization reports showing cost savings

## 🏗️ Technical Implementation

### Data Retention Policy Model
```python
# packages/core-logic/src/coaching_assistant/models/data_retention.py

import enum
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import BaseModel

class DataCategory(enum.Enum):
    """Categories of data for retention policies"""
    PERSONAL_IDENTIFIABLE = "personal_identifiable"  # Names, emails, phone numbers
    PERSONAL_SENSITIVE = "personal_sensitive"        # Session content, memos
    USAGE_ANALYTICS = "usage_analytics"              # Usage logs, analytics data
    AUDIT_LOGS = "audit_logs"                       # System audit trails
    SYSTEM_METADATA = "system_metadata"              # IDs, timestamps, technical data
    BUSINESS_RECORDS = "business_records"            # Financial, billing data

class RetentionAction(enum.Enum):
    """Actions that can be taken on data"""
    RETAIN = "retain"           # Keep data as-is
    ARCHIVE = "archive"         # Move to cold storage
    ANONYMIZE = "anonymize"     # Remove personal identifiers
    DELETE = "delete"           # Permanent deletion

class ComplianceRegime(enum.Enum):
    """Legal compliance regimes"""
    GDPR_EU = "gdpr_eu"        # European GDPR
    GDPR_UK = "gdpr_uk"        # UK GDPR
    CCPA_CA = "ccpa_ca"        # California CCPA
    SOX_US = "sox_us"          # Sarbanes-Oxley Act
    GENERAL = "general"        # General business rules

class DataRetentionPolicy(BaseModel):
    """Configurable data retention policies"""
    
    # Policy identification
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Policy scope
    data_category = Column(Enum(DataCategory), nullable=False, index=True)
    compliance_regime = Column(Enum(ComplianceRegime), nullable=False)
    
    # Retention rules
    retention_days = Column(Integer, nullable=False)  # -1 for indefinite
    action_after_retention = Column(Enum(RetentionAction), nullable=False)
    
    # Advanced settings
    grace_period_days = Column(Integer, default=30)  # Extra time before action
    batch_size = Column(Integer, default=1000)       # Records per batch
    
    # Policy status
    is_active = Column(Boolean, default=True, nullable=False)
    requires_confirmation = Column(Boolean, default=True)  # For deletion actions
    
    # Legal and business context
    legal_basis = Column(Text, nullable=True)
    business_justification = Column(Text, nullable=True)
    
    # Execution configuration
    execution_schedule = Column(String(50), default="daily")  # cron-like schedule
    last_executed = Column(DateTime(timezone=True), nullable=True)
    next_execution = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), nullable=False)
    policy_metadata = Column(JSONB, default={})
    
    def __repr__(self):
        return f"<DataRetentionPolicy(name={self.name}, category={self.data_category.value}, days={self.retention_days})>"
    
    @property
    def retention_cutoff_date(self) -> datetime:
        """Calculate cutoff date for retention"""
        if self.retention_days == -1:
            # Indefinite retention
            return datetime.min
        
        return datetime.utcnow() - timedelta(days=self.retention_days)
    
    @property
    def grace_cutoff_date(self) -> datetime:
        """Calculate cutoff date including grace period"""
        if self.retention_days == -1:
            return datetime.min
            
        total_days = self.retention_days + self.grace_period_days
        return datetime.utcnow() - timedelta(days=total_days)
    
    def is_due_for_execution(self) -> bool:
        """Check if policy is due for execution"""
        if not self.is_active:
            return False
            
        if not self.next_execution:
            return True  # Never executed
            
        return datetime.utcnow() >= self.next_execution
    
    def calculate_next_execution(self) -> datetime:
        """Calculate next execution time based on schedule"""
        if self.execution_schedule == "daily":
            return datetime.utcnow() + timedelta(days=1)
        elif self.execution_schedule == "weekly":
            return datetime.utcnow() + timedelta(weeks=1)
        elif self.execution_schedule == "monthly":
            return datetime.utcnow() + timedelta(days=30)
        else:
            return datetime.utcnow() + timedelta(days=1)  # Default to daily

class DataRetentionExecution(BaseModel):
    """Track retention policy executions"""
    
    policy_id = Column(UUID(as_uuid=True), ForeignKey("data_retention_policy.id"), nullable=False)
    
    # Execution details
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(['running', 'completed', 'failed', 'cancelled']), nullable=False)
    
    # Processing statistics
    records_evaluated = Column(Integer, default=0)
    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Results
    actions_taken = Column(JSONB, default={})  # {"deleted": 10, "anonymized": 5}
    error_message = Column(Text, nullable=True)
    execution_log = Column(Text, nullable=True)
    
    # Verification
    verification_checksum = Column(String(64), nullable=True)
    rollback_possible = Column(Boolean, default=False)
    
    # Relationships
    policy = relationship("DataRetentionPolicy", back_populates="executions")
    
    @property
    def execution_duration(self) -> timedelta:
        """Calculate execution duration"""
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return datetime.utcnow() - self.started_at
        return timedelta(0)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of processing"""
        if self.records_evaluated == 0:
            return 0.0
        return (self.records_processed / self.records_evaluated) * 100

# Add relationship
DataRetentionPolicy.executions = relationship("DataRetentionExecution", back_populates="policy")
```

### Data Retention Service
```python
# packages/core-logic/src/coaching_assistant/services/data_retention_service.py

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataRetentionService:
    """Service for automated data retention policy management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def execute_due_policies(self) -> List[DataRetentionExecution]:
        """Execute all policies that are due for execution"""
        
        due_policies = self.db.query(DataRetentionPolicy).filter(
            and_(
                DataRetentionPolicy.is_active == True,
                or_(
                    DataRetentionPolicy.next_execution == None,
                    DataRetentionPolicy.next_execution <= datetime.utcnow()
                )
            )
        ).all()
        
        executions = []
        for policy in due_policies:
            try:
                execution = self.execute_policy(policy)
                executions.append(execution)
                logger.info(f"Executed retention policy '{policy.name}': {execution.status}")
            except Exception as e:
                logger.error(f"Failed to execute retention policy '{policy.name}': {e}")
                
        return executions
    
    def execute_policy(self, policy: DataRetentionPolicy) -> DataRetentionExecution:
        """Execute a specific retention policy"""
        
        # Create execution record
        execution = DataRetentionExecution(
            policy_id=policy.id,
            started_at=datetime.utcnow(),
            status='running'
        )
        self.db.add(execution)
        self.db.commit()
        
        try:
            # Execute policy based on data category
            if policy.data_category == DataCategory.PERSONAL_IDENTIFIABLE:
                result = self._process_personal_identifiable_data(policy, execution)
            elif policy.data_category == DataCategory.PERSONAL_SENSITIVE:
                result = self._process_personal_sensitive_data(policy, execution)
            elif policy.data_category == DataCategory.USAGE_ANALYTICS:
                result = self._process_usage_analytics_data(policy, execution)
            elif policy.data_category == DataCategory.AUDIT_LOGS:
                result = self._process_audit_logs(policy, execution)
            elif policy.data_category == DataCategory.SYSTEM_METADATA:
                result = self._process_system_metadata(policy, execution)
            else:
                raise ValueError(f"Unsupported data category: {policy.data_category}")
            
            # Update execution record
            execution.completed_at = datetime.utcnow()
            execution.status = 'completed'
            execution.records_evaluated = result.get('evaluated', 0)
            execution.records_processed = result.get('processed', 0)
            execution.records_failed = result.get('failed', 0)
            execution.actions_taken = result.get('actions', {})
            execution.execution_log = result.get('log', '')
            
            # Update policy's next execution time
            policy.last_executed = execution.completed_at
            policy.next_execution = policy.calculate_next_execution()
            
            self.db.commit()
            
            # Create audit log for policy execution
            from ..services.audit_service import get_audit_service, AuditEventType
            audit_service = get_audit_service(self.db)
            audit_service.log_system_event(
                event_type=AuditEventType.DATA_RETENTION_POLICY,
                description=f"Executed retention policy '{policy.name}': {execution.records_processed} records processed",
                metadata={
                    'policy_name': policy.name,
                    'records_processed': execution.records_processed,
                    'actions_taken': execution.actions_taken,
                    'execution_duration': str(execution.execution_duration)
                }
            )
            
            return execution
            
        except Exception as e:
            # Update execution record with failure
            execution.completed_at = datetime.utcnow()
            execution.status = 'failed'
            execution.error_message = str(e)
            self.db.commit()
            
            logger.error(f"Retention policy execution failed: {e}")
            raise
    
    def _process_personal_identifiable_data(self, policy: DataRetentionPolicy, execution: DataRetentionExecution) -> Dict:
        """Process personal identifiable data (clients, users)"""
        
        cutoff_date = policy.grace_cutoff_date
        log_messages = []
        actions = {}
        
        # Process clients
        eligible_clients = self.db.query(Client).filter(
            and_(
                Client.created_at < cutoff_date,
                Client.is_anonymized == False,
                Client.is_active == False  # Only process inactive clients
            )
        ).all()
        
        log_messages.append(f"Found {len(eligible_clients)} eligible clients for {policy.action_after_retention.value}")
        
        processed_count = 0
        failed_count = 0
        
        for client in eligible_clients:
            try:
                if policy.action_after_retention == RetentionAction.ANONYMIZE:
                    # Use existing anonymization logic
                    from ..services.gdpr_service import GDPRService
                    gdpr_service = GDPRService(self.db)
                    gdpr_service.process_erasure_request(client.user_id, [client.id])
                    actions['anonymized'] = actions.get('anonymized', 0) + 1
                    
                elif policy.action_after_retention == RetentionAction.DELETE:
                    if client.can_be_hard_deleted():
                        self.db.delete(client)
                        actions['deleted'] = actions.get('deleted', 0) + 1
                    else:
                        log_messages.append(f"Client {client.id} cannot be hard deleted, skipping")
                        continue
                
                processed_count += 1
                
            except Exception as e:
                failed_count += 1
                log_messages.append(f"Failed to process client {client.id}: {e}")
        
        self.db.commit()
        
        return {
            'evaluated': len(eligible_clients),
            'processed': processed_count,
            'failed': failed_count,
            'actions': actions,
            'log': '\n'.join(log_messages)
        }
    
    def _process_usage_analytics_data(self, policy: DataRetentionPolicy, execution: DataRetentionExecution) -> Dict:
        """Process usage analytics data"""
        
        cutoff_date = policy.grace_cutoff_date
        log_messages = []
        actions = {}
        
        if policy.action_after_retention == RetentionAction.RETAIN:
            # Usage analytics are retained indefinitely
            log_messages.append("Usage analytics marked for indefinite retention")
            return {
                'evaluated': 0,
                'processed': 0,
                'failed': 0,
                'actions': actions,
                'log': '\n'.join(log_messages)
            }
        
        elif policy.action_after_retention == RetentionAction.ARCHIVE:
            # Move old usage logs to archive table
            old_usage_logs = self.db.query(UsageLog).filter(
                UsageLog.created_at < cutoff_date
            ).all()
            
            # Create archived records
            for log in old_usage_logs:
                archived_log = ArchivedUsageLog(
                    original_id=log.id,
                    user_id=log.user_id,
                    session_id=log.session_id,
                    duration_minutes=log.duration_minutes,
                    cost_usd=log.cost_usd,
                    stt_provider=log.stt_provider,
                    created_at=log.created_at,
                    archived_at=datetime.utcnow()
                )
                self.db.add(archived_log)
                self.db.delete(log)
            
            actions['archived'] = len(old_usage_logs)
            
        self.db.commit()
        
        return {
            'evaluated': len(old_usage_logs) if 'old_usage_logs' in locals() else 0,
            'processed': actions.get('archived', 0),
            'failed': 0,
            'actions': actions,
            'log': '\n'.join(log_messages)
        }
    
    def _process_audit_logs(self, policy: DataRetentionPolicy, execution: DataRetentionExecution) -> Dict:
        """Process audit logs with extended retention"""
        
        # Audit logs typically have longer retention periods
        cutoff_date = policy.grace_cutoff_date
        log_messages = []
        actions = {}
        
        if policy.action_after_retention == RetentionAction.ARCHIVE:
            old_audit_logs = self.db.query(AuditLog).filter(
                AuditLog.timestamp < cutoff_date
            ).all()
            
            # Archive old audit logs
            archived_count = 0
            for audit_log in old_audit_logs:
                # Move to archive storage (implement based on infrastructure)
                archived_audit = ArchivedAuditLog.from_audit_log(audit_log)
                self.db.add(archived_audit)
                self.db.delete(audit_log)
                archived_count += 1
            
            actions['archived'] = archived_count
            log_messages.append(f"Archived {archived_count} old audit log entries")
        
        self.db.commit()
        
        return {
            'evaluated': len(old_audit_logs) if 'old_audit_logs' in locals() else 0,
            'processed': actions.get('archived', 0),
            'failed': 0,
            'actions': actions,
            'log': '\n'.join(log_messages)
        }

    def simulate_policy_execution(self, policy_id: UUID) -> Dict:
        """Simulate policy execution without making changes"""
        
        policy = self.db.query(DataRetentionPolicy).filter(
            DataRetentionPolicy.id == policy_id
        ).first()
        
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")
        
        cutoff_date = policy.grace_cutoff_date
        
        # Simulate based on data category
        if policy.data_category == DataCategory.PERSONAL_IDENTIFIABLE:
            eligible_clients = self.db.query(Client).filter(
                and_(
                    Client.created_at < cutoff_date,
                    Client.is_anonymized == False,
                    Client.is_active == False
                )
            ).count()
            
            return {
                'policy_name': policy.name,
                'cutoff_date': cutoff_date.isoformat(),
                'estimated_records': eligible_clients,
                'action': policy.action_after_retention.value,
                'impact_summary': f"Would {policy.action_after_retention.value} {eligible_clients} inactive clients"
            }
        
        # Add simulation for other data categories...
        
        return {
            'policy_name': policy.name,
            'cutoff_date': cutoff_date.isoformat(),
            'estimated_records': 0,
            'action': policy.action_after_retention.value,
            'impact_summary': "Simulation not implemented for this data category"
        }

# Archive models for cold storage
class ArchivedUsageLog(BaseModel):
    """Archived usage log entries"""
    original_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    session_id = Column(UUID(as_uuid=True), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    cost_usd = Column(String(10), nullable=True)
    stt_provider = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=False)

class ArchivedAuditLog(BaseModel):
    """Archived audit log entries"""
    original_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    event_type = Column(String(50), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(50), nullable=True)
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=False)
    
    @classmethod
    def from_audit_log(cls, audit_log: AuditLog):
        """Create archived entry from audit log"""
        return cls(
            original_id=audit_log.id,
            event_type=audit_log.event_type.value,
            user_id=audit_log.user_id,
            entity_type=audit_log.entity_type,
            entity_id=audit_log.entity_id,
            description=audit_log.description,
            timestamp=audit_log.timestamp,
            archived_at=datetime.utcnow()
        )
```

### Automated Retention Job
```python
# packages/core-logic/src/coaching_assistant/tasks/retention_tasks.py

from celery import Task
from ..core.celery_app import celery_app
from ..core.database import get_db_session
from ..services.data_retention_service import DataRetentionService
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def execute_data_retention_policies():
    """Daily job to execute due data retention policies"""
    
    logger.info("Starting automated data retention policy execution")
    
    with get_db_session() as db:
        retention_service = DataRetentionService(db)
        
        try:
            executions = retention_service.execute_due_policies()
            
            total_processed = sum(exec.records_processed for exec in executions)
            successful_executions = len([exec for exec in executions if exec.status == 'completed'])
            
            logger.info(
                f"Data retention execution completed: "
                f"{successful_executions}/{len(executions)} policies executed successfully, "
                f"{total_processed} total records processed"
            )
            
            return {
                'policies_executed': len(executions),
                'successful_executions': successful_executions,
                'total_records_processed': total_processed,
                'executions': [
                    {
                        'policy_id': str(exec.policy_id),
                        'status': exec.status,
                        'records_processed': exec.records_processed,
                        'actions_taken': exec.actions_taken
                    }
                    for exec in executions
                ]
            }
            
        except Exception as e:
            logger.error(f"Data retention execution failed: {e}")
            raise

# Schedule daily execution
from celery.schedules import crontab
celery_app.conf.beat_schedule.update({
    'execute-data-retention-policies': {
        'task': 'coaching_assistant.tasks.retention_tasks.execute_data_retention_policies',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2:00 AM
        'options': {'queue': 'retention'}
    }
})
```

### Admin API for Retention Management
```python
# packages/core-logic/src/coaching_assistant/api/admin/data_retention.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from ...services.data_retention_service import DataRetentionService
from ...models.data_retention import DataRetentionPolicy, DataCategory, RetentionAction

router = APIRouter()

@router.get("/policies")
async def list_retention_policies(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all data retention policies"""
    
    policies = db.query(DataRetentionPolicy).order_by(DataRetentionPolicy.name).all()
    
    return {
        "policies": [
            {
                "id": str(policy.id),
                "name": policy.name,
                "description": policy.description,
                "data_category": policy.data_category.value,
                "retention_days": policy.retention_days,
                "action_after_retention": policy.action_after_retention.value,
                "is_active": policy.is_active,
                "last_executed": policy.last_executed.isoformat() if policy.last_executed else None,
                "next_execution": policy.next_execution.isoformat() if policy.next_execution else None
            }
            for policy in policies
        ]
    }

@router.post("/policies")
async def create_retention_policy(
    policy_data: RetentionPolicyCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create new data retention policy"""
    
    # Validate policy configuration
    if policy_data.retention_days < -1:
        raise HTTPException(status_code=400, detail="Retention days must be -1 (indefinite) or positive")
    
    if policy_data.action_after_retention == RetentionAction.DELETE and policy_data.retention_days < 90:
        raise HTTPException(status_code=400, detail="Deletion policies require minimum 90 days retention")
    
    policy = DataRetentionPolicy(
        name=policy_data.name,
        description=policy_data.description,
        data_category=DataCategory(policy_data.data_category),
        compliance_regime=policy_data.compliance_regime,
        retention_days=policy_data.retention_days,
        action_after_retention=RetentionAction(policy_data.action_after_retention),
        grace_period_days=policy_data.grace_period_days or 30,
        legal_basis=policy_data.legal_basis,
        business_justification=policy_data.business_justification,
        created_by=current_user.id,
        next_execution=datetime.utcnow() + timedelta(days=1)  # Start tomorrow
    )
    
    db.add(policy)
    db.commit()
    
    return {
        "message": "Retention policy created successfully",
        "policy_id": str(policy.id)
    }

@router.post("/policies/{policy_id}/simulate")
async def simulate_policy_execution(
    policy_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Simulate policy execution to preview impact"""
    
    retention_service = DataRetentionService(db)
    
    try:
        simulation_result = retention_service.simulate_policy_execution(policy_id)
        return simulation_result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/policies/{policy_id}/execute")
async def execute_policy_now(
    policy_id: UUID,
    confirm: bool = False,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Execute policy immediately (admin action)"""
    
    if not confirm:
        raise HTTPException(status_code=400, detail="Policy execution requires explicit confirmation")
    
    policy = db.query(DataRetentionPolicy).filter(DataRetentionPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    retention_service = DataRetentionService(db)
    
    try:
        execution = retention_service.execute_policy(policy)
        
        return {
            "message": "Policy executed successfully",
            "execution_id": str(execution.id),
            "records_processed": execution.records_processed,
            "actions_taken": execution.actions_taken,
            "status": execution.status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy execution failed: {str(e)}")

@router.get("/executions")
async def list_policy_executions(
    limit: int = 50,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List recent policy executions"""
    
    executions = db.query(DataRetentionExecution).order_by(
        DataRetentionExecution.started_at.desc()
    ).limit(limit).all()
    
    return {
        "executions": [
            {
                "id": str(execution.id),
                "policy_name": execution.policy.name,
                "started_at": execution.started_at.isoformat(),
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "status": execution.status,
                "records_processed": execution.records_processed,
                "actions_taken": execution.actions_taken,
                "success_rate": execution.success_rate,
                "duration": str(execution.execution_duration)
            }
            for execution in executions
        ]
    }

# Request/Response models
class RetentionPolicyCreate(BaseModel):
    name: str
    description: Optional[str]
    data_category: str
    compliance_regime: str = "general"
    retention_days: int
    action_after_retention: str
    grace_period_days: Optional[int] = 30
    legal_basis: Optional[str]
    business_justification: Optional[str]
```

## 🧪 Test Scenarios

### Policy Execution Tests
```python
def test_personal_data_anonymization_policy():
    """Test automated personal data anonymization"""
    # Create policy for personal data anonymization
    policy = DataRetentionPolicy(
        name="Personal Data Anonymization",
        data_category=DataCategory.PERSONAL_IDENTIFIABLE,
        retention_days=365,  # 1 year
        action_after_retention=RetentionAction.ANONYMIZE,
        grace_period_days=30
    )
    db.add(policy)
    
    # Create old inactive client
    old_client = create_test_client(db, user_id, created_at=datetime.utcnow() - timedelta(days=400))
    old_client.is_active = False
    db.commit()
    
    # Execute policy
    retention_service = DataRetentionService(db)
    execution = retention_service.execute_policy(policy)
    
    # Verify client was anonymized
    updated_client = db.query(Client).filter(Client.id == old_client.id).first()
    assert updated_client.is_anonymized == True
    assert execution.records_processed == 1
    assert execution.actions_taken.get('anonymized') == 1

def test_audit_log_archival_policy():
    """Test automated audit log archival"""
    policy = DataRetentionPolicy(
        name="Audit Log Archival",
        data_category=DataCategory.AUDIT_LOGS,
        retention_days=2555,  # 7 years
        action_after_retention=RetentionAction.ARCHIVE
    )
    
    # Create old audit logs
    old_logs = [
        create_audit_log(db, timestamp=datetime.utcnow() - timedelta(days=2600))
        for _ in range(5)
    ]
    
    retention_service = DataRetentionService(db)
    execution = retention_service.execute_policy(policy)
    
    # Verify logs were archived
    assert execution.records_processed == 5
    assert execution.actions_taken.get('archived') == 5
    
    # Check archived logs exist
    archived_count = db.query(ArchivedAuditLog).count()
    assert archived_count == 5
```

### Policy Management Tests
```bash
# Test: Create retention policy
curl -X POST "/api/v1/admin/data-retention/policies" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "name": "Client Data Anonymization",
    "data_category": "personal_identifiable", 
    "retention_days": 365,
    "action_after_retention": "anonymize"
  }'

# Test: Simulate policy execution
curl -X POST "/api/v1/admin/data-retention/policies/$POLICY_ID/simulate" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected: Returns impact estimation without making changes
```

## 📊 Success Metrics

### Compliance Metrics
- **Policy Coverage**: 100% of data categories covered by retention policies
- **Execution Success Rate**: >99% successful policy executions
- **Compliance Violations**: 0% data retained beyond legal requirements
- **GDPR Article 5 Compliance**: 100% compliance with data minimization principles

### Operational Benefits
- **Storage Cost Reduction**: 30-50% reduction in storage costs through automated cleanup
- **Manual Intervention**: <5% of retention operations require manual intervention
- **Policy Execution Time**: <2 hours for large-scale retention operations

## 📋 Definition of Done

- [ ] **Retention Policy Model**: Comprehensive data retention policy configuration system
- [ ] **Automated Execution**: Daily job for automated policy execution
- [ ] **Policy Management**: Admin interface for creating and managing retention policies
- [ ] **Simulation Capability**: Policy impact simulation before execution
- [ ] **Safety Mechanisms**: Confirmation requirements and rollback capabilities
- [ ] **Archive Storage**: Cold storage system for archived data
- [ ] **Compliance Reporting**: Reports demonstrating retention policy compliance
- [ ] **Unit Tests**: >85% coverage for retention policy components
- [ ] **Integration Tests**: End-to-end policy execution scenarios
- [ ] **Documentation**: Admin guide for data retention policy management

## 🔄 Dependencies & Risks

### Dependencies
- ✅ US003 (GDPR Compliance Enhancement) - Required for anonymization workflows
- ✅ US005 (Audit Trail Logging) - Required for policy execution auditing
- ⏳ Cold storage infrastructure for archived data
- ⏳ Legal review of retention policies and compliance requirements

### Risks & Mitigations
- **Risk**: Accidental deletion of important data
  - **Mitigation**: Confirmation requirements, simulation mode, comprehensive testing
- **Risk**: Policy execution performance impact
  - **Mitigation**: Batch processing, off-peak execution, performance monitoring
- **Risk**: Legal compliance gaps in policy configuration
  - **Mitigation**: Legal review, compliance templates, regular audits

## 📞 Stakeholders

**Product Owner**: Legal/Compliance Team  
**Technical Lead**: Backend Engineering, DevOps  
**Reviewers**: Legal Counsel, Data Protection Officer, Infrastructure Team  
**QA Focus**: Compliance verification, Data safety, Performance testing