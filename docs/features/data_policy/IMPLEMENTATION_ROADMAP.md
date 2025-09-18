# Data Policy Implementation Roadmap

## 📋 Overview
This roadmap outlines the implementation strategy for comprehensive data retention policies, focusing on audio TTL, coaching session protection, and selective transcript deletion.

## 🎯 Implementation Priorities

### Phase 1: Audio TTL & Auto-Delete (Week 1)
**Critical Foundation** - GDPR compliance and cost reduction

| Task | Owner | Effort | Dependencies |
|------|-------|--------|--------------|
| GCS Bucket TTL Configuration | DevOps | 1d | Terraform access |
| Backend Audio Cleanup Service | Backend | 2d | GCS configuration |
| Frontend Upload Warnings | Frontend | 1d | UI/UX design |
| Testing & Verification | QA | 1d | All components |

### Phase 2: Coaching Session Protection (Week 2)
**Data Integrity** - Protect accumulated coaching hours

| Task | Owner | Effort | Dependencies |
|------|-------|--------|--------------|
| Soft Delete Schema | Backend | 1d | Database access |
| Session Deletion Service | Backend | 2d | Soft delete schema |
| Warning Dialog UI | Frontend | 2d | UX requirements |
| Audit Trail System | Backend | 1d | Database schema |

### Phase 3: Selective Transcript Deletion (Week 3)
**Granular Privacy Control** - User-controlled content deletion

| Task | Owner | Effort | Dependencies |
|------|-------|--------|--------------|
| Transcript Deletion Schema | Backend | 1d | Session protection |
| Selective Deletion API | Backend | 3d | Database schema |
| Deletion Interface UI | Frontend | 3d | API completion |
| Statistics Preservation | Backend | 2d | All components |

### Phase 4: Verification & Monitoring (Week 4)
**Quality Assurance** - Comprehensive testing and monitoring

| Task | Owner | Effort | Dependencies |
|------|-------|--------|--------------|
| Automated Testing Suite | QA | 3d | All features |
| Monitoring & Alerts | DevOps | 2d | Infrastructure |
| Documentation & Training | Tech Writer | 2d | Feature completion |
| Production Deployment | DevOps | 1d | All testing |

## 🔧 Technical Implementation Tasks

### 🏗️ Infrastructure Tasks

#### 1. Terraform Configuration Updates
```bash
# Priority: P0 (Required for Phase 1)
# Estimated Effort: 4 hours
# Owner: DevOps Team

# Files to update:
- terraform/gcp/storage.tf
- terraform/gcp/variables.tf
- terraform/environments/production.tfvars
- terraform/environments/development.tfvars

# Tasks:
1. Add GCS lifecycle policies for audio buckets
2. Configure 24-hour TTL for both prod/dev environments
3. Add monitoring for TTL policy compliance
4. Update bucket permissions for cleanup operations
```

#### 2. Database Schema Migrations
```sql
-- Priority: P0 (Required for Phase 2)
-- Estimated Effort: 6 hours
-- Owner: Backend Team

-- Migration 001: Audio TTL tracking
ALTER TABLE session
ADD COLUMN audio_deleted_at TIMESTAMP NULL,
ADD COLUMN audio_ttl_expires_at TIMESTAMP NULL;

-- Migration 002: Coaching session soft delete
ALTER TABLE coaching_session
ADD COLUMN deleted_at TIMESTAMP NULL,
ADD COLUMN deletion_reason VARCHAR(255),
ADD COLUMN deleted_by_user_id UUID REFERENCES "user"(id);

-- Migration 003: Transcript selective deletion
ALTER TABLE transcript_segment
ADD COLUMN deleted_at TIMESTAMP NULL,
ADD COLUMN deletion_type VARCHAR(50),
ADD COLUMN preserved_metadata JSONB;

-- Migration 004: Audit tables
CREATE TABLE deletion_audit_log (
  id UUID PRIMARY KEY,
  entity_type VARCHAR(50),
  entity_id UUID,
  deletion_type VARCHAR(20),
  requested_by UUID REFERENCES "user"(id),
  executed_at TIMESTAMP DEFAULT NOW(),
  reason VARCHAR(200),
  preserved_data JSONB
);
```

### 🔧 Backend Development Tasks

