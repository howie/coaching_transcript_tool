# User Story US002: Coaching Session Data Protection

## Story Overview
**Epic**: Core Data Governance
**Story ID**: US-002
**Priority**: P0 (Critical)
**Effort**: 3 Story Points

## User Story
**As a coach, I want my coaching session records preserved for accurate hour tracking, but I want strong warnings when attempting deletion so that I don't accidentally lose accumulated coaching time data.**

## Business Value
- **Coaching Hour Integrity**: Accurate tracking of professional development hours
- **Business Intelligence**: Preserved coaching statistics for analytics
- **User Protection**: Prevents accidental loss of valuable coaching history
- **Compliance**: Maintains audit trail for professional certification requirements

## Acceptance Criteria

### ✅ Primary Criteria
- [ ] **AC-002.1**: Coaching session records preserved permanently by default
- [ ] **AC-002.2**: Clear warning dialog appears when user attempts session deletion
- [ ] **AC-002.3**: Deletion warning explains impact on accumulated coaching hours
- [ ] **AC-002.4**: Two-step confirmation required for session deletion
- [ ] **AC-002.5**: Session statistics preserved even when session is deleted

### 🔧 Technical Criteria
- [ ] **AC-002.6**: Soft delete implementation for coaching sessions
- [ ] **AC-002.7**: Statistics aggregation unaffected by session soft deletes
- [ ] **AC-002.8**: Database constraints prevent accidental hard deletes
- [ ] **AC-002.9**: Audit trail for all session deletion actions

### 📊 Quality Criteria
- [ ] **AC-002.10**: Zero accidental session deletions after warning implementation
- [ ] **AC-002.11**: 100% accuracy in coaching hour calculations

## UI/UX Requirements

### 🚨 Deletion Warning Dialog
```
⚠️ 確認刪除教練會議記錄

您即將刪除此教練會議記錄。請注意：

❌ 此操作將影響您的累積教練時數統計
❌ 相關的逐字稿內容將一併移除
✅ 會保留匿名化的統計資料供分析使用

目前累積教練時數：125.5 小時
刪除後將變為：123.0 小時 (-2.5 小時)

[ ] 我了解此操作的影響，仍要繼續刪除
[取消] [確認刪除]
```

### 📊 Session Preservation Notice
```
💡 教練會議記錄預設永久保存

為了準確追蹤您的教練時數，所有會議記錄預設永久保存。
您可以隨時刪除個別逐字稿內容，但會議統計資料將保留。

了解更多關於資料保存政策 →
```

## Technical Implementation

### 🗄️ Database Schema Changes
```sql
-- Add soft delete and audit tracking to coaching sessions
ALTER TABLE coaching_session
ADD COLUMN deleted_at TIMESTAMP NULL,
ADD COLUMN deletion_reason VARCHAR(255),
ADD COLUMN deleted_by_user_id UUID REFERENCES "user"(id);

-- Create session deletion audit table
CREATE TABLE session_deletion_audit (
  id UUID PRIMARY KEY,
  session_id UUID NOT NULL,
  session_duration_minutes DECIMAL(8,2),
  deletion_timestamp TIMESTAMP DEFAULT NOW(),
  user_id UUID REFERENCES "user"(id),
  deletion_reason VARCHAR(255),
  preserved_statistics JSONB
);

-- Add index for soft delete queries
CREATE INDEX idx_coaching_session_active
ON coaching_session (user_id, deleted_at)
WHERE deleted_at IS NULL;
```

### 🔧 Backend Implementation

#### 1. Soft Delete Service
```python
# src/coaching_assistant/core/services/session_deletion_service.py
class SessionDeletionService:
    def soft_delete_session(
        self,
        session_id: UUID,
        user_id: UUID,
        reason: str
    ) -> SessionDeletionResult:
        """Soft delete session while preserving statistics"""
        # 1. Verify session ownership
        # 2. Calculate impact on coaching hours
        # 3. Preserve statistics in audit table
        # 4. Soft delete session record
        # 5. Update user's total coaching hours
        pass

    def calculate_deletion_impact(
        self,
        session_id: UUID
    ) -> DeletionImpact:
        """Calculate impact on user's coaching statistics"""
        pass
```

#### 2. API Endpoints
```python
# src/coaching_assistant/api/controllers/session_controller.py
@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    deletion_request: SessionDeletionRequest,
    current_user: User = Depends(get_current_user)
):
    """Delete coaching session with protection warnings"""
    # 1. Validate deletion request with confirmation flag
    # 2. Calculate impact on coaching hours
    # 3. Execute soft delete
    # 4. Return updated statistics
    pass

@router.get("/sessions/{session_id}/deletion-impact")
async def get_deletion_impact(
    session_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Get deletion impact preview for warning dialog"""
    pass
```

