# US005: Audit Trail Logging

## 📋 User Story

**As a** system administrator and compliance officer  
**I want** comprehensive audit trails for all data operations and system activities  
**So that** we can track all changes, investigate issues, and maintain regulatory compliance

## 💼 Business Value

### Current Problem
- Limited audit logging for data operations and user activities
- No centralized audit trail for compliance verification
- Difficult to investigate data issues or user complaints
- Insufficient logging for security incident response
- No audit trail for GDPR data processing activities

### Business Impact
- **Compliance Risk**: Insufficient audit trails for regulatory requirements
- **Security Risk**: Limited visibility into data access and modifications
- **Support Overhead**: Difficult to troubleshoot user issues without comprehensive logs
- **Investigation Challenges**: Cannot track data changes or user activities effectively

### Value Delivered
- **Regulatory Compliance**: Complete audit trails for GDPR, SOX, and other requirements
- **Security Monitoring**: Full visibility into data access and system activities
- **Issue Resolution**: Comprehensive logging enables faster problem diagnosis
- **User Trust**: Transparent logging builds user confidence in data handling

## 🎯 Acceptance Criteria

### Comprehensive Activity Logging
1. **User Activity Logging**
   - [ ] All user authentication events (login, logout, password changes)
   - [ ] User profile changes and settings updates
   - [ ] Client creation, modification, and deletion (including soft delete)
   - [ ] Session creation, processing, and management activities

2. **Data Operation Logging**
   - [ ] All database create, update, delete operations on sensitive data
   - [ ] File upload and processing activities
   - [ ] Transcription start, progress, completion, and failure events
   - [ ] Usage analytics creation and modification

3. **System Operation Logging**
   - [ ] Admin actions and configuration changes
   - [ ] Automated data retention policy executions
   - [ ] GDPR processing activities (anonymization, data export)
   - [ ] Billing and usage calculation events

### Audit Log Structure
4. **Structured Audit Entries**
   - [ ] Consistent audit log format across all operations
   - [ ] Comprehensive metadata: timestamp, user, IP address, operation type
   - [ ] Before/after values for data modifications
   - [ ] Context information: session IDs, client IDs, related entities

5. **Audit Log Integrity**
   - [ ] Immutable audit logs (cannot be modified after creation)
   - [ ] Cryptographic integrity verification for audit entries
   - [ ] Audit log retention policies separate from business data
   - [ ] Secure storage with restricted access controls

### Audit Query and Reporting
6. **Audit Log Access**
   - [ ] Admin interface for searching and filtering audit logs
   - [ ] User activity summaries for individual users
   - [ ] Compliance reports for regulatory requirements
   - [ ] Export functionality for external audit systems

## 🏗️ Technical Implementation

