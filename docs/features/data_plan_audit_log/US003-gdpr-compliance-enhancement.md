# US003: GDPR Compliance Enhancement

## 📋 User Story

**As a** data protection officer and platform user  
**I want** comprehensive GDPR compliance with enhanced data retention and anonymization capabilities  
**So that** personal data is properly protected while preserving business-critical usage analytics

## 💼 Business Value

### Current Problem
- Basic anonymization exists but lacks comprehensive GDPR data lifecycle management
- No automated data retention policies for different data types
- Usage analytics could be lost when GDPR deletion requests are processed
- Missing audit trails for data protection compliance verification

### Business Impact
- **Legal Risk**: GDPR non-compliance penalties up to 4% of annual revenue
- **Operational Risk**: Manual data retention processes prone to errors
- **Analytics Loss**: GDPR deletions could eliminate valuable business intelligence
- **Audit Risk**: Insufficient documentation for regulatory compliance audits

### Value Delivered  
- **Full GDPR Compliance**: Automated compliance with all data protection requirements
- **Risk Mitigation**: Proactive data protection reduces legal and operational risks
- **Analytics Preservation**: Smart anonymization preserves business value while protecting privacy
- **Audit Readiness**: Complete documentation and audit trails for regulatory inspections

## 🎯 Acceptance Criteria

### Enhanced Anonymization System
1. **Multi-Level Data Classification**
   - [ ] Personal data (PII) identified and classified by sensitivity level
   - [ ] Usage data separated from personal data for independent retention
   - [ ] System metadata preserved for technical operations
   - [ ] Business analytics anonymized but preserved

2. **Smart Anonymization Process**
   - [ ] Personal identifiers removed while preserving data relationships
   - [ ] Usage statistics converted to anonymized aggregates
   - [ ] Session data anonymized but analytical value retained
   - [ ] Coach-client relationships anonymized with pseudonymization

3. **Data Subject Rights Implementation**
   - [ ] Right to access: Complete data export functionality
   - [ ] Right to rectification: Personal data correction workflows
   - [ ] Right to erasure: Enhanced anonymization process
   - [ ] Right to portability: Structured data export formats

### Automated Data Retention
4. **Data Lifecycle Management**
   - [ ] Automated retention policies based on data type and purpose
   - [ ] Personal data auto-purged after retention period
   - [ ] Usage analytics retained indefinitely in anonymized form
   - [ ] System logs retained per compliance requirements

5. **Retention Policy Engine**
   - [ ] Configurable retention periods by data category
   - [ ] Automated execution of retention policies
   - [ ] Manual override capabilities for legal holds
   - [ ] Audit logging of all retention actions

### Compliance Monitoring
6. **GDPR Compliance Dashboard**
   - [ ] Real-time compliance status monitoring
   - [ ] Data retention policy compliance tracking
   - [ ] Data subject request processing metrics
   - [ ] Breach detection and notification systems

## 🏗️ Technical Implementation

