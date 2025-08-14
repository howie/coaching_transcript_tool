# AI Audio Transcription Bug Fixes - August 14, 2025

## 🎯 Critical Issue: Speaker Role Mapping System Inconsistencies

### Problem Summary
Multiple critical bugs were affecting the speaker role assignment system across both subtitle upload and automatic transcription workflows, causing user-selected roles to be incorrectly overridden or ignored.

## 🔍 Root Cause Analysis

### Issue 1: Subtitle Upload Role Mapping Failure
**Problem**: User-selected speaker roles (coach/client) during subtitle upload were being overridden when the frontend refetched transcript data, causing all speakers to become "client".

**Root Cause**: Frontend and backend used different speaker key normalization algorithms:
- **Frontend**: `speakerName.toLowerCase().replace(/\s+/g, '_').replace(/[^\w_]/g, '')`
- **Backend**: `speaker_name.lower().replace(' ', '_')` (only replaced spaces)

**Example Failure**:
- Frontend generated: `speaker_howie_yu` 
- Backend generated: `speaker_howie yu` (space not handled)
- Result: Key mismatch → role mapping failed → default to 'client'

### Issue 2: Frontend/Backend Role System Inconsistency
**Problem**: Frontend used numeric speaker IDs (COACH: 0, CLIENT: 1) while backend expected different convention (1=coach, 2=client).

**Root Cause**: Mixed conventions led to confusion and incorrect role assignments after transcript processing.

### Issue 3: Celery Transcription Task Role Assignment Failure
**Problem**: AssemblyAI transcription results weren't properly converting speaker IDs and role assignments weren't being persisted to the database.

**Root Causes**:
- `_convert_speaker_id()` mapped "A"→0, "B"→1, but frontend expected 1-based IDs
- Role assignments only stored in provider_metadata, not accessible to frontend APIs
- Missing SessionRole database records for automatic role assignments

## 🛠️ Comprehensive Solutions Implemented

### 1. Speaker Key Normalization Unification
**Backend Changes** (`coaching_sessions.py`):
```python
# OLD (inconsistent)
speaker_key = f"speaker_{speaker_name.lower().replace(' ', '_')}"

# NEW (matches frontend)
normalized_name = re.sub(r'[^\w_]', '', speaker_name.lower().replace(' ', '_'))
speaker_key = f"speaker_{normalized_name}"
```

**Applied to**:
- VTT parser (both `<v>` format and prefix format)
- SRT parser (prefix format)
- Ensures consistent speaker key generation across all subtitle formats

### 2. Role System Migration to String Enums
**Frontend Changes** (`page.tsx`):
```typescript
// OLD (numeric IDs - confusing)
const SPEAKER_IDS = {
  COACH: 0,
  CLIENT: 1
} as const;

// NEW (string enums - clear)
const SPEAKER_ROLES = {
  COACH: 'coach' as const,
  CLIENT: 'client' as const
} as const;
```

**Updated Functions**:
- `getSpeakerRoleFromId` → `getSpeakerRoleFromSegment`
- Prioritizes segment.role field when available
- Falls back to role_assignments or numeric convention
- All role detection logic now uses string enums

**Backend Enhancement**:
- VTT/SRT parsers now generate both `speaker_id` (backward compatibility) and `speaker_role` (new standard)
- Segments include role information for direct frontend consumption

### 3. Celery Task Role Assignment Architecture Overhaul
**AssemblyAI Provider Fixes** (`assemblyai_stt.py`):
```python
# OLD (0-based mapping)
def _convert_speaker_id(self, speaker_id) -> int:
    return ord(speaker_id.upper()) - ord('A')  # "A"→0, "B"→1

# NEW (1-based mapping matching convention)
def _convert_speaker_id(self, speaker_id) -> int:
    return ord(speaker_id.upper()) - ord('A') + 1  # "A"→1, "B"→2
```

**New Role Persistence System** (`transcription_tasks.py`):
```python
def _save_speaker_role_assignments(db: Session, session_id: UUID, provider_metadata: dict):
    """Save speaker role assignments from provider metadata to SessionRole table"""
    role_assignments = provider_metadata.get('speaker_role_assignments', {})
    
    for speaker_id, role_str in role_assignments.items():
        speaker_role = SpeakerRole.COACH if role_str == 'coach' else SpeakerRole.CLIENT
        session_role = SessionRole(
            session_id=session_id,
            speaker_id=int(speaker_id),
            role=speaker_role
        )
        db.add(session_role)
```

