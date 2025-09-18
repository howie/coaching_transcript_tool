# User Story US001: Audio File TTL & Auto-Delete Implementation

## Story Overview
**Epic**: Core Data Governance
**Story ID**: US-001
**Priority**: P0 (Critical)
**Effort**: 5 Story Points

## User Story
**As a system administrator, I want audio files to automatically delete after 24 hours so that we comply with GDPR data minimization requirements and reduce storage costs.**

## Business Value
- **GDPR Compliance**: Automatic data minimization reduces privacy risks
- **Cost Reduction**: Significant reduction in GCS storage costs (~80% savings)
- **Security**: Minimizes exposure window for sensitive audio data
- **Trust**: Demonstrates commitment to user privacy

## Acceptance Criteria

### ✅ Primary Criteria
- [ ] **AC-001.1**: Audio files automatically delete exactly 24 hours after upload
- [ ] **AC-001.2**: TTL policy applies to both production and development buckets
- [ ] **AC-001.3**: Users receive notification before upload explaining 24-hour retention
- [ ] **AC-001.4**: System gracefully handles attempts to access deleted audio files

### 🔧 Technical Criteria
- [ ] **AC-001.5**: GCS bucket lifecycle policy configured for 1-day TTL
- [ ] **AC-001.6**: Terraform configuration includes TTL settings for both environments
- [ ] **AC-001.7**: API endpoints handle "audio file not found" scenarios
- [ ] **AC-001.8**: Database records updated to reflect audio deletion status

### 📊 Quality Criteria
- [ ] **AC-001.9**: 100% of audio files deleted within 24±1 hours
- [ ] **AC-001.10**: Zero impact on transcription processing pipeline

## Implementation Tasks

### 🏗️ Infrastructure (Terraform)
```hcl
# terraform/gcp/storage.tf
resource "google_storage_bucket" "audio_storage" {
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 1  # 1 day
    }
  }
}
```

### 🔧 Backend Implementation

#### 1. Update GCS Configuration
- **File**: `src/coaching_assistant/config/settings.py`
- **Action**: Add TTL configuration settings
- **Test**: Verify TTL settings are properly loaded

#### 2. API Response Handling
- **File**: `src/coaching_assistant/api/controllers/session_controller.py`
- **Action**: Handle audio file not found exceptions
- **Test**: Mock deleted audio file scenarios

#### 3. Database Schema Update
```sql
-- Add audio deletion tracking
ALTER TABLE session
ADD COLUMN audio_deleted_at TIMESTAMP NULL,
ADD COLUMN audio_ttl_expires_at TIMESTAMP NULL;
```

#### 4. Cleanup Service
- **File**: `src/coaching_assistant/tasks/audio_cleanup.py`
- **Action**: Celery task to update database when files expire
- **Test**: Verify database updates match actual file deletion

### 🌐 Frontend Implementation

#### 1. Upload Warning Component
- **File**: `apps/web/components/AudioUploader.tsx`
- **Action**: Add prominent 24-hour deletion warning
- **Test**: Verify warning is visible and clear

#### 2. Session Status Display
- **File**: `apps/web/components/SessionDetails.tsx`
- **Action**: Show audio availability status
- **Test**: Handle both available and deleted audio states

## Testing Strategy

### 🧪 Unit Tests
```python
# tests/unit/tasks/test_audio_cleanup.py
def test_audio_cleanup_task():
    # Test database updates when audio expires
    pass

def test_handle_missing_audio_file():
    # Test API graceful handling of deleted files
    pass
```

### 🔗 Integration Tests
```python
# tests/integration/test_audio_ttl.py
def test_gcs_ttl_policy():
    # Verify GCS actually deletes files after 24 hours
    pass

def test_transcription_with_expired_audio():
    # Ensure transcription works even if audio is deleted
    pass
```

### 🎯 E2E Tests
```typescript
// tests/e2e/audio-lifecycle.spec.ts
test('user sees audio deletion warning on upload', async () => {
  // Verify upload warning is displayed
});

test('session shows audio expired status', async () => {
  // Test UI handles expired audio gracefully
});
```

## Verification Procedures

### 🔍 Manual Verification
1. **Upload Test File**: Upload audio file to development environment
2. **Verify TTL**: Check GCS console shows 24-hour expiration
3. **Wait for Deletion**: Confirm file actually deletes after 24 hours
4. **Test API Response**: Verify API handles missing file gracefully
5. **Check Database**: Confirm database records updated correctly

### 📊 Automated Monitoring
```python
# Monitoring script
def verify_audio_ttl_compliance():
    """Daily check for TTL policy compliance"""
    # Check no audio files older than 25 hours exist
    # Alert if TTL policy not working
```

## Success Metrics
- **Deletion Accuracy**: 100% of files deleted within 24±1 hours
- **Storage Cost Reduction**: 75-80% reduction in audio storage costs
- **API Reliability**: 99.9% uptime handling missing audio scenarios
- **User Awareness**: 100% of users see deletion warning before upload

## Risk Mitigation

### ⚠️ Potential Risks
1. **Processing Delays**: Audio deleted before transcription completes
2. **User Confusion**: Users expect permanent audio storage
3. **Debug Challenges**: Cannot access audio for troubleshooting after 24h

### 🛡️ Mitigation Strategies
1. **Priority Processing**: High-priority queue for audio transcription
2. **Clear Communication**: Prominent warnings and documentation
3. **Debug Window**: Ensure all debug/troubleshooting happens within 24h

## Dependencies
- **Terraform**: GCS bucket lifecycle configuration
- **Backend**: Audio file handling and cleanup services
- **Frontend**: User notification and status display
- **Monitoring**: TTL compliance verification

## Definition of Done
- [ ] GCS TTL policy configured and tested
- [ ] All audio files auto-delete after exactly 24 hours
- [ ] Users clearly warned about 24-hour retention
- [ ] API gracefully handles deleted audio files
- [ ] Database tracking of audio deletion status
- [ ] Comprehensive test coverage (unit + integration + E2E)
- [ ] Monitoring alerts for TTL compliance
- [ ] Documentation updated with new retention policy