### Enhanced Data Classification
```python
# packages/core-logic/src/coaching_assistant/models/data_classification.py

from enum import Enum
from typing import Dict, List

class DataCategory(Enum):
    """Data classification for GDPR compliance"""
    PERSONAL_IDENTIFIABLE = "personal_identifiable"  # Name, email, phone
    PERSONAL_SENSITIVE = "personal_sensitive"       # Health, preferences  
    USAGE_ANALYTICS = "usage_analytics"             # Session duration, costs
    SYSTEM_METADATA = "system_metadata"             # IDs, timestamps
    BUSINESS_ANALYTICS = "business_analytics"       # Aggregated insights

class RetentionPeriod(Enum):
    """Data retention periods"""
    IMMEDIATE = 0                    # Delete immediately
    DAYS_30 = 30                    # 30 days
    MONTHS_12 = 365                 # 1 year
    YEARS_7 = 2555                  # 7 years (business records)
    INDEFINITE = -1                 # Keep indefinitely (anonymized)

class DataClassificationMap:
    """Map database fields to GDPR data categories"""
    
    FIELD_CLASSIFICATION = {
        # Client personal data
        'client.name': DataCategory.PERSONAL_IDENTIFIABLE,
        'client.email': DataCategory.PERSONAL_IDENTIFIABLE, 
        'client.phone': DataCategory.PERSONAL_IDENTIFIABLE,
        'client.memo': DataCategory.PERSONAL_SENSITIVE,
        
        # User personal data
        'user.name': DataCategory.PERSONAL_IDENTIFIABLE,
        'user.email': DataCategory.PERSONAL_IDENTIFIABLE,
        'user.avatar_url': DataCategory.PERSONAL_IDENTIFIABLE,
        
        # Usage and analytics data
        'usage_logs.*': DataCategory.USAGE_ANALYTICS,
        'usage_analytics.*': DataCategory.BUSINESS_ANALYTICS,
        'session.title': DataCategory.PERSONAL_SENSITIVE,
        'session.duration_*': DataCategory.USAGE_ANALYTICS,
        
        # System metadata  
        '*.id': DataCategory.SYSTEM_METADATA,
        '*.created_at': DataCategory.SYSTEM_METADATA,
        '*.updated_at': DataCategory.SYSTEM_METADATA,
    }
    
    RETENTION_POLICIES = {
        DataCategory.PERSONAL_IDENTIFIABLE: RetentionPeriod.YEARS_7,
        DataCategory.PERSONAL_SENSITIVE: RetentionPeriod.YEARS_7,
        DataCategory.USAGE_ANALYTICS: RetentionPeriod.INDEFINITE,
        DataCategory.BUSINESS_ANALYTICS: RetentionPeriod.INDEFINITE,
        DataCategory.SYSTEM_METADATA: RetentionPeriod.YEARS_7,
    }

# Enhanced anonymization model
class GDPRAnonymization(BaseModel):
    """Track GDPR anonymization operations"""
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)
    client_id = Column(UUID(as_uuid=True), nullable=True)  # May be multiple clients
    
    # Request details
    request_type = Column(Enum(['access', 'rectification', 'erasure', 'portability']), nullable=False)
    request_date = Column(DateTime(timezone=True), nullable=False)
    processed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Processing details
    status = Column(Enum(['pending', 'processing', 'completed', 'failed']), default='pending')
    data_categories_processed = Column(JSONB, default={})
    
    # Anonymization metadata
    original_records_count = Column(Integer, nullable=False, default=0)
    anonymized_records_count = Column(Integer, nullable=False, default=0)
    preserved_analytics_count = Column(Integer, nullable=False, default=0)
    
    # Audit trail
    processing_log = Column(Text, nullable=True)
    verification_checksum = Column(String(64), nullable=True)
```