### 🌐 Frontend Implementation

#### 1. Deletion Warning Component
```typescript
// apps/web/components/SessionDeletionDialog.tsx
interface SessionDeletionDialogProps {
  session: CoachingSession;
  onConfirm: (reason: string) => void;
  onCancel: () => void;
}

const SessionDeletionDialog: React.FC<SessionDeletionDialogProps> = ({
  session,
  onConfirm,
  onCancel
}) => {
  const [impact, setImpact] = useState<DeletionImpact | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [reason, setReason] = useState('');

  // Calculate deletion impact on component mount
  useEffect(() => {
    fetchDeletionImpact(session.id).then(setImpact);
  }, [session.id]);

  return (
    <Dialog>
      {/* Warning content with coaching hours impact */}
      {/* Confirmation checkbox */}
      {/* Reason input field */}
    </Dialog>
  );
};
```

#### 2. Statistics Protection Notice
```typescript
// apps/web/components/SessionPreservationNotice.tsx
const SessionPreservationNotice: React.FC = () => {
  return (
    <InfoCard>
      <InfoIcon />
      <div>
        <h3>教練會議記錄預設永久保存</h3>
        <p>為了準確追蹤您的教練時數，所有會議記錄預設永久保存...</p>
        <Link href="/data-policy">了解更多關於資料保存政策</Link>
      </div>
    </InfoCard>
  );
};
```

## Testing Strategy

### 🧪 Unit Tests
```python
# tests/unit/services/test_session_deletion_service.py
def test_soft_delete_preserves_statistics():
    """Test that soft delete preserves coaching hour statistics"""
    pass

def test_deletion_impact_calculation():
    """Test accurate calculation of deletion impact"""
    pass

def test_unauthorized_deletion_blocked():
    """Test that users cannot delete others' sessions"""
    pass
```

### 🔗 Integration Tests
```python
# tests/integration/test_session_protection.py
def test_coaching_hours_accuracy_after_deletion():
    """Test coaching hour calculations remain accurate after deletions"""
    pass

def test_audit_trail_completeness():
    """Test that all deletion actions are properly audited"""
    pass
```

### 🎯 E2E Tests
```typescript
// tests/e2e/session-protection.spec.ts
test('deletion warning shows coaching hours impact', async () => {
  // 1. Navigate to session details
  // 2. Click delete button
  // 3. Verify warning dialog shows correct impact
  // 4. Verify two-step confirmation required
});

test('session statistics preserved after deletion', async () => {
  // 1. Note current coaching hours
  // 2. Delete a session with confirmation
  // 3. Verify hours updated correctly but statistics preserved
});
```

## Verification Procedures

### 🔍 Manual Testing Checklist
- [ ] Upload and process a coaching session
- [ ] Attempt to delete session - verify warning appears
- [ ] Check warning shows accurate coaching hours impact
- [ ] Confirm deletion requires two-step process
- [ ] Verify statistics are preserved in database
- [ ] Check coaching hours total is updated correctly

### 📊 Automated Monitoring
```python
# Monitoring script
def verify_session_protection():
    """Daily verification of session protection measures"""
    # Check no hard deletes occurred
    # Verify audit trail completeness
    # Validate coaching hour calculation accuracy
```

## Success Metrics
- **Accidental Deletions**: Reduce to 0% (from current unknown baseline)
- **User Awareness**: 100% of deletion attempts show warning
- **Data Integrity**: 100% accuracy in coaching hour calculations
- **Audit Coverage**: 100% of deletion actions logged

## Risk Mitigation

### ⚠️ Potential Risks
1. **User Confusion**: Users may not understand why deletion is restricted
2. **Storage Growth**: Permanent session retention increases storage costs
3. **Privacy Concerns**: Users may want complete data deletion

### 🛡️ Mitigation Strategies
1. **Clear Communication**: Detailed explanation of preservation benefits
2. **Selective Deletion**: Allow transcript content deletion while preserving session metadata
3. **Privacy Options**: Provide data anonymization instead of deletion

## Dependencies
- **Database**: Soft delete schema implementation
- **Backend**: Session deletion service and audit system
- **Frontend**: Warning dialogs and confirmation UI
- **Analytics**: Updated reporting to handle soft deletes

## Definition of Done
- [ ] Soft delete system implemented for coaching sessions
- [ ] Two-step deletion confirmation with impact warning
- [ ] Statistics preservation during deletion process
- [ ] Complete audit trail for all deletion actions
- [ ] User education about session preservation benefits
- [ ] Comprehensive test coverage for protection measures
- [ ] Documentation updated with protection policies