### 4. Database Role Record Creation
**Subtitle Upload Flow**:
- Creates SessionRole records during VTT/SRT parsing
- Preserves user-selected role assignments in database
- Links to transcription session for API retrieval

**Audio Transcription Flow**:
- Extracts role assignments from SimpleRoleAssigner results in provider_metadata
- Creates SessionRole records during Celery task completion
- Enables frontend API access to automatic role assignments

### 5. Backend API Error Fixes
**Missing Variable Fix** (`coaching_sessions.py`):
```python
# Fixed missing transcription_session_summary variable
transcription_session_summary = get_transcription_session_summary(db, session.transcription_session_id)
```

**Import Error Fix** (`sessions.py`):
```python
# OLD (incorrect import)
from datetime import datetime

# NEW (complete import)
from datetime import datetime, timedelta
```

## 📊 Testing Results

### Before Fixes:
- ❌ Subtitle upload: All speakers became "client" regardless of user selection
- ❌ Audio transcription: Role assignments not accessible to frontend
- ❌ API errors: 500 errors due to missing variables and import issues
- ❌ Inconsistent speaker ID conventions causing confusion

### After Fixes:
- ✅ Subtitle upload: User-selected roles correctly preserved and displayed
- ✅ Audio transcription: Automatic role assignments properly stored and accessible
- ✅ API stability: All endpoints working correctly
- ✅ Unified string enum system: Clear, consistent role handling

## 🔒 Data Integrity & Backward Compatibility

### Backward Compatibility Maintained:
- Numeric `speaker_id` fields preserved in database schema
- Existing transcription sessions continue to work
- API responses include both old and new format data

### Database Schema Enhancements:
- SessionRole table properly utilized for role storage
- provider_metadata preserved for audit trail
- Dual-format segment data (numeric ID + string role)

## 🚀 Performance & User Experience Improvements

### User Experience:
- Consistent role display across all transcription methods
- Reliable role preservation during file uploads
- Clear visual feedback for role assignments

### System Performance:
- Reduced API errors and failed requests
- Improved error handling and recovery
- More reliable Celery task execution

### Developer Experience:
- Clear string enums eliminate confusion
- Consistent naming conventions across codebase
- Better error messages and debugging information

## 📝 Files Modified

### Frontend Changes:
- `apps/web/app/dashboard/sessions/[id]/page.tsx` - Role system migration
- `apps/web/lib/api.ts` - Enhanced logging for debugging

### Backend Changes:
- `packages/core-logic/src/coaching_assistant/api/coaching_sessions.py` - Speaker key normalization, role record creation
- `packages/core-logic/src/coaching_assistant/services/assemblyai_stt.py` - Speaker ID mapping fix
- `packages/core-logic/src/coaching_assistant/tasks/transcription_tasks.py` - Role assignment persistence
- `packages/core-logic/src/coaching_assistant/api/sessions.py` - Import error fix

## 🎯 Impact Assessment

### User Impact:
- **High Positive**: Role assignments now work correctly across all workflows
- **Eliminates Confusion**: Clear string-based role system
- **Preserves User Intent**: Subtitle upload selections properly maintained

### System Impact:
- **Improved Reliability**: Fewer API errors and failed transactions
- **Better Data Consistency**: Unified role storage and retrieval
- **Enhanced Maintainability**: Clear conventions and documentation

### Business Impact:
- **Reduced Support Load**: Fewer user reports about incorrect role assignments
- **Increased User Satisfaction**: Core functionality working as expected
- **Professional Quality**: System behavior matches user expectations

## 📋 Verification Checklist

- [x] Subtitle upload with custom role assignments preserves user choices
- [x] Audio transcription automatic role assignment works correctly  
- [x] Frontend displays consistent roles across all data sources
- [x] SessionRole records created for all transcription methods
- [x] API endpoints return complete role information
- [x] Error handling improved for missing data scenarios
- [x] String enum migration completed without breaking changes
- [x] Backward compatibility maintained for existing data

## 🔮 Future Improvements

### Short Term:
- Monitor role assignment accuracy in production
- Collect user feedback on role assignment interface
- Add role assignment confidence metrics to UI

### Long Term:
- Implement machine learning for improved automatic role detection
- Add support for multi-speaker scenarios (group coaching)
- Integrate role assignments with advanced analytics features

---

**Status**: ✅ **COMPLETED**  
**Date**: August 14, 2025  
**Impact**: Critical bug fixes ensuring core functionality reliability