### Enhanced Anonymization Service
```python
# packages/core-logic/src/coaching_assistant/services/gdpr_service.py

from typing import Dict, List
import hashlib
import json

class GDPRService:
    """Enhanced GDPR compliance service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.anonymization_counter = 0
    
    def process_erasure_request(self, user_id: UUID, client_ids: List[UUID] = None) -> GDPRAnonymization:
        """Process GDPR erasure request with enhanced anonymization"""
        
        # Create GDPR processing record
        gdpr_request = GDPRAnonymization(
            user_id=user_id,
            request_type='erasure',
            request_date=datetime.utcnow(),
            status='processing'
        )
        self.db.add(gdpr_request)
        self.db.commit()
        
        try:
            processing_log = []
            
            # Step 1: Anonymize personal data
            personal_data_stats = self._anonymize_personal_data(user_id, client_ids)
            processing_log.append(f"Anonymized {personal_data_stats['count']} personal records")
            
            # Step 2: Convert usage data to anonymous analytics
            usage_stats = self._convert_usage_to_anonymous_analytics(user_id, client_ids)
            processing_log.append(f"Preserved {usage_stats['count']} usage records as anonymous analytics")
            
            # Step 3: Anonymize session metadata
            session_stats = self._anonymize_session_metadata(user_id, client_ids)
            processing_log.append(f"Anonymized {session_stats['count']} session records")
            
            # Step 4: Update audit trail
            audit_stats = self._create_anonymization_audit_trail(gdpr_request.id, user_id, client_ids)
            processing_log.append(f"Created audit trail with {audit_stats['count']} entries")
            
            # Complete the request
            gdpr_request.status = 'completed'
            gdpr_request.processed_date = datetime.utcnow()
            gdpr_request.original_records_count = personal_data_stats['count'] + session_stats['count']
            gdpr_request.anonymized_records_count = personal_data_stats['count'] + session_stats['count']
            gdpr_request.preserved_analytics_count = usage_stats['count']
            gdpr_request.processing_log = '\n'.join(processing_log)
            gdpr_request.verification_checksum = self._generate_verification_checksum(gdpr_request)
            
            self.db.commit()
            
            return gdpr_request
            
        except Exception as e:
            gdpr_request.status = 'failed'
            gdpr_request.processing_log = f"Error: {str(e)}"
            self.db.commit()
            raise
    
    def _anonymize_personal_data(self, user_id: UUID, client_ids: List[UUID]) -> Dict:
        """Anonymize personal data while preserving relationships"""
        
        anonymized_count = 0
        
        # Anonymize client data
        if client_ids:
            clients = self.db.query(Client).filter(Client.id.in_(client_ids)).all()
        else:
            clients = self.db.query(Client).filter(Client.user_id == user_id).all()
        
        for client in clients:
            if not client.is_anonymized:
                self.anonymization_counter += 1
                client.anonymize(self.anonymization_counter)
                anonymized_count += 1
        
        # Anonymize user data if processing all user data
        if not client_ids:  # Full user deletion request
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.name = f"匿名用戶 {hash(user.id) % 10000}"
                user.email = f"anonymous_{hash(user.id) % 10000}@deleted.com"
                user.avatar_url = None
                anonymized_count += 1
        
        self.db.commit()
        return {"count": anonymized_count}
    
    def _convert_usage_to_anonymous_analytics(self, user_id: UUID, client_ids: List[UUID]) -> Dict:
        """Convert usage logs to anonymous analytics"""
        
        # Query usage logs to be anonymized
        query = self.db.query(UsageLog).filter(UsageLog.user_id == user_id)
        if client_ids:
            query = query.filter(UsageLog.client_id.in_(client_ids))
        
        usage_logs = query.all()
        
        # Create anonymous analytics aggregations
        anonymous_analytics = {}
        for log in usage_logs:
            month_key = f"{log.created_at.year}-{log.created_at.month}"
            
            if month_key not in anonymous_analytics:
                anonymous_analytics[month_key] = {
                    'total_minutes': 0,
                    'total_sessions': 0,
                    'total_cost': 0,
                    'provider_breakdown': {},
                    'transcription_types': {}
                }
            
            # Aggregate anonymous usage data
            anonymous_analytics[month_key]['total_minutes'] += log.duration_minutes
            anonymous_analytics[month_key]['total_sessions'] += 1
            anonymous_analytics[month_key]['total_cost'] += float(log.cost_usd or 0)
            
            # Provider breakdown
            provider = log.stt_provider
            anonymous_analytics[month_key]['provider_breakdown'][provider] = \
                anonymous_analytics[month_key]['provider_breakdown'].get(provider, 0) + log.duration_minutes
            
            # Transcription type breakdown
            trans_type = log.transcription_type.value
            anonymous_analytics[month_key]['transcription_types'][trans_type] = \
                anonymous_analytics[month_key]['transcription_types'].get(trans_type, 0) + 1
        
        # Store anonymous analytics
        for month_key, stats in anonymous_analytics.items():
            year, month = map(int, month_key.split('-'))
            
            anonymous_record = AnonymousUsageAnalytics(
                anonymized_user_hash=hashlib.md5(str(user_id).encode()).hexdigest()[:16],
                year=year,
                month=month,
                total_minutes=stats['total_minutes'],
                total_sessions=stats['total_sessions'],
                total_cost=stats['total_cost'],
                provider_breakdown=stats['provider_breakdown'],
                transcription_types=stats['transcription_types'],
                anonymization_date=datetime.utcnow()
            )
            
            self.db.add(anonymous_record)
        
        self.db.commit()
        return {"count": len(usage_logs)}
    
    def generate_data_export(self, user_id: UUID) -> Dict:
        """Generate complete data export for data subject access request"""
        
        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "user_id": str(user_id),
            "personal_data": {},
            "usage_data": {},
            "session_data": {},
            "metadata": {}
        }
        
        # Personal data
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            export_data["personal_data"]["user"] = {
                "name": user.name,
                "email": user.email,
                "plan": user.plan.value,
                "created_at": user.created_at.isoformat()
            }
        
        # Client data
        clients = self.db.query(Client).filter(Client.user_id == user_id).all()
        export_data["personal_data"]["clients"] = []
        for client in clients:
            if not client.is_anonymized:
                export_data["personal_data"]["clients"].append({
                    "name": client.name,
                    "email": client.email,
                    "phone": client.phone,
                    "created_at": client.created_at.isoformat(),
                    "status": client.status
                })
        
        # Usage data
        usage_logs = self.db.query(UsageLog).filter(UsageLog.user_id == user_id).all()
        export_data["usage_data"] = []
        for log in usage_logs:
            export_data["usage_data"].append({
                "session_id": str(log.session_id),
                "duration_minutes": log.duration_minutes,
                "cost_usd": float(log.cost_usd) if log.cost_usd else 0,
                "provider": log.stt_provider,
                "transcription_type": log.transcription_type.value,
                "date": log.created_at.isoformat()
            })
        
        return export_data

# New model for anonymous analytics preservation
class AnonymousUsageAnalytics(BaseModel):
    """Anonymous usage analytics for GDPR compliance"""
    
    anonymized_user_hash = Column(String(32), nullable=False)  # Non-reversible hash
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    total_minutes = Column(Integer, nullable=False, default=0)
    total_sessions = Column(Integer, nullable=False, default=0) 
    total_cost = Column(Numeric(10, 6), default=0)
    
    provider_breakdown = Column(JSONB, default={})
    transcription_types = Column(JSONB, default={})
    
    anonymization_date = Column(DateTime(timezone=True), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('anonymized_user_hash', 'year', 'month'),
        Index('idx_anonymous_analytics_hash_date', 'anonymized_user_hash', 'year', 'month')
    )
```

