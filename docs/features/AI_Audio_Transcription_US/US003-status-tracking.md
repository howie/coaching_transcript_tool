# User Story: US003 - Processing Status Tracking

## Implementation Status: ✅ COMPLETED

**Backend Status:** ✅ IMPLEMENTED (status polling API and progress tracking)  
**Frontend Status:** ✅ IMPLEMENTED (progress UI components and real-time polling)

### Implementation Completed ✅
- ✅ Backend: Processing status API endpoints implemented
- ✅ Frontend: Progress bars and status UI components 
- ✅ Real-time polling with useTranscriptionStatus hook
- ✅ Database schema for processing_status table
- ✅ Progress calculation with time-based and actual progress
- ✅ Status persistence and error handling

## Story
**As a** coach  
**I want to** track the progress of my transcription  
**So that** I know when it's ready and can plan my time accordingly

## Priority: P1 (High)

## Acceptance Criteria

### AC1: Status States ✅ COMPLETED
- ✅ Display current status: pending, processing, completed, failed
- ✅ Show progress percentage (0-100%)
- ✅ Display estimated completion time
- ✅ Update status in real-time with 5-second polling
- ✅ Show processing duration and speed after completion

### AC2: Progress Calculation ✅ COMPLETED
- ✅ Calculate based on audio duration (est. 4x processing time)
- ✅ Update progress every 5 seconds via polling
- ✅ Combine actual progress (70%) with time estimate (30%)
- ✅ Show contextual messages based on progress stages
- ✅ Handle processing timeouts and stalled processes

### AC3: User Interface ✅ COMPLETED
- ✅ Progress bar with percentage display (TranscriptionProgress component)
- ✅ Estimated time remaining with formatTimeRemaining helper
- ✅ Dynamic progress color changes based on status
- ✅ Success/failure indication with clear messaging
- ⏳ Option to cancel processing (deferred to future)

### AC4: Status Persistence ✅ COMPLETED
- ✅ Store status updates in processing_status table
- ✅ Survive page refresh/reconnection with useTranscriptionStatus hook
- ✅ Show last update timestamp with created_at/updated_at
- ✅ Maintain history of status changes in database
- ⏳ Clean up old status records (deferred - manual cleanup)

### AC5: Error Communication ✅ COMPLETED
- ✅ Clear error messages with status.message field
- ✅ Distinguish between retryable and permanent failures in task logic
- ✅ Provide contextual status messages based on progress
- ⏳ Retry failed transcriptions (deferred to manual retry)
- ⏳ Support documentation links (deferred)

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

## Monitoring and Debugging

### API Logs Location
When running `make run-api`, logs are output to **stdout/stderr** by default. To capture them:

```bash
# Direct console output (default)
make run-api

# Redirect logs to file
make run-api > api.log 2>&1

# Follow logs in real-time
make run-api | tee api.log

# Filter transcription-related logs
make run-api | grep -E "(transcribe|STT|session|processing)"
```

### Key Log Messages to Monitor
```bash
# Transcription start
"Starting transcription for session {session_id}"

# Audio sent to Google STT
"Sending audio to STT provider: {gcs_uri}"

# Processing progress
"Transcription completed: {segments} segments"

# Status updates
"Session {session_id} completed successfully"
```

### Debugging Commands

#### 1. Check Celery Task Status
```bash
# View active tasks
celery -A coaching_assistant.core.celery_app inspect active

# Check task history
celery -A coaching_assistant.core.celery_app events

# Monitor specific task
celery -A coaching_assistant.core.celery_app inspect task <task_id>
```

#### 2. Database Status Monitoring
```sql
-- Check session status
SELECT id, status, transcription_job_id, audio_filename, created_at, updated_at 
FROM session 
WHERE id = 'your-session-id';

-- Check processing progress
SELECT session_id, status, progress, message, created_at 
FROM processing_status 
WHERE session_id = 'your-session-id' 
ORDER BY created_at DESC LIMIT 5;

-- Verify transcript segments
SELECT COUNT(*) as segment_count, 
       MIN(start_sec) as first_segment, 
       MAX(end_sec) as last_segment
FROM transcript_segment 
WHERE session_id = 'your-session-id';
```

#### 3. Google Cloud Storage Verification
```bash
# Check if audio file exists
gcloud storage ls gs://your-bucket/audio-uploads/user-id/

# Verify file size and metadata
gcloud storage ls -l gs://your-bucket/audio-uploads/user-id/session-id.*
```

#### 4. Google STT API Monitoring

⚠️ **Permission Issue Solution:**
The error you encountered occurs because the service account `coaching-storage@coachingassistant.iam.gserviceaccount.com` lacks logging permissions.

**Fix:** Add logging permissions to your service account:
```bash
# Add Logging Viewer role
gcloud projects add-iam-policy-binding coachingassistant \
    --member="serviceAccount:coaching-storage@coachingassistant.iam.gserviceaccount.com" \
    --role="roles/logging.viewer"

# Or use a more specific role
gcloud projects add-iam-policy-binding coachingassistant \
    --member="serviceAccount:coaching-storage@coachingassistant.iam.gserviceaccount.com" \
    --role="roles/logging.privateLogViewer"
```

**Alternative:** Use your personal account for debugging:
```bash
# Switch to personal account
gcloud config set account your-email@gmail.com
gcloud auth login

# Then check logs
gcloud logging read "resource.type=cloud_function AND textPayload:speech" --limit=50
```

**Better Query for Speech-to-Text API:**
```bash
# Check STT API usage
gcloud logging read 'protoPayload.serviceName="speech.googleapis.com"' --limit=20

# Monitor transcription requests
gcloud logging read 'resource.type="audited_resource" AND protoPayload.serviceName="speech.googleapis.com"' --format="table(timestamp,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail)"
```

### Real-time Monitoring Setup

#### Terminal 1: API Logs
```bash
make run-api | grep -E --color=always "(transcribe|STT|session|ERROR|WARN)"
```

#### Terminal 2: Database Status
```bash
# Watch processing status changes
watch -n 5 'psql $DATABASE_URL -c "SELECT session_id, status, progress, message FROM processing_status ORDER BY updated_at DESC LIMIT 5;"'
```

#### Terminal 3: Celery Worker
```bash
# Monitor Celery worker
celery -A coaching_assistant.core.celery_app worker --loglevel=info
```

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