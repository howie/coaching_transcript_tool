# US001: Usage Analytics Foundation

## 📋 User Story

**As a** business stakeholder  
**I want** independent usage analytics and tracking system  
**So that** usage records are preserved regardless of client/coach deletions and billing is always accurate

## 💼 Business Value

### Current Problem
- Usage records are lost when clients or coaches are deleted from the system
- User.usage_minutes field can become inconsistent with actual transcription activity
- No historical usage data for business analytics or compliance auditing
- Billing inaccuracies due to data loss during client management operations

### Business Impact  
- **Revenue Risk**: Lost usage data = potential billing discrepancies (~$X,XXX/month potential loss)
- **Compliance Risk**: GDPR requires audit trails, current system has gaps  
- **Analytics Gap**: Cannot track user behavior patterns or platform usage trends
- **Support Issues**: No data trail for customer support resolution

### Value Delivered
- **100% Usage Tracking**: Never lose usage records again
- **Business Intelligence**: Historical usage data for growth analytics
- **Compliance Ready**: Complete audit trails for regulatory requirements
- **Billing Accuracy**: Reliable usage data for precise billing calculations

## 🎯 Acceptance Criteria

### Core Requirements
1. **Independent Usage Logging**
   - [ ] Every transcription creates a permanent usage log entry
   - [ ] Usage logs survive client/coach deletions
   - [ ] Usage logs include: session_id, user_id, duration, cost, timestamp, transcription_type

2. **Usage Analytics Aggregation**
   - [ ] Daily batch job aggregates usage data into monthly summaries  
   - [ ] Analytics include: total minutes, session count, cost breakdown, user activity
   - [ ] Aggregations handle client anonymization properly

3. **Integration with Transcription Workflow**
   - [ ] Usage logging happens automatically after successful transcription
   - [ ] Failed transcriptions don't create usage records
   - [ ] User.usage_minutes field stays synchronized with actual usage

4. **API Endpoints**
   - [ ] GET /api/v1/usage/summary - User's current usage summary
   - [ ] GET /api/v1/usage/history - User's historical usage data
   - [ ] GET /api/v1/admin/usage/analytics - Admin analytics (requires admin role)

### Data Requirements
5. **Database Schema**
   - [ ] New `usage_logs` table with proper indexing
   - [ ] New `usage_analytics` table for aggregated data
   - [ ] Foreign key relationships preserve data integrity
   - [ ] Migration handles existing usage data

6. **Data Integrity**
   - [ ] Usage logs are immutable after creation
   - [ ] Referential integrity maintained even after client deletion
   - [ ] Database constraints prevent duplicate usage entries

## 🏗️ Technical Implementation

### Database Schema
```sql
-- Usage log for individual transcription events
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
    session_id UUID NOT NULL REFERENCES session(id) ON DELETE CASCADE,
    client_id UUID REFERENCES client(id) ON DELETE SET NULL,
    
    -- Usage details
    duration_minutes INTEGER NOT NULL,
    duration_seconds INTEGER NOT NULL,
    cost_usd DECIMAL(10,6),
    stt_provider VARCHAR(50) NOT NULL,
    
    -- Transcription type classification  
    transcription_type VARCHAR(20) NOT NULL CHECK (transcription_type IN ('original', 'retry_failed', 'retry_success')),
    
    -- Timestamps
    transcription_started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    transcription_completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    language VARCHAR(20),
    provider_metadata JSONB DEFAULT '{}',
    
    -- Constraints
    UNIQUE(session_id, transcription_type),
    CHECK(duration_minutes >= 0),
    CHECK(duration_seconds >= 0)
);

-- Monthly usage analytics (aggregated data)
CREATE TABLE usage_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
    
    -- Time period
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    
    -- Usage summaries
    total_sessions INTEGER NOT NULL DEFAULT 0,
    total_minutes INTEGER NOT NULL DEFAULT 0,
    total_seconds INTEGER NOT NULL DEFAULT 0,
    total_cost_usd DECIMAL(10,6) DEFAULT 0,
    
    -- Transcription type breakdown
    original_transcriptions INTEGER NOT NULL DEFAULT 0,
    failed_retries INTEGER NOT NULL DEFAULT 0,
    successful_retranscriptions INTEGER NOT NULL DEFAULT 0,
    
    -- Provider breakdown
    google_stt_minutes INTEGER NOT NULL DEFAULT 0,
    assemblyai_minutes INTEGER NOT NULL DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, year, month),
    CHECK(year >= 2025),
    CHECK(month >= 1 AND month <= 12),
    CHECK(total_sessions >= 0),
    CHECK(total_minutes >= 0)
);

-- Indexes for performance
CREATE INDEX idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX idx_usage_logs_session_id ON usage_logs(session_id);
CREATE INDEX idx_usage_logs_created_at ON usage_logs(created_at);
CREATE INDEX idx_usage_analytics_user_month ON usage_analytics(user_id, year, month);
```