### Audit Log Data Model
```python
# packages/core-logic/src/coaching_assistant/models/audit_log.py

import enum
from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from .base import BaseModel

class AuditEventType(enum.Enum):
    """Types of audit events"""
    # Authentication events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    PASSWORD_CHANGE = "password_change"
    
    # User profile events
    PROFILE_CREATE = "profile_create"
    PROFILE_UPDATE = "profile_update"
    PROFILE_DELETE = "profile_delete"
    
    # Client management events
    CLIENT_CREATE = "client_create"
    CLIENT_UPDATE = "client_update"
    CLIENT_SOFT_DELETE = "client_soft_delete"
    CLIENT_RESTORE = "client_restore"
    CLIENT_ANONYMIZE = "client_anonymize"
    CLIENT_HARD_DELETE = "client_hard_delete"
    
    # Session and transcription events
    SESSION_CREATE = "session_create"
    SESSION_UPDATE = "session_update"
    TRANSCRIPTION_START = "transcription_start"
    TRANSCRIPTION_COMPLETE = "transcription_complete"
    TRANSCRIPTION_FAIL = "transcription_fail"
    TRANSCRIPTION_RETRY = "transcription_retry"
    
    # Data processing events
    USAGE_LOG_CREATE = "usage_log_create"
    ANALYTICS_UPDATE = "analytics_update"
    DATA_EXPORT = "data_export"
    
    # Admin events
    ADMIN_ACTION = "admin_action"
    CONFIG_CHANGE = "config_change"
    DATA_RETENTION_POLICY = "data_retention_policy"
    
    # GDPR events
    GDPR_ACCESS_REQUEST = "gdpr_access_request"
    GDPR_ERASURE_REQUEST = "gdpr_erasure_request"
    GDPR_DATA_EXPORT = "gdpr_data_export"

class AuditSeverity(enum.Enum):
    """Severity levels for audit events"""
    LOW = "low"           # Normal operations
    MEDIUM = "medium"     # Important changes  
    HIGH = "high"         # Security-sensitive operations
    CRITICAL = "critical" # GDPR, admin actions

class AuditLog(BaseModel):
    """Immutable audit log entries"""
    
    # Event identification
    event_type = Column(Enum(AuditEventType), nullable=False, index=True)
    severity = Column(Enum(AuditSeverity), nullable=False, default=AuditSeverity.LOW)
    
    # User and session context
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # None for system events
    session_token = Column(String(64), nullable=True)  # For session tracking
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)
    
    # Entity context
    entity_type = Column(String(50), nullable=True, index=True)  # "client", "session", "user", etc.
    entity_id = Column(String(50), nullable=True, index=True)   # UUID as string
    
    # Operation details
    operation = Column(String(100), nullable=False)  # "create", "update", "delete", etc.
    description = Column(Text, nullable=False)       # Human-readable description
    
    # Data changes (for update operations)
    old_values = Column(JSONB, nullable=True)  # Before state
    new_values = Column(JSONB, nullable=True)  # After state
    
    # Additional context
    metadata = Column(JSONB, default={}, nullable=False)  # Additional context data
    
    # Timing information
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Integrity protection
    checksum = Column(String(64), nullable=True)  # SHA-256 hash for integrity
    
    def __repr__(self):
        return f"<AuditLog(event={self.event_type.value}, user={self.user_id}, entity={self.entity_type}:{self.entity_id})>"
    
    @property
    def is_data_modification(self) -> bool:
        """Check if this audit entry represents a data modification"""
        return self.operation in ['create', 'update', 'delete'] and self.entity_type is not None
    
    @property
    def is_security_relevant(self) -> bool:
        """Check if this audit entry is security-relevant"""
        return self.severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]
    
    def calculate_checksum(self) -> str:
        """Calculate integrity checksum for audit entry"""
        import hashlib
        import json
        
        # Create deterministic representation
        data = {
            'event_type': self.event_type.value,
            'user_id': str(self.user_id) if self.user_id else None,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'operation': self.operation,
            'description': self.description,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'old_values': self.old_values,
            'new_values': self.new_values
        }
        
        # Create hash
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

# Index for performance
from sqlalchemy import Index
Index('idx_audit_log_user_time', AuditLog.user_id, AuditLog.timestamp)
Index('idx_audit_log_entity', AuditLog.entity_type, AuditLog.entity_id)
Index('idx_audit_log_event_time', AuditLog.event_type, AuditLog.timestamp)
```

