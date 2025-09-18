# User Story US003: Selective Transcript Deletion

## Story Overview
**Epic**: Core Data Governance
**Story ID**: US-003
**Priority**: P0 (Critical)
**Effort**: 4 Story Points

## User Story
**As a coach, I want to delete sensitive transcript content while preserving session timing and statistical data so that I can maintain privacy while keeping coaching hour records intact.**

## Business Value
- **Privacy Control**: Users can remove sensitive conversation content
- **Statistical Integrity**: Preserve coaching analytics and hour tracking
- **Selective Deletion**: Granular control over what data to delete
- **Compliance**: Meet privacy requirements while maintaining business needs

## Acceptance Criteria

### ✅ Primary Criteria
- [ ] **AC-003.1**: Users can delete individual transcript segments independently
- [ ] **AC-003.2**: Session duration and timing statistics preserved after transcript deletion
- [ ] **AC-003.3**: Coaching hour calculations unaffected by transcript content deletion
- [ ] **AC-003.4**: Users can delete entire transcript while preserving session metadata
- [ ] **AC-003.5**: Clear distinction between content deletion and session deletion

### 🔧 Technical Criteria
- [ ] **AC-003.6**: Soft delete for transcript segments with anonymized preservation
- [ ] **AC-003.7**: Session statistics calculated from preserved timing data
- [ ] **AC-003.8**: Database maintains referential integrity during partial deletions
- [ ] **AC-003.9**: Audit trail for all transcript deletion actions

### 📊 Quality Criteria
- [ ] **AC-003.10**: 100% accuracy in preserved timing and duration statistics
- [ ] **AC-003.11**: Zero corruption of coaching hour calculations during deletions

## Data Preservation Strategy

### 📊 What Gets Preserved
```json
{
  "session_metadata": {
    "duration_minutes": 45.5,
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T10:45:30Z",
    "participant_count": 2,
    "language": "zh-TW"
  },
  "timing_statistics": {
    "total_segments": 156,
    "average_segment_duration": 3.2,
    "speaker_distribution": {
      "coach": 0.6,
      "client": 0.4
    }
  },
  "quality_metrics": {
    "confidence_average": 0.89,
    "diarization_accuracy": 0.92
  }
}
```

### 🗑️ What Gets Deleted
```json
{
  "transcript_content": {
    "segments": [
      {
        "text": "[DELETED]",
        "speaker": "coach",
        "start_time": 15.3,
        "end_time": 18.7,
        "deleted_at": "2024-01-20T14:30:00Z"
      }
    ]
  }
}
```

## Technical Implementation

### 🗄️ Database Schema Changes
```sql
-- Add soft delete and anonymization to transcript segments
ALTER TABLE transcript_segment
ADD COLUMN deleted_at TIMESTAMP NULL,
ADD COLUMN deletion_type VARCHAR(50), -- 'content_only', 'full_segment'
ADD COLUMN preserved_metadata JSONB;

-- Create transcript deletion audit table
CREATE TABLE transcript_deletion_audit (
  id UUID PRIMARY KEY,
  session_id UUID NOT NULL,
  segment_id UUID,
  deletion_type VARCHAR(50),
  deletion_timestamp TIMESTAMP DEFAULT NOW(),
  user_id UUID REFERENCES "user"(id),
  preserved_statistics JSONB
);

-- Update session table to track transcript status
ALTER TABLE session
ADD COLUMN transcript_segments_total INTEGER DEFAULT 0,
ADD COLUMN transcript_segments_deleted INTEGER DEFAULT 0,
ADD COLUMN transcript_fully_deleted BOOLEAN DEFAULT FALSE;
```

### 🔧 Backend Implementation