### Python Models
```python
# packages/core-logic/src/coaching_assistant/models/usage_log.py
class TranscriptionType(enum.Enum):
    ORIGINAL = "original"  # First transcription attempt
    RETRY_FAILED = "retry_failed"  # Retry after failure (free)
    RETRY_SUCCESS = "retry_success"  # Re-transcription of successful session (charged)

class UsageLog(BaseModel):
    """Individual usage log entry for each transcription event"""
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("session.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("client.id", ondelete="SET NULL"), nullable=True)
    
    duration_minutes = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    cost_usd = Column(Numeric(10, 6), nullable=True)
    stt_provider = Column(String(50), nullable=False)
    transcription_type = Column(Enum(TranscriptionType), nullable=False)
    
    transcription_started_at = Column(DateTime(timezone=True), nullable=False)
    transcription_completed_at = Column(DateTime(timezone=True), nullable=False)
    
    language = Column(String(20), nullable=True)
    provider_metadata = Column(JSONB, default={}, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")
    session = relationship("Session", back_populates="usage_logs")
    client = relationship("Client", back_populates="usage_logs")

class UsageAnalytics(BaseModel):
    """Monthly aggregated usage analytics"""
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    total_sessions = Column(Integer, nullable=False, default=0)
    total_minutes = Column(Integer, nullable=False, default=0)
    total_seconds = Column(Integer, nullable=False, default=0)
    total_cost_usd = Column(Numeric(10, 6), default=0)
    
    original_transcriptions = Column(Integer, nullable=False, default=0)
    failed_retries = Column(Integer, nullable=False, default=0)
    successful_retranscriptions = Column(Integer, nullable=False, default=0)
    
    google_stt_minutes = Column(Integer, nullable=False, default=0)
    assemblyai_minutes = Column(Integer, nullable=False, default=0)
    
    # Relationship
    user = relationship("User", back_populates="usage_analytics")
```

### Integration with Transcription Tasks
```python
# packages/core-logic/src/coaching_assistant/tasks/transcription_tasks.py

def _create_usage_log_entry(db: Session, session: Session, result: TranscriptionResult, transcription_type: TranscriptionType = TranscriptionType.ORIGINAL):
    """Create usage log entry after successful transcription"""
    
    usage_log = UsageLog(
        user_id=session.user_id,
        session_id=session.id,
        client_id=getattr(session, 'client_id', None),  # If session linked to coaching session
        
        duration_minutes=int(result.total_duration_sec / 60),
        duration_seconds=int(result.total_duration_sec),
        cost_usd=result.cost_usd,
        stt_provider=session.stt_provider,
        transcription_type=transcription_type,
        
        transcription_started_at=session.updated_at,  # When processing started
        transcription_completed_at=datetime.utcnow(),
        
        language=session.language,
        provider_metadata=result.provider_metadata
    )
    
    db.add(usage_log)
    db.commit()
    
    # Update user's usage_minutes for plan limit checking
    user = db.query(User).filter(User.id == session.user_id).first()
    user.add_usage(int(result.total_duration_sec / 60))
    db.commit()
    
    logger.info(f"Created usage log entry for session {session.id}: {usage_log.duration_minutes} minutes")
    
    return usage_log

# Modified transcription task
@celery.task(bind=True)
def transcribe_audio_task(self, session_id: str, user_id: str):
    """Enhanced transcription task with usage logging"""
    
    # ... existing transcription logic ...
    
    try:
        # Transcription processing
        result = provider.transcribe(...)
        
        # Save transcript segments (existing logic)
        _save_transcript_segments(db, session_id, result.segments)
        
        # NEW: Create usage log entry
        transcription_type = _determine_transcription_type(db, session_id)
        usage_log = _create_usage_log_entry(db, session, result, transcription_type)
        
        # Mark session as completed
        session.mark_completed(duration_seconds=int(result.total_duration_sec))
        
        # Trigger monthly analytics update (async)
        update_monthly_analytics.delay(user_id, usage_log.created_at.year, usage_log.created_at.month)
        
    except Exception as e:
        # Transcription failed - no usage log created
        session.mark_failed(str(e))
        raise
```

### API Endpoints  
```python
# packages/core-logic/src/coaching_assistant/api/usage.py

@router.get("/summary")
async def get_usage_summary(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get user's current usage summary"""
    
    # Current month usage from analytics
    current_month = datetime.now()
    analytics = db.query(UsageAnalytics).filter(
        UsageAnalytics.user_id == current_user.id,
        UsageAnalytics.year == current_month.year,
        UsageAnalytics.month == current_month.month
    ).first()
    
    # Real-time usage from logs (for current month)
    current_month_logs = db.query(UsageLog).filter(
        UsageLog.user_id == current_user.id,
        extract('year', UsageLog.created_at) == current_month.year,
        extract('month', UsageLog.created_at) == current_month.month
    ).all()
    
    return {
        "current_month": {
            "total_minutes": sum(log.duration_minutes for log in current_month_logs),
            "total_sessions": len(current_month_logs),
            "total_cost": sum(log.cost_usd or 0 for log in current_month_logs),
            "breakdown": {
                "original": len([l for l in current_month_logs if l.transcription_type == TranscriptionType.ORIGINAL]),
                "retries": len([l for l in current_month_logs if l.transcription_type == TranscriptionType.RETRY_FAILED]),
                "re_transcriptions": len([l for l in current_month_logs if l.transcription_type == TranscriptionType.RETRY_SUCCESS])
            }
        },
        "plan_limits": {
            "plan": current_user.plan.value,
            "limit_minutes": _get_plan_limit(current_user.plan),
            "remaining_minutes": max(0, _get_plan_limit(current_user.plan) - current_user.usage_minutes)
        }
    }
```