### Automated Data Retention System
```python
# packages/core-logic/src/coaching_assistant/services/data_retention_service.py

class DataRetentionService:
    """Automated GDPR-compliant data retention"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @classmethod
    def run_daily_retention_check(cls):
        """Daily job to check and enforce retention policies"""
        
        service = cls(get_db())
        
        # Check personal data retention
        service._process_personal_data_retention()
        
        # Check system metadata retention  
        service._process_system_metadata_retention()
        
        # Check audit log retention
        service._process_audit_log_retention()
        
        # Generate retention report
        service._generate_retention_report()
    
    def _process_personal_data_retention(self):
        """Process retention for personal data"""
        
        retention_cutoff = datetime.utcnow() - timedelta(days=RetentionPeriod.YEARS_7.value)
        
        # Find clients requiring anonymization
        clients_to_anonymize = self.db.query(Client).filter(
            and_(
                Client.created_at < retention_cutoff,
                Client.is_anonymized == False,
                Client.is_active == False  # Only inactive clients
            )
        ).all()
        
        gdpr_service = GDPRService(self.db)
        
        for client in clients_to_anonymize:
            try:
                # Auto-anonymize after retention period
                gdpr_service.process_erasure_request(
                    user_id=client.user_id,
                    client_ids=[client.id]
                )
                
                logger.info(f"Auto-anonymized client {client.id} due to retention policy")
                
            except Exception as e:
                logger.error(f"Failed to auto-anonymize client {client.id}: {e}")
    
    def _process_audit_log_retention(self):
        """Process audit log retention (keep longer for compliance)"""
        
        # Keep audit logs for 10 years
        retention_cutoff = datetime.utcnow() - timedelta(days=3650)
        
        old_audit_logs = self.db.query(AuditLog).filter(
            AuditLog.created_at < retention_cutoff
        ).count()
        
        if old_audit_logs > 0:
            # Archive old audit logs instead of deleting
            self._archive_audit_logs(retention_cutoff)
            logger.info(f"Archived {old_audit_logs} old audit log entries")
```