#### 1. Audio TTL Implementation
```python
# Priority: P0
# Estimated Effort: 12 hours
# Owner: Backend Team

# New files to create:
- src/coaching_assistant/tasks/audio_cleanup.py
- src/coaching_assistant/core/services/audio_ttl_service.py
- src/coaching_assistant/infrastructure/gcs_lifecycle_client.py

# Existing files to modify:
- src/coaching_assistant/api/controllers/session_controller.py
- src/coaching_assistant/config/settings.py

# Key tasks:
1. Implement Celery task for TTL monitoring
2. Add audio file status tracking
3. Handle missing audio file scenarios
4. Update upload endpoint with TTL info
```

#### 2. Session Protection Service
```python
# Priority: P1
# Estimated Effort: 16 hours
# Owner: Backend Team

# New files to create:
- src/coaching_assistant/core/services/session_deletion_service.py
- src/coaching_assistant/core/models/deletion_audit.py
- src/coaching_assistant/api/schemas/deletion_schemas.py

# Key tasks:
1. Implement soft delete for coaching sessions
2. Create deletion impact calculation
3. Build audit trail system
4. Add coaching hours recalculation logic
```

#### 3. Selective Deletion Service
```python
# Priority: P1
# Estimated Effort: 20 hours
# Owner: Backend Team

# New files to create:
- src/coaching_assistant/core/services/transcript_deletion_service.py
- src/coaching_assistant/core/models/transcript_deletion.py
- src/coaching_assistant/utils/metadata_preservation.py

# Key tasks:
1. Implement granular transcript deletion
2. Create metadata preservation logic
3. Build statistics recalculation engine
4. Add deletion type handling (content vs full)
```

### 🌐 Frontend Development Tasks

#### 1. Upload Warning Components
```typescript
// Priority: P0
// Estimated Effort: 8 hours
// Owner: Frontend Team

// New components to create:
- apps/web/components/AudioTTLWarning.tsx
- apps/web/components/UploadRetentionNotice.tsx
- apps/web/hooks/useAudioTTL.ts

// Existing components to modify:
- apps/web/components/AudioUploader.tsx
- apps/web/components/SessionDetails.tsx

// Key tasks:
1. Add prominent 24-hour deletion warning
2. Show audio availability status
3. Handle expired audio file states
4. Update upload flow with retention info
```

#### 2. Session Deletion Protection UI
```typescript
// Priority: P1
// Estimated Effort: 16 hours
// Owner: Frontend Team

// New components to create:
- apps/web/components/SessionDeletionDialog.tsx
- apps/web/components/DeletionImpactPreview.tsx
- apps/web/components/CoachingHoursWarning.tsx

// Key tasks:
1. Create two-step deletion confirmation
2. Show coaching hours impact
3. Add deletion reason collection
4. Implement protection notices
```

#### 3. Selective Deletion Interface
```typescript
// Priority: P1
// Estimated Effort: 24 hours
// Owner: Frontend Team

// New components to create:
- apps/web/components/TranscriptDeletionPanel.tsx
- apps/web/components/DeletionOptionsDialog.tsx
- apps/web/components/PreservationPreview.tsx
- apps/web/components/SegmentSelector.tsx

// Key tasks:
1. Build granular segment selection
2. Create deletion type selection
3. Show preservation preview
4. Handle batch deletion operations
```

## 🧪 Testing Strategy

### 🔬 Unit Testing Plan
```bash
# Total Estimated Effort: 24 hours
# Owner: Development Teams

# Backend Unit Tests (16 hours)
tests/unit/tasks/test_audio_cleanup.py
tests/unit/services/test_session_deletion_service.py
tests/unit/services/test_transcript_deletion_service.py
tests/unit/utils/test_metadata_preservation.py

# Frontend Unit Tests (8 hours)
tests/unit/components/SessionDeletionDialog.test.tsx
tests/unit/components/TranscriptDeletionPanel.test.tsx
tests/unit/hooks/useAudioTTL.test.ts
```