## 🧪 Test Scenarios

### Unit Tests
```python
def test_usage_log_creation_success():
    """Test usage log created after successful transcription"""
    # Given: Completed transcription session
    # When: Usage log creation is triggered
    # Then: Usage log entry created with correct data
    
def test_usage_log_survives_client_deletion():
    """Test usage logs remain after client deletion"""
    # Given: Client with usage logs
    # When: Client is deleted
    # Then: Usage logs remain queryable, client_id becomes null
    
def test_user_usage_minutes_synchronization():
    """Test User.usage_minutes stays in sync with usage logs"""
    # Given: Multiple transcription sessions
    # When: Usage logs are created
    # Then: User.usage_minutes equals sum of usage log minutes
```

### Integration Tests
```bash
# Test: End-to-end usage tracking
curl -X POST /api/v1/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "Usage Test", "language": "en-US"}'

# Upload and process audio file
curl -X POST /api/v1/sessions/$SESSION_ID/upload-url
curl -X PUT $UPLOAD_URL --data-binary @test-audio.mp3
curl -X POST /api/v1/sessions/$SESSION_ID/start-transcription

# Wait for completion then verify usage log
curl -X GET /api/v1/usage/summary

# Expected: Usage log entry created, User.usage_minutes updated
```

## 📊 Success Metrics

### Technical Metrics
- **Usage Log Accuracy**: 100% of successful transcriptions create usage logs
- **Data Consistency**: User.usage_minutes matches sum of usage logs within 1 minute
- **Performance Impact**: <50ms additional latency for usage log creation
- **Storage Efficiency**: Usage logs table size stays <10MB per 1000 sessions

### Business Metrics
- **Data Retention**: 0% usage data loss during client deletion operations
- **Billing Accuracy**: 100% of chargeable transcriptions properly recorded
- **Analytics Availability**: Historical usage data available for business intelligence

## ⚡ Performance Considerations

### Database Optimization
- Partitioning usage_logs table by month for large datasets
- Index optimization for common query patterns
- Async analytics aggregation to avoid blocking transcription workflow

### Scalability Planning  
- Usage logs designed for 100,000+ entries per month
- Analytics aggregation handles user growth to 10,000+ active users
- Monitoring for query performance degradation

## 🔒 Security & Compliance

### Data Protection
- Usage logs contain no personal information (only IDs and metadata)
- Client PII removal doesn't affect usage analytics
- Audit trail for all usage log operations

### GDPR Compliance
- Usage logs support "right to portability" (data export)
- Personal data anonymization doesn't break usage analytics
- Data retention policies separate personal data from usage metrics

## 📋 Definition of Done

- [ ] **Database Schema**: Migration creates usage_logs and usage_analytics tables
- [ ] **Models**: Python models with proper relationships and validation
- [ ] **Integration**: Transcription tasks create usage logs automatically
- [ ] **API Endpoints**: Usage summary and history endpoints working
- [ ] **User Sync**: User.usage_minutes stays synchronized with usage logs
- [ ] **Unit Tests**: >90% coverage for usage logging components
- [ ] **Integration Tests**: End-to-end usage tracking verified
- [ ] **Performance**: <50ms additional latency for usage log creation
- [ ] **Documentation**: API documentation and usage guide updated
- [ ] **Monitoring**: Usage log creation success/failure metrics in place

## 🔄 Dependencies & Risks

### Dependencies
- ✅ Current transcription system is stable (prerequisite met)
- ⏳ Database migration tooling ready
- ⏳ Celery task queue for async analytics

### Risks & Mitigations
- **Risk**: Usage log creation failures could impact transcription
  - **Mitigation**: Wrap in try/catch, log errors, don't block transcription completion
- **Risk**: Large usage_logs table performance impact
  - **Mitigation**: Implement table partitioning, regular archiving strategy
- **Risk**: Analytics aggregation performance with scale
  - **Mitigation**: Batch processing, database query optimization

## 📞 Stakeholders

**Product Owner**: Business Team  
**Technical Lead**: Backend Engineering  
**Reviewers**: Legal (GDPR), Finance (Billing)  
**QA Focus**: Data integrity, Performance testing