### API Endpoints for GDPR Compliance
```python
# packages/core-logic/src/coaching_assistant/api/gdpr.py

@router.post("/data-subject-access-request")
async def data_subject_access_request(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Process data subject access request (GDPR Article 15)"""
    
    gdpr_service = GDPRService(db)
    export_data = gdpr_service.generate_data_export(current_user.id)
    
    # Log the access request
    audit_log = AuditLog(
        user_id=current_user.id,
        action="data_subject_access_request",
        entity_type="user",
        entity_id=str(current_user.id),
        details={"export_size": len(json.dumps(export_data))}
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "message": "Data export generated successfully",
        "export_data": export_data,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.post("/erasure-request")
async def erasure_request(
    client_ids: Optional[List[UUID]] = None,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Process GDPR erasure request (Right to be Forgotten)"""
    
    gdpr_service = GDPRService(db)
    
    # Process erasure request
    gdpr_request = gdpr_service.process_erasure_request(
        user_id=current_user.id,
        client_ids=client_ids
    )
    
    return {
        "message": "Erasure request processed successfully",
        "request_id": str(gdpr_request.id),
        "anonymized_records": gdpr_request.anonymized_records_count,
        "preserved_analytics": gdpr_request.preserved_analytics_count,
        "processing_date": gdpr_request.processed_date.isoformat()
    }

@router.get("/compliance-status")
async def get_compliance_status(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get GDPR compliance status for user"""
    
    # Check data retention status
    retention_cutoff = datetime.utcnow() - timedelta(days=RetentionPeriod.YEARS_7.value)
    
    overdue_clients = db.query(Client).filter(
        and_(
            Client.user_id == current_user.id,
            Client.created_at < retention_cutoff,
            Client.is_anonymized == False
        )
    ).count()
    
    # Recent GDPR requests
    recent_requests = db.query(GDPRAnonymization).filter(
        and_(
            GDPRAnonymization.user_id == current_user.id,
            GDPRAnonymization.request_date > datetime.utcnow() - timedelta(days=90)
        )
    ).all()
    
    return {
        "compliance_status": "compliant" if overdue_clients == 0 else "attention_required",
        "overdue_anonymization_count": overdue_clients,
        "recent_requests": [
            {
                "id": str(req.id),
                "type": req.request_type,
                "status": req.status,
                "request_date": req.request_date.isoformat(),
                "processed_date": req.processed_date.isoformat() if req.processed_date else None
            }
            for req in recent_requests
        ]
    }
```

## 🧪 Test Scenarios

