# WP6-Cleanup-1: Speaker Role Vertical - Complete Implementation

**Status**: 🔥 **Critical Priority** (Not Started)
**Work Package**: WP6-Cleanup-1 - Speaker Role Vertical Complete Implementation
**Epic**: Clean Architecture Cleanup Phase

## Overview

Complete the speaker role management vertical slice that was partially implemented but left incomplete during WP5. This is critical for transcript functionality and represents a core user workflow.

## User Value Statement

**As a coach**, I want to **assign and manage speaker roles in my transcripts** so that **I can clearly identify who said what during coaching sessions and generate professional transcripts**.

## Business Impact

- **Revenue**: Enables professional transcript generation (core paid feature)
- **User Experience**: Critical for transcript usability and coaching session analysis
- **Technical Debt**: Removes major architectural violation blocking Clean Architecture completion

## Critical TODOs Being Resolved

### 🔥 Core Implementation Missing
- `src/coaching_assistant/core/services/speaker_role_management_use_case.py:90`
  ```python
  # TODO: Implement SpeakerRoleRepoPort and update this logic
  ```
- `src/coaching_assistant/core/services/speaker_role_management_use_case.py:173`
  ```python
  # TODO: Implement SegmentRoleRepoPort and update this logic
  ```
- `src/coaching_assistant/infrastructure/db/repositories/transcript_repository.py:55`
  ```python
  # TODO: Implement speaker role updates via SegmentRoleModel table
  ```

## Architecture Compliance Issues Fixed

### Current Violations
- **Missing Repository Implementations**: SpeakerRoleRepoPort, SegmentRoleRepoPort not implemented
- **Incomplete Use Cases**: Core business logic stubbed out with TODOs
- **Infrastructure Gap**: No proper ORM model for speaker role relationships

### Clean Architecture Solutions
- **Complete Repository Pattern**: Implement missing repository ports and implementations
- **Pure Business Logic**: Complete use case implementations with proper domain validation
- **Proper Domain ↔ ORM Conversion**: Full speaker role entity mapping

## Implementation Tasks

### 1. Complete Core Domain Models
- **File**: `src/coaching_assistant/core/models/speaker_role.py`
- **Requirements**:
  - `SpeakerRole` domain entity with business validation
  - `SegmentRole` domain entity for segment-speaker relationships
  - Proper value objects and domain logic

### 2. Implement Repository Ports
- **File**: `src/coaching_assistant/core/repositories/ports.py`
- **Requirements**:
  - Complete `SpeakerRoleRepoPort` protocol definition
  - Complete `SegmentRoleRepoPort` protocol definition
  - Proper CRUD and query operations

### 3. Complete Infrastructure Implementation
- **Files**:
  - `src/coaching_assistant/infrastructure/db/models/speaker_role_model.py`
  - `src/coaching_assistant/infrastructure/db/repositories/speaker_role_repository.py`
- **Requirements**:
  - SQLAlchemy ORM models with proper relationships
  - Complete repository implementations
  - Domain ↔ ORM conversion methods

### 4. Complete Use Case Implementation
- **File**: `src/coaching_assistant/core/services/speaker_role_management_use_case.py`
- **Requirements**:
  - Remove all TODO comments
  - Implement complete business logic
  - Proper error handling and validation

### 5. API Layer Integration
- **File**: `src/coaching_assistant/api/v1/coaching_sessions.py`
- **Requirements**:
  - Update speaker role assignment endpoints
  - Use completed use cases instead of direct DB access
  - Proper error responses

### 6. Factory Pattern Integration
- **File**: `src/coaching_assistant/infrastructure/factories.py`
- **Requirements**:
  - Add speaker role use case factories
  - Complete dependency injection

## E2E Demonstration Workflow

### Demo Script: "Coach Assigns Speaker Roles to Transcript"

**Pre-requisites**: Completed transcript with unassigned speakers

1. **Load Transcript** - GET `/api/v1/coaching-sessions/{id}/transcript`
   - Verify transcript segments exist with generic speaker labels
   - Expected: Segments with "Speaker 1", "Speaker 2" labels