### Audit Logging Service
```python
# packages/core-logic/src/coaching_assistant/services/audit_service.py

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from flask import request, g
import logging

logger = logging.getLogger(__name__)

class AuditService:
    """Service for creating and managing audit logs"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_event(
        self,
        event_type: AuditEventType,
        operation: str,
        description: str,
        user_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        severity: AuditSeverity = AuditSeverity.LOW,
        metadata: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Create audit log entry"""
        
        # Extract request context if available
        if not ip_address and hasattr(request, 'remote_addr'):
            ip_address = request.remote_addr
        if not user_agent and hasattr(request, 'user_agent'):
            user_agent = str(request.user_agent)
        
        # Get current user if not specified
        if not user_id and hasattr(g, 'current_user') and g.current_user:
            user_id = g.current_user.id
        
        audit_entry = AuditLog(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            operation=operation,
            description=description,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata or {}
        )
        
        # Calculate integrity checksum
        audit_entry.checksum = audit_entry.calculate_checksum()
        
        try:
            self.db.add(audit_entry)
            self.db.commit()
            
            logger.info(f"Audit log created: {event_type.value} - {description}")
            return audit_entry
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create audit log: {e}")
            raise
    
    def log_user_activity(
        self,
        event_type: AuditEventType,
        description: str,
        user_id: UUID,
        metadata: Optional[Dict] = None
    ) -> AuditLog:
        """Log user activity events"""
        return self.log_event(
            event_type=event_type,
            operation="user_activity",
            description=description,
            user_id=user_id,
            severity=AuditSeverity.MEDIUM,
            metadata=metadata
        )
    
    def log_data_change(
        self,
        event_type: AuditEventType,
        entity_type: str,
        entity_id: UUID,
        operation: str,
        description: str,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        user_id: Optional[UUID] = None
    ) -> AuditLog:
        """Log data modification events"""
        
        # Determine severity based on entity type and operation
        severity = AuditSeverity.MEDIUM
        if entity_type in ['user', 'client'] and operation in ['delete', 'anonymize']:
            severity = AuditSeverity.HIGH
        
        return self.log_event(
            event_type=event_type,
            operation=operation,
            description=description,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=str(entity_id),
            old_values=old_values,
            new_values=new_values,
            severity=severity
        )
    
    def log_system_event(
        self,
        event_type: AuditEventType,
        description: str,
        metadata: Optional[Dict] = None,
        severity: AuditSeverity = AuditSeverity.LOW
    ) -> AuditLog:
        """Log system-level events"""
        return self.log_event(
            event_type=event_type,
            operation="system_operation",
            description=description,
            severity=severity,
            metadata=metadata
        )
    
    def log_gdpr_activity(
        self,
        event_type: AuditEventType,
        description: str,
        user_id: UUID,
        metadata: Optional[Dict] = None
    ) -> AuditLog:
        """Log GDPR-related activities"""
        return self.log_event(
            event_type=event_type,
            operation="gdpr_processing",
            description=description,
            user_id=user_id,
            severity=AuditSeverity.CRITICAL,
            metadata=metadata
        )
    
    def search_audit_logs(
        self,
        user_id: Optional[UUID] = None,
        event_types: Optional[List[AuditEventType]] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Search audit logs with filters"""
        
        query = self.db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if event_types:
            query = query.filter(AuditLog.event_type.in_(event_types))
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == str(entity_id))
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        if severity:
            query = query.filter(AuditLog.severity == severity)
        
        return query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    def verify_audit_integrity(self, audit_log: AuditLog) -> bool:
        """Verify integrity of audit log entry"""
        expected_checksum = audit_log.calculate_checksum()
        return audit_log.checksum == expected_checksum

# Global audit service instance
def get_audit_service(db: Session) -> AuditService:
    """Get audit service instance"""
    return AuditService(db)

# Convenience functions for common audit operations
def audit_client_change(
    db: Session,
    client: "Client", 
    operation: str, 
    description: str, 
    old_values: Optional[Dict] = None,
    new_values: Optional[Dict] = None
):
    """Audit client-related changes"""
    audit_service = get_audit_service(db)
    
    event_type_mapping = {
        'create': AuditEventType.CLIENT_CREATE,
        'update': AuditEventType.CLIENT_UPDATE,
        'soft_delete': AuditEventType.CLIENT_SOFT_DELETE,
        'restore': AuditEventType.CLIENT_RESTORE,
        'anonymize': AuditEventType.CLIENT_ANONYMIZE,
        'hard_delete': AuditEventType.CLIENT_HARD_DELETE
    }
    
    event_type = event_type_mapping.get(operation, AuditEventType.CLIENT_UPDATE)
    
    return audit_service.log_data_change(
        event_type=event_type,
        entity_type="client",
        entity_id=client.id,
        operation=operation,
        description=description,
        old_values=old_values,
        new_values=new_values,
        user_id=client.user_id
    )

def audit_session_change(
    db: Session,
    session: "Session",
    operation: str,
    description: str,
    metadata: Optional[Dict] = None
):
    """Audit session-related changes"""
    audit_service = get_audit_service(db)
    
    event_type_mapping = {
        'create': AuditEventType.SESSION_CREATE,
        'update': AuditEventType.SESSION_UPDATE,
        'transcription_start': AuditEventType.TRANSCRIPTION_START,
        'transcription_complete': AuditEventType.TRANSCRIPTION_COMPLETE,
        'transcription_fail': AuditEventType.TRANSCRIPTION_FAIL,
        'transcription_retry': AuditEventType.TRANSCRIPTION_RETRY
    }
    
    event_type = event_type_mapping.get(operation, AuditEventType.SESSION_UPDATE)
    
    return audit_service.log_data_change(
        event_type=event_type,
        entity_type="session",
        entity_id=session.id,
        operation=operation,
        description=description,
        user_id=session.user_id,
        metadata=metadata
    )
```