#### 1. Selective Deletion Service
```python
# src/coaching_assistant/core/services/transcript_deletion_service.py
from enum import Enum
from typing import List, Optional

class DeletionType(Enum):
    CONTENT_ONLY = "content_only"  # Delete text, preserve timing
    FULL_SEGMENT = "full_segment"  # Delete segment completely
    ENTIRE_TRANSCRIPT = "entire_transcript"  # Delete all content

class TranscriptDeletionService:
    def delete_transcript_segments(
        self,
        session_id: UUID,
        segment_ids: List[UUID],
        deletion_type: DeletionType,
        user_id: UUID
    ) -> DeletionResult:
        """Delete specified transcript segments"""
        # 1. Validate ownership and permissions
        # 2. Preserve timing and statistical metadata
        # 3. Execute deletion based on type
        # 4. Update session statistics
        # 5. Create audit trail
        pass

    def preserve_segment_metadata(
        self,
        segment: TranscriptSegment
    ) -> dict:
        """Extract and preserve important metadata before deletion"""
        return {
            "duration": segment.end_time - segment.start_time,
            "speaker_role": segment.speaker_role,
            "confidence_score": segment.confidence,
            "timestamp": segment.start_time,
            "word_count": len(segment.text.split())
        }

    def calculate_session_statistics(
        self,
        session_id: UUID
    ) -> SessionStatistics:
        """Calculate session stats from preserved metadata"""
        # Use preserved_metadata JSONB to calculate stats
        # even when transcript content is deleted
        pass
```

#### 2. API Endpoints
```python
# src/coaching_assistant/api/controllers/transcript_controller.py
@router.delete("/sessions/{session_id}/transcript/segments")
async def delete_transcript_segments(
    session_id: UUID,
    deletion_request: TranscriptDeletionRequest,
    current_user: User = Depends(get_current_user)
):
    """Delete specific transcript segments with preservation options"""
    pass

@router.delete("/sessions/{session_id}/transcript")
async def delete_entire_transcript(
    session_id: UUID,
    preserve_statistics: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Delete entire transcript while preserving session metadata"""
    pass

@router.get("/sessions/{session_id}/transcript/deletion-preview")
async def preview_transcript_deletion(
    session_id: UUID,
    segment_ids: List[UUID],
    current_user: User = Depends(get_current_user)
):
    """Preview what will be preserved vs deleted"""
    pass
```

### 🌐 Frontend Implementation

#### 1. Selective Deletion Interface
```typescript
// apps/web/components/TranscriptDeletionPanel.tsx
interface TranscriptDeletionPanelProps {
  session: Session;
  segments: TranscriptSegment[];
}

const TranscriptDeletionPanel: React.FC<TranscriptDeletionPanelProps> = ({
  session,
  segments
}) => {
  const [selectedSegments, setSelectedSegments] = useState<UUID[]>([]);
  const [deletionType, setDeletionType] = useState<DeletionType>('content_only');

  return (
    <div className="deletion-panel">
      {/* Segment selection checkboxes */}
      {/* Deletion type radio buttons */}
      {/* Preview of what will be preserved */}
      {/* Confirmation with impact summary */}
    </div>
  );
};
```

#### 2. Deletion Options UI
```typescript
// apps/web/components/DeletionOptionsDialog.tsx
const DeletionOptionsDialog: React.FC = () => {
  return (
    <Dialog>
      <h3>選擇刪除方式</h3>

      <RadioGroup name="deletion-type">
        <Radio value="content_only">
          <strong>僅刪除內容文字</strong>
          <p>保留時間軸、講者分配、統計資料</p>
          <Badge>推薦：保持教練時數完整</Badge>
        </Radio>

        <Radio value="full_segment">
          <strong>完全刪除選定片段</strong>
          <p>刪除內容和時間資訊，可能影響統計</p>
        </Radio>

        <Radio value="entire_transcript">
          <strong>刪除整份逐字稿</strong>
          <p>僅保留會議時長和基本統計</p>
        </Radio>
      </RadioGroup>

      <PreservationPreview />
    </Dialog>
  );
};
```

