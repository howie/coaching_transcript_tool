# User Story: US005 - Processing Status Tracking

## Story
**As a** coach  
**I want to** track the progress of my transcription  
**So that** I know when it's ready and can plan my time accordingly

## Priority: P1 (High)

## Acceptance Criteria

### AC1: Status States
- [ ] Display current status: pending, processing, completed, failed
- [ ] Show progress percentage (0-100%)
- [ ] Display estimated completion time
- [ ] Update status in real-time or near real-time
- [ ] Show processing duration after completion

### AC2: Progress Calculation
- [ ] Calculate based on audio duration (est. 4x processing time)
- [ ] Update progress every 10 seconds minimum
- [ ] Adjust estimate based on actual processing speed
- [ ] Show "almost done" when >90% complete
- [ ] Handle stalled processes (no progress for 5 minutes)

### AC3: User Interface
- [ ] Progress bar with percentage display
- [ ] Estimated time remaining (e.g., "~5 minutes left")
- [ ] Processing animation while active
- [ ] Success/failure indication with clear messaging
- [ ] Option to cancel processing (future)

### AC4: Status Persistence
- [ ] Store status updates in database
- [ ] Survive page refresh/reconnection
- [ ] Show last update timestamp
- [ ] Maintain history of status changes
- [ ] Clean up old status records (>30 days)

### AC5: Error Communication
- [ ] Clear error messages for failures
- [ ] Distinguish between retryable and permanent failures
- [ ] Provide actionable next steps
- [ ] Option to retry failed transcriptions
- [ ] Link to support/help documentation

## Definition of Done

### Development
- [ ] Status tracking service implemented
- [ ] API endpoint for status queries
- [ ] Database schema for status history
- [ ] Polling mechanism in frontend
- [ ] Unit tests with >80% coverage

### Testing
- [ ] Test status updates during processing
- [ ] Verify estimate accuracy
- [ ] Test failure scenarios and recovery
- [ ] Test with slow/stalled processes
- [ ] Verify persistence across sessions

### Performance
- [ ] Status query response < 100ms
- [ ] Polling doesn't overload server
- [ ] Efficient database queries
- [ ] Handle 100+ concurrent status checks

### Documentation
- [ ] Status state machine documented
- [ ] API endpoint documentation
- [ ] Progress calculation formula explained
- [ ] Troubleshooting guide for stuck processes

## Technical Notes

### API Endpoint
```
GET /api/v1/sessions/{id}/status

Response:
{
    "session_id": "uuid",
    "status": "processing",
    "progress": 45,
    "estimated_completion": "2025-01-09T10:30:00Z",
    "started_at": "2025-01-09T10:20:00Z",
    "message": "Processing audio...",
    "duration_processed": 1200,
    "duration_total": 3600
}
```

### Status State Machine
```
pending -> processing -> completed
                     \-> failed
                     
processing -> failed (on error)
failed -> processing (on retry)
```

### Progress Calculation
```python
def calculate_progress(duration_processed, total_duration):
    # Estimate 4x real-time processing
    expected_time = total_duration * 4
    elapsed_time = time.now() - start_time
    
    # Weight actual progress (70%) and time (30%)
    actual_progress = (duration_processed / total_duration) * 100
    time_progress = (elapsed_time / expected_time) * 100
    
    return (actual_progress * 0.7) + (time_progress * 0.3)
```

### Frontend Polling
```javascript
// Poll every 5 seconds while processing
const pollInterval = setInterval(async () => {
    const status = await fetchStatus(sessionId);
    updateUI(status);
    
    if (status.status !== 'processing') {
        clearInterval(pollInterval);
    }
}, 5000);
```

### Database Schema
```sql
CREATE TABLE processing_status (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    status VARCHAR(20),
    progress INTEGER,
    message TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_status_session ON processing_status(session_id);
CREATE INDEX idx_status_updated ON processing_status(updated_at);
```

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Polling overload | Server strain | Rate limiting, caching |
| Stalled processes | Poor UX | Timeout detection |
| Inaccurate estimates | User frustration | Conservative estimates |
| Lost status updates | Confusion | Status persistence |

## Dependencies
- US001: Audio Upload (session must exist)
- US002: Transcription Processing (generates status)
- Redis for status caching (optional)

## Related Stories
- US002: Transcription Processing
- Future: US006 - WebSocket Real-time Updates
- Future: US009 - Email Notifications

## Specification by Example

### Example 1: Progress Updates
**Given** a 60-minute audio file starts processing  
**And** estimated completion time is "4 hours"  
**When** I check status after 30 minutes  
**Then** status should be "processing"  
**And** progress should show approximately 12-15%  
**And** estimated time remaining should be "~3.5 hours"  
**And** message should be "Processing audio..."  

### Example 2: Real-time Polling
**Given** transcription is in progress  
**When** I stay on the status page  
**Then** progress should update every 5 seconds  
**And** I should see progress bar moving  
**And** percentage should increase over time  
**And** estimated completion time should adjust  
**And** page should not require manual refresh  

### Example 3: Successful Completion
**Given** transcription is at 95% progress  
**When** processing completes successfully  
**Then** status should change to "completed"  
**And** progress should show 100%  
**And** message should be "Transcription complete!"  
**And** "Download transcript" button should appear  
**And** processing duration should be displayed  

### Example 4: Error Handling
**Given** transcription fails after 20 minutes  
**When** I check the status  
**Then** status should be "failed"  
**And** progress should show where it stopped  
**And** error message should be "Processing failed. Please try again."  
**And** "Retry" button should be available  
**And** "Upload new file" option should be shown  

### Example 5: Session Persistence
**Given** transcription is in progress at 40%  
**When** I refresh the browser page  
**Then** status should still show "processing"  
**And** progress should display current percentage (40%)  
**And** estimated time should be recalculated  
**And** no data should be lost  

### Example 6: Multiple Sessions
**Given** I have 3 files processing simultaneously  
**When** I view my dashboard  
**Then** each session should show independent status  
**And** progress bars should update separately  
**And** completion times should be different  
**And** I can track each session individually  

## Notes for QA
- Test with various audio lengths
- Simulate network disconnections
- Test browser refresh during processing
- Verify status after server restart
- Check cleanup of old status records

## Future Enhancements
- WebSocket for real-time updates
- Email/SMS notifications on completion
- Batch status checking for multiple sessions
- Historical processing analytics
- Priority queue status display