### Integration with Existing Models
```python
# packages/core-logic/src/coaching_assistant/models/client.py (Enhanced)

class Client(BaseModel):
    """Enhanced Client model with audit logging"""
    
    # ... existing fields ...
    
    def soft_delete(self, deleted_by_user_id: UUID):
        """Soft delete with audit logging"""
        from ..services.audit_service import audit_client_change
        from ..core.database import get_db_session
        
        old_values = {
            'is_active': self.is_active,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'deleted_by': str(self.deleted_by) if self.deleted_by else None
        }
        
        # Perform soft delete
        self.is_active = False
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by_user_id
        
        new_values = {
            'is_active': self.is_active,
            'deleted_at': self.deleted_at.isoformat(),
            'deleted_by': str(self.deleted_by)
        }
        
        # Create audit log
        with get_db_session() as db:
            audit_client_change(
                db=db,
                client=self,
                operation='soft_delete',
                description=f"Client '{self.name}' soft deleted",
                old_values=old_values,
                new_values=new_values
            )
    
    def anonymize(self, anonymous_number: int):
        """Enhanced anonymization with audit logging"""
        from ..services.audit_service import audit_client_change
        from ..core.database import get_db_session
        
        old_values = {
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'is_anonymized': self.is_anonymized
        }
        
        # Perform anonymization (existing logic)
        self.name = f"已刪除客戶 {anonymous_number}"
        self.email = None
        self.phone = None
        self.memo = None
        self.is_anonymized = True
        self.anonymized_at = datetime.utcnow()
        
        new_values = {
            'name': self.name,
            'email': None,
            'phone': None,
            'is_anonymized': self.is_anonymized
        }
        
        # Create audit log
        with get_db_session() as db:
            audit_client_change(
                db=db,
                client=self,
                operation='anonymize',
                description=f"Client anonymized for GDPR compliance",
                old_values=old_values,
                new_values=new_values
            )
```

### API Middleware for Automatic Logging
```python
# packages/core-logic/src/coaching_assistant/middleware/audit_middleware.py

from flask import request, g
from functools import wraps
from ..services.audit_service import get_audit_service, AuditEventType, AuditSeverity

def audit_api_call(
    event_type: AuditEventType = None,
    description: str = None,
    severity: AuditSeverity = AuditSeverity.LOW
):
    """Decorator to automatically audit API calls"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute the function first
            try:
                result = func(*args, **kwargs)
                
                # Create audit log after successful execution
                if hasattr(g, 'db') and g.db:
                    audit_service = get_audit_service(g.db)
                    
                    # Auto-generate description if not provided
                    auto_description = description or f"API call: {request.method} {request.path}"
                    
                    audit_service.log_event(
                        event_type=event_type or AuditEventType.ADMIN_ACTION,
                        operation=request.method.lower(),
                        description=auto_description,
                        severity=severity,
                        metadata={
                            'endpoint': request.endpoint,
                            'method': request.method,
                            'path': request.path,
                            'response_status': 'success'
                        }
                    )
                
                return result
                
            except Exception as e:
                # Log failed API calls
                if hasattr(g, 'db') and g.db:
                    audit_service = get_audit_service(g.db)
                    audit_service.log_event(
                        event_type=AuditEventType.ADMIN_ACTION,
                        operation=request.method.lower(),
                        description=f"API call failed: {request.method} {request.path} - {str(e)}",
                        severity=AuditSeverity.HIGH,
                        metadata={
                            'endpoint': request.endpoint,
                            'method': request.method,
                            'path': request.path,
                            'response_status': 'error',
                            'error_message': str(e)
                        }
                    )
                raise
        
        return wrapper
    return decorator

# Usage in API endpoints
@router.delete("/{client_id}")
@audit_api_call(
    event_type=AuditEventType.CLIENT_SOFT_DELETE,
    description="Client soft deletion via API",
    severity=AuditSeverity.HIGH
)
async def soft_delete_client(client_id: UUID, ...):
    # API implementation
    pass
```