2. **Assign Speaker Roles** - PATCH `/api/v1/coaching-sessions/{id}/speaker-roles`
   ```json
   {
     "speaker_assignments": {
       "Speaker 1": "COACH",
       "Speaker 2": "CLIENT"
     }
   }
   ```
   - Verify business logic validation (only COACH/CLIENT allowed)
   - Expected: 200 OK with updated assignments

3. **Verify Assignment** - GET `/api/v1/coaching-sessions/{id}/transcript`
   - Verify all segments now show proper role labels
   - Expected: Segments display "教練" and "客戶" based on i18n

4. **Update Individual Segments** - PATCH `/api/v1/coaching-sessions/{id}/segments/{segment_id}/role`
   ```json
   {
     "role": "CLIENT"
   }
   ```
   - Verify granular control over individual segments
   - Expected: Only targeted segment role updated

5. **Export Professional Transcript** - GET `/api/v1/coaching-sessions/{id}/export?format=txt`
   - Verify exported transcript uses proper role labels
   - Expected: Clean transcript with "教練:" and "客戶:" prefixes

## Success Metrics

### Functional Validation
- ✅ All speaker role TODOs removed from codebase
- ✅ Complete E2E workflow functional (load → assign → verify → export)
- ✅ API returns proper role labels in all transcript responses
- ✅ Individual segment role updates work correctly

### Architecture Validation
- ✅ Zero direct database access in use cases
- ✅ Repository pattern fully implemented
- ✅ Clean Architecture compliance: Core ← Infrastructure
- ✅ Factory pattern provides proper dependency injection

### Quality Validation
- ✅ Unit tests for all domain models and use cases
- ✅ Integration tests for repository implementations
- ✅ API tests for all speaker role endpoints
- ✅ E2E test for complete workflow automation

## Testing Strategy

### Unit Tests (Required)
```bash
# Test domain models
pytest tests/unit/core/models/test_speaker_role.py -v

# Test use cases (pure business logic)
pytest tests/unit/core/services/test_speaker_role_management_use_case.py -v
```

### Integration Tests (Required)
```bash
# Test repository implementations
pytest tests/integration/infrastructure/test_speaker_role_repository.py -v

# Test API endpoints
pytest tests/api/test_speaker_role_endpoints.py -v
```

### E2E Tests (Required)
```bash
# Complete workflow automation
pytest tests/e2e/test_speaker_role_assignment_workflow.py -v
```

### Manual Verification (Required)
- Frontend transcript viewer shows proper role labels
- Export functionality includes role assignments
- Error handling works for invalid role assignments

## Dependencies

### Blocked By
- None (can start immediately)

### Blocking
- **WP6-Cleanup-2**: Factory pattern completion depends on this
- **WP6-Cleanup-3**: Legacy model removal depends on this

## Definition of Done

- [ ] All TODO comments removed from speaker role related files
- [ ] Complete repository pattern implementation (ports + infrastructure)
- [ ] Use cases implement complete business logic without TODOs
- [ ] API endpoints use Clean Architecture pattern exclusively
- [ ] E2E demo workflow passes automated tests
- [ ] Frontend transcript viewer shows proper role labels
- [ ] Export functionality includes role assignments
- [ ] Zero architecture violations in speaker role vertical
- [ ] Code review completed and approved
- [ ] Documentation updated with new API behavior

## Risk Assessment

### Technical Risks
- **Medium**: Database schema changes may require migration
- **Low**: API contract changes (backward compatible with proper versioning)

### Business Risks
- **High Impact if Delayed**: Core transcript functionality remains incomplete
- **Revenue Impact**: Professional transcript generation not fully functional

## Delivery Timeline

- **Estimated Effort**: 2-3 days (1 developer)
- **Critical Path**: Complete domain → infrastructure → use cases → API integration
- **Deliverable**: Fully functional speaker role assignment with E2E demo

---

## Related Work Packages

- **WP6-Cleanup-2**: Factory Pattern Migration (depends on this)
- **WP6-Cleanup-3**: Legacy Model Removal (depends on this)
- **Future**: Advanced speaker identification features (builds on this)

This work package resolves the most critical architecture violation and enables complete transcript functionality - a core user value proposition.