#### 3. Statistics Preservation Display
```typescript
// apps/web/components/PreservationPreview.tsx
const PreservationPreview: React.FC = ({ deletionType, segments }) => {
  return (
    <div className="preservation-preview">
      <h4>將保留的資料：</h4>
      <ul className="preserved-data">
        <li>✅ 會議時長：45分30秒</li>
        <li>✅ 講者分配比例：教練 60% / 客戶 40%</li>
        <li>✅ 累積教練時數統計</li>
        {deletionType === 'content_only' && (
          <>
            <li>✅ 時間軸和片段結構</li>
            <li>✅ 講者識別資訊</li>
          </>
        )}
      </ul>

      <h4>將刪除的資料：</h4>
      <ul className="deleted-data">
        <li>❌ 逐字稿文字內容</li>
        {deletionType === 'full_segment' && (
          <>
            <li>❌ 選定片段的時間資訊</li>
            <li>❌ 片段的講者識別</li>
          </>
        )}
      </ul>
    </div>
  );
};
```

## Testing Strategy

### 🧪 Unit Tests
```python
# tests/unit/services/test_transcript_deletion_service.py
def test_content_only_deletion_preserves_timing():
    """Test that content-only deletion preserves all timing data"""
    pass

def test_session_statistics_accuracy_after_deletion():
    """Test session statistics remain accurate after partial deletions"""
    pass

def test_coaching_hours_unaffected_by_transcript_deletion():
    """Test coaching hour calculations unchanged by transcript deletions"""
    pass
```

### 🔗 Integration Tests
```python
# tests/integration/test_selective_deletion.py
def test_partial_transcript_deletion_preserves_session():
    """Test that partial transcript deletion doesn't affect session integrity"""
    pass

def test_metadata_preservation_during_deletion():
    """Test that statistical metadata is properly preserved"""
    pass
```

### 🎯 E2E Tests
```typescript
// tests/e2e/selective-deletion.spec.ts
test('user can delete transcript content while preserving statistics', async () => {
  // 1. Navigate to transcript view
  // 2. Select segments for deletion
  // 3. Choose "content only" deletion
  // 4. Verify statistics are preserved
  // 5. Verify coaching hours unchanged
});

test('deletion preview shows accurate preservation summary', async () => {
  // 1. Select segments for deletion
  // 2. Open deletion preview
  // 3. Verify preservation summary is accurate
  // 4. Test different deletion types
});
```

## Verification Procedures

### 🔍 Manual Testing Checklist
- [ ] Upload and process a session with transcript
- [ ] Delete individual segments with content-only option
- [ ] Verify session duration and statistics preserved
- [ ] Delete entire transcript with preservation
- [ ] Check coaching hours remain accurate
- [ ] Verify audit trail completeness

### 📊 Statistical Integrity Verification
```python
# Verification script
def verify_statistical_integrity():
    """Verify statistics remain accurate after deletions"""
    # Compare preserved metadata with original calculations
    # Validate coaching hour totals
    # Check session duration accuracy
```

## Success Metrics
- **Data Accuracy**: 100% accuracy in preserved statistics after deletion
- **User Control**: 95% user satisfaction with deletion granularity
- **System Integrity**: Zero corruption of coaching hour calculations
- **Privacy Compliance**: 100% of sensitive content removable by users

## Risk Mitigation

### ⚠️ Potential Risks
1. **Data Corruption**: Partial deletions might corrupt session integrity
2. **Statistical Errors**: Preserved metadata might become inconsistent
3. **User Confusion**: Complex deletion options might confuse users

### 🛡️ Mitigation Strategies
1. **Atomic Operations**: Ensure all deletion operations are transactional
2. **Validation**: Continuous validation of preserved statistics
3. **Simple Defaults**: Default to safest option (content-only deletion)

## Dependencies
- **Database**: Soft delete schema and metadata preservation
- **Backend**: Selective deletion service and statistics engine
- **Frontend**: Granular deletion UI and preservation preview
- **Analytics**: Updated reporting for partial deletions

## Definition of Done
- [ ] Selective deletion system for transcript segments
- [ ] Multiple deletion types with clear preservation rules
- [ ] Statistical integrity maintained during all deletion types
- [ ] User-friendly deletion interface with preview
- [ ] Complete audit trail for all deletion actions
- [ ] Comprehensive test coverage for all deletion scenarios
- [ ] Documentation for deletion policies and procedures