### Audit Log API Endpoints
```python
# packages/core-logic/src/coaching_assistant/api/audit.py

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from ..services.audit_service import AuditService, AuditEventType, AuditSeverity
from ..models.audit_log import AuditLog

router = APIRouter()

@router.get("/logs")
async def get_audit_logs(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs with filtering (admin only)"""
    
    audit_service = AuditService(db)
    
    # Convert string parameters to enums
    event_types = None
    if event_type:
        try:
            event_types = [AuditEventType(event_type)]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
    
    severity_enum = None
    if severity:
        try:
            severity_enum = AuditSeverity(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
    
    # Search audit logs
    audit_logs = audit_service.search_audit_logs(
        user_id=user_id,
        event_types=event_types,
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date,
        severity=severity_enum,
        limit=limit,
        offset=offset
    )
    
    return {
        "audit_logs": [
            {
                "id": str(log.id),
                "event_type": log.event_type.value,
                "severity": log.severity.value,
                "timestamp": log.timestamp.isoformat(),
                "user_id": str(log.user_id) if log.user_id else None,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "operation": log.operation,
                "description": log.description,
                "ip_address": log.ip_address,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "metadata": log.metadata
            }
            for log in audit_logs
        ],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(audit_logs)
        }
    }

@router.get("/user/{user_id}/activity")
async def get_user_activity(
    user_id: UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get user activity summary (admin only)"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    audit_service = AuditService(db)
    user_logs = audit_service.search_audit_logs(
        user_id=user_id,
        start_date=start_date,
        limit=1000
    )
    
    # Aggregate activity statistics
    activity_stats = {}
    for log in user_logs:
        event_type = log.event_type.value
        activity_stats[event_type] = activity_stats.get(event_type, 0) + 1
    
    return {
        "user_id": str(user_id),
        "period_days": days,
        "total_activities": len(user_logs),
        "activity_breakdown": activity_stats,
        "recent_activities": [
            {
                "timestamp": log.timestamp.isoformat(),
                "event_type": log.event_type.value,
                "description": log.description,
                "ip_address": log.ip_address
            }
            for log in user_logs[:10]  # Most recent 10
        ]
    }

@router.get("/compliance-report")
async def generate_compliance_report(
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Generate compliance audit report (admin only)"""
    
    audit_service = AuditService(db)
    
    # Get all audit logs for the period
    all_logs = audit_service.search_audit_logs(
        start_date=start_date,
        end_date=end_date,
        limit=10000
    )
    
    # Generate compliance statistics
    report = {
        "report_period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "summary": {
            "total_events": len(all_logs),
            "high_severity_events": len([l for l in all_logs if l.severity == AuditSeverity.HIGH]),
            "critical_events": len([l for l in all_logs if l.severity == AuditSeverity.CRITICAL]),
            "gdpr_events": len([l for l in all_logs if l.event_type.value.startswith('gdpr_')])
        },
        "event_breakdown": {},
        "user_activity": {},
        "data_operations": []
    }
    
    # Event breakdown
    for log in all_logs:
        event_type = log.event_type.value
        report["event_breakdown"][event_type] = report["event_breakdown"].get(event_type, 0) + 1
    
    # High-priority events for review
    critical_events = [l for l in all_logs if l.severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]]
    report["critical_events"] = [
        {
            "timestamp": log.timestamp.isoformat(),
            "event_type": log.event_type.value,
            "description": log.description,
            "user_id": str(log.user_id) if log.user_id else None,
            "severity": log.severity.value
        }
        for log in critical_events[:50]  # Top 50 critical events
    ]
    
    return report
```

## 🧪 Test Scenarios

