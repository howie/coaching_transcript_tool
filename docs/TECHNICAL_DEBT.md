# Technical Debt

## Database Schema Naming Issues

### Current Confusing Column Names

The following column names are confusing and should be renamed in a future migration:

#### CoachingSession Table
- `coach_id` → Should be `user_id` (points to user.id)
- `audio_timeseq_id` → Should be `transcription_session_id` (points to session.id)
- `transcript_timeseq_id` → Should be removed or clarified (unclear purpose)

#### Relationships
```
User (用戶)
  ↓ 1:N (coach_id → user_id)
CoachingSession (會談記錄)
  ↓ 1:1 (audio_timeseq_id → transcription_session_id)
Session (轉錄會話)
  ↓ 1:N
ProcessingStatus (處理狀態)
TranscriptSegment (轉錄片段)
```

### Proposed Migration Plan

1. **Phase 1**: Add new columns with clear names
   - Add `user_id` alongside `coach_id`
   - Add `transcription_session_id` alongside `audio_timeseq_id`

2. **Phase 2**: Update all code to use new column names
   - Update models
   - Update API endpoints
   - Update frontend code

3. **Phase 3**: Remove old columns
   - Drop `coach_id`
   - Drop `audio_timeseq_id`
   - Remove `transcript_timeseq_id` if unused

### Impact Assessment
- **High Risk**: Database schema changes affect all layers
- **Medium Effort**: Requires updates to backend API and frontend
- **Low Business Impact**: No user-facing changes

### Recommendation
Defer this refactoring until after current MVP features are stable.
Focus on fixing the immediate `audio_timeseq_id` mapping bug first.

## Recently Resolved Technical Debt

### Fixed in August 2025 ✅
1. **Frontend-Backend Integration Gap** - RESOLVED
   - **Issue**: Frontend using mock/fake data instead of real API calls
   - **Solution**: Complete API client implementation with real endpoints (Commit: a58d430)
   - **Impact**: Eliminated development/production inconsistencies

2. **Progress Bar Precision Issues** - RESOLVED  
   - **Issue**: Floating point display issues causing visual inconsistencies
   - **Solution**: Implemented Math.round() for all progress calculations (Commit: 4d7b09a)
   - **Impact**: Consistent UI display across all progress indicators

3. **Database Transaction Inconsistency** - RESOLVED
   - **Issue**: Failed transcriptions leaving database in inconsistent state
   - **Solution**: Proper rollback mechanisms and atomic operations (Commit: a930412)
   - **Impact**: Improved data integrity and error recovery

4. **Real-time Polling Memory Leaks** - RESOLVED
   - **Issue**: Polling timers not properly cleaned up causing memory leaks
   - **Solution**: Proper useEffect cleanup and timer management (Commit: a58d430)
   - **Impact**: Better browser performance and resource management

## Current Priority Technical Debt

### High Priority (Address Next Quarter)
1. **Database Schema Naming Consistency**
   - Still needs addressing: confusing column names across tables
   - Impact: Developer confusion and maintenance overhead
   - Effort: Medium (requires careful migration planning)

2. **Audio Format Support Strategy**
   - Current state: M4A removed, MP4 added, but no clear format strategy
   - Recommendation: Establish comprehensive audio format support matrix
   - Consider: User demand vs. technical complexity trade-offs

### Medium Priority (Address When Convenient)
1. **Polling to WebSocket Migration**
   - Current: 5-second polling for status updates
   - Future: Real-time WebSocket updates for better performance
   - Benefits: Reduced server load, better real-time experience

2. **Error Handling Standardization**
   - Current: Mixed error handling patterns across components
   - Future: Standardized error boundary and messaging system
   - Benefits: Consistent user experience and easier debugging

### Low Priority (Monitor for Future)
1. **Component State Management**
   - Current: Mixed useState/useEffect patterns
   - Future: Consider centralized state management for complex workflows
   - Trigger: If state management becomes unwieldy

2. **API Response Caching**
   - Current: No caching strategy for API responses
   - Future: Implement smart caching for frequently accessed data
   - Benefits: Improved performance and reduced server load

## Technical Debt Prevention Measures

### Recently Implemented ✅
1. **Comprehensive Testing Coverage**
   - Added extensive test suites for critical components
   - Prevents regression and ensures quality

2. **Better Documentation Standards**
   - Enhanced commit messages with clear problem/solution descriptions
   - Improved code comments and architectural documentation

3. **Consistent Error Handling Patterns**
   - Standardized error handling across transcription pipeline
   - Better logging and debugging capabilities

### Recommended for Future
1. **Code Review Process Enhancement**
   - Focus on identifying potential technical debt during reviews
   - Establish criteria for when to address vs. defer technical debt

2. **Regular Technical Debt Assessment**
   - Quarterly review of accumulated technical debt
   - Prioritization based on business impact and development velocity

3. **Refactoring Budget Allocation**
   - Dedicate percentage of development time to technical debt reduction
   - Balance feature development with code quality maintenance