### GDPR Compliance Tests
```python
def test_erasure_request_preserves_analytics():
    """Test erasure request preserves anonymous analytics"""
    # Given: Client with usage history
    client = create_test_client(db, user_id)
    usage_logs = create_usage_logs(db, client_id=client.id, count=5)
    
    # When: GDPR erasure request is processed
    gdpr_service = GDPRService(db)
    request = gdpr_service.process_erasure_request(user_id, [client.id])
    
    # Then: Personal data anonymized, analytics preserved
    anonymized_client = db.query(Client).filter(Client.id == client.id).first()
    assert anonymized_client.is_anonymized == True
    assert "已刪除客戶" in anonymized_client.name
    
    # Anonymous analytics should be created
    anonymous_analytics = db.query(AnonymousUsageAnalytics).all()
    assert len(anonymous_analytics) > 0
    
def test_data_subject_access_request():
    """Test complete data export for access request"""
    # Given: User with comprehensive data
    user = create_test_user(db)
    clients = create_test_clients(db, user.id, count=3)
    usage_logs = create_usage_logs(db, user_id=user.id, count=10)
    
    # When: Data export is requested
    gdpr_service = GDPRService(db)
    export_data = gdpr_service.generate_data_export(user.id)
    
    # Then: All user data is included
    assert "personal_data" in export_data
    assert "usage_data" in export_data
    assert len(export_data["personal_data"]["clients"]) == 3
    assert len(export_data["usage_data"]) == 10
```

### Automated Retention Tests
```python
def test_automated_data_retention():
    """Test automated data retention enforcement"""
    # Given: Old client data beyond retention period
    old_date = datetime.utcnow() - timedelta(days=2600)  # >7 years
    old_client = create_test_client(db, user_id, created_at=old_date)
    old_client.is_active = False  # Inactive client
    
    # When: Retention service runs
    retention_service = DataRetentionService(db)
    retention_service._process_personal_data_retention()
    
    # Then: Old client should be auto-anonymized
    updated_client = db.query(Client).filter(Client.id == old_client.id).first()
    assert updated_client.is_anonymized == True
```

## 📊 Success Metrics

### Compliance Metrics
- **GDPR Request Processing**: 100% of data subject requests processed within 30 days
- **Data Retention Compliance**: 0% overdue personal data beyond retention period
- **Anonymization Accuracy**: 100% successful anonymization without data loss
- **Audit Trail Completeness**: 100% of data operations logged for compliance

### Technical Metrics
- **Export Performance**: <30 seconds for complete data export
- **Anonymization Performance**: <5 minutes for client anonymization
- **Storage Optimization**: 70% reduction in personal data storage after anonymization
- **Analytics Preservation**: 100% of usage analytics preserved in anonymous form

## 📋 Definition of Done

- [ ] **Enhanced Anonymization**: Multi-level data classification and smart anonymization
- [ ] **Data Subject Rights**: Access, rectification, erasure, and portability APIs
- [ ] **Automated Retention**: Daily job for retention policy enforcement
- [ ] **Anonymous Analytics**: Usage data preservation system for anonymized users
- [ ] **Compliance Dashboard**: GDPR compliance status monitoring
- [ ] **Audit Logging**: Complete audit trail for all data operations
- [ ] **Documentation**: GDPR compliance procedures and user guides
- [ ] **Testing**: Comprehensive GDPR compliance test suite
- [ ] **Performance**: All operations meet performance targets
- [ ] **Legal Review**: Legal team approval for GDPR compliance approach

## 🔄 Dependencies & Risks

### Dependencies
- ✅ US001 (Usage Analytics Foundation) - Required for anonymous analytics
- ✅ US002 (Soft Delete System) - Required for data lifecycle management
- ⏳ Legal team review of GDPR compliance approach
- ⏳ Data retention policy definitions

### Risks & Mitigations
- **Risk**: Complex anonymization could break system functionality
  - **Mitigation**: Comprehensive testing, gradual rollout, rollback procedures
- **Risk**: Performance impact of automated retention checks
  - **Mitigation**: Optimize queries, run during off-peak hours, monitoring
- **Risk**: Legal compliance gaps
  - **Mitigation**: Legal review, compliance audit, regular policy updates

## 📞 Stakeholders

**Product Owner**: Legal/Compliance Team  
**Technical Lead**: Backend Engineering, Data Engineering  
**Reviewers**: Privacy Officer, Security Team, External Legal Counsel  
**QA Focus**: Compliance verification, Data integrity, Security testing