### Audit Logging Tests
```python
def test_audit_log_creation():
    """Test audit log entry creation"""
    audit_service = AuditService(db)
    
    audit_log = audit_service.log_event(
        event_type=AuditEventType.CLIENT_CREATE,
        operation="create",
        description="Test client created",
        entity_type="client",
        entity_id=str(uuid4()),
        user_id=test_user.id
    )
    
    assert audit_log.id is not None
    assert audit_log.event_type == AuditEventType.CLIENT_CREATE
    assert audit_log.checksum is not None
    
def test_audit_integrity_verification():
    """Test audit log integrity verification"""
    audit_service = AuditService(db)
    
    audit_log = audit_service.log_event(
        event_type=AuditEventType.CLIENT_UPDATE,
        operation="update",
        description="Test update",
        old_values={"name": "Old Name"},
        new_values={"name": "New Name"}
    )
    
    # Verify integrity
    assert audit_service.verify_audit_integrity(audit_log) == True
    
    # Tamper with data
    audit_log.description = "Tampered description"
    assert audit_service.verify_audit_integrity(audit_log) == False

def test_client_anonymization_audit():
    """Test client anonymization creates proper audit trail"""
    client = create_test_client(db, user_id)
    original_name = client.name
    
    # Anonymize client
    client.anonymize(1)
    
    # Check audit log was created
    audit_logs = db.query(AuditLog).filter(
        and_(
            AuditLog.entity_type == "client",
            AuditLog.entity_id == str(client.id),
            AuditLog.event_type == AuditEventType.CLIENT_ANONYMIZE
        )
    ).all()
    
    assert len(audit_logs) == 1
    audit_log = audit_logs[0]
    assert audit_log.old_values["name"] == original_name
    assert "已刪除客戶" in audit_log.new_values["name"]
```

### API Integration Tests
```bash
# Test: Admin audit log access
curl -X GET "/api/v1/audit/logs?limit=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected: Returns audit logs with proper structure

# Test: User activity summary  
curl -X GET "/api/v1/audit/user/$USER_ID/activity?days=7" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected: Returns user activity breakdown

# Test: Compliance report generation
curl -X GET "/api/v1/audit/compliance-report?start_date=2025-08-01&end_date=2025-08-14" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected: Returns comprehensive compliance report
```

## 📊 Success Metrics

### Audit Coverage
- **Event Coverage**: 100% of critical operations generate audit logs
- **Data Integrity**: 100% of audit logs pass integrity verification
- **Compliance Readiness**: All GDPR and regulatory requirements covered by audit trails

### Performance Impact
- **Logging Performance**: <10ms additional latency for audit log creation
- **Query Performance**: <500ms for audit log searches with filters
- **Storage Efficiency**: Audit logs consume <5% of total database storage

### Operational Benefits
- **Issue Resolution**: 50% reduction in time to diagnose user issues
- **Compliance Confidence**: Pass 100% of audit compliance checks
- **Security Monitoring**: Full visibility into all data access and modifications

## 📋 Definition of Done

- [ ] **Audit Log Model**: Comprehensive AuditLog model with integrity protection
- [ ] **Audit Service**: AuditService with logging, search, and verification capabilities
- [ ] **Model Integration**: All critical models integrated with audit logging
- [ ] **API Middleware**: Automatic audit logging for API calls
- [ ] **Admin APIs**: Audit log query, user activity, and compliance reporting endpoints
- [ ] **Integrity Verification**: Cryptographic integrity protection for audit entries
- [ ] **Performance Optimization**: Proper indexing and query optimization
- [ ] **Unit Tests**: >90% coverage for audit logging components
- [ ] **Integration Tests**: End-to-end audit trail verification
- [ ] **Documentation**: Admin guide for audit log management and compliance reporting

## 🔄 Dependencies & Risks

### Dependencies
- ✅ Database infrastructure for audit log storage
- ⏳ Admin user authentication and authorization system
- ⏳ Performance monitoring for audit logging overhead
- ⏳ Retention policies for audit log data

### Risks & Mitigations
- **Risk**: Audit logging performance impact on application
  - **Mitigation**: Async logging, optimized queries, performance monitoring
- **Risk**: Audit log storage growth
  - **Mitigation**: Retention policies, archiving strategies, compression
- **Risk**: Audit log integrity compromised
  - **Mitigation**: Cryptographic checksums, immutable storage, access controls

## 📞 Stakeholders

**Product Owner**: Compliance/Legal Team  
**Technical Lead**: Backend Engineering, Security Team  
**Reviewers**: Security Officer, Database Admin, External Auditors  
**QA Focus**: Audit completeness, Data integrity, Compliance verification