### 🔗 Integration Testing Plan
```bash
# Total Estimated Effort: 32 hours
# Owner: QA Team

# Database Integration Tests (12 hours)
tests/integration/test_audio_ttl_compliance.py
tests/integration/test_session_protection.py
tests/integration/test_selective_deletion.py

# API Integration Tests (12 hours)
tests/integration/api/test_deletion_endpoints.py
tests/integration/api/test_ttl_endpoints.py
tests/integration/api/test_preservation_endpoints.py

# E2E Workflow Tests (8 hours)
tests/e2e/audio-lifecycle.spec.ts
tests/e2e/session-protection.spec.ts
tests/e2e/selective-deletion.spec.ts
```

### 🎯 Manual Testing Checklist
```markdown
# Audio TTL Testing (4 hours)
- [ ] Upload audio file and verify TTL warning shown
- [ ] Wait 24+ hours and verify auto-deletion
- [ ] Test API handling of missing audio files
- [ ] Verify GCS bucket lifecycle policy working

# Session Protection Testing (4 hours)
- [ ] Attempt session deletion and verify warning
- [ ] Test two-step confirmation process
- [ ] Verify coaching hours impact calculation
- [ ] Test audit trail creation

# Selective Deletion Testing (6 hours)
- [ ] Test individual segment deletion
- [ ] Verify metadata preservation accuracy
- [ ] Test full transcript deletion with stats preservation
- [ ] Verify UI shows correct preservation preview
```

## 📊 Monitoring & Verification

### 🔍 Automated Monitoring
```python
# Priority: P1
# Estimated Effort: 8 hours
# Owner: DevOps Team

# Monitoring scripts to create:
scripts/monitor_audio_ttl_compliance.py
scripts/verify_coaching_hours_integrity.py
scripts/check_deletion_audit_completeness.py

# Alerts to configure:
- Audio files older than 25 hours detected
- Coaching hours calculation errors
- Missing deletion audit entries
- GCS TTL policy failures
```

### 📈 Success Metrics Dashboard
```typescript
// Priority: P2
// Estimated Effort: 12 hours
// Owner: Frontend Team

// Dashboard components:
- TTL Compliance Rate (target: 100%)
- Storage Cost Reduction (target: 75-80%)
- Accidental Deletion Rate (target: 0%)
- User Satisfaction Score (target: >90%)
```

## 🚀 Deployment Strategy

### 🔄 Rollout Plan
1. **Development Environment** (Week 1)
   - Deploy infrastructure changes
   - Test basic functionality
   - Verify TTL policies working

2. **Staging Environment** (Week 2-3)
   - Full feature testing
   - User acceptance testing
   - Performance validation

3. **Production Deployment** (Week 4)
   - Blue-green deployment
   - Gradual feature rollout
   - Real-time monitoring

### 🛡️ Risk Mitigation
```markdown
# Deployment Risks & Mitigation

Risk: Data loss during migration
Mitigation: Full database backup before schema changes

Risk: TTL policy too aggressive
Mitigation: Start with 48-hour TTL, reduce to 24-hour after validation

Risk: User confusion with new deletion flow
Mitigation: In-app tutorials and comprehensive documentation

Risk: Performance impact from new auditing
Mitigation: Async audit logging and database indexing
```

## 📚 Documentation Requirements

### 📖 User Documentation (8 hours)
- Data retention policy explanation
- Deletion options guide
- Coaching hours protection explanation
- Privacy control tutorials

### 🔧 Technical Documentation (12 hours)
- API endpoint documentation
- Database schema documentation
- Deployment procedures
- Monitoring and alerting setup

### 📋 Training Materials (6 hours)
- Admin training for data governance
- Support team training for user questions
- Developer onboarding for new retention policies

## 🏁 Definition of Done

### ✅ Feature Completion Criteria
- [ ] All audio files auto-delete after exactly 24 hours
- [ ] Coaching sessions protected with two-step deletion
- [ ] Selective transcript deletion preserves statistics
- [ ] Complete audit trail for all deletion actions
- [ ] Comprehensive test coverage (>90%)
- [ ] Performance impact <10% on existing operations
- [ ] User documentation complete and published
- [ ] Monitoring and alerting operational

### 📊 Success Validation
- [ ] TTL compliance rate: 100%
- [ ] Storage cost reduction: 75-80%
- [ ] Zero accidental coaching hour data loss
- [ ] User satisfaction score: >90%
- [ ] System uptime maintained: >99.9%