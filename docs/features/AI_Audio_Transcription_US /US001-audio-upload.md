# User Story: US001 - Audio File Upload

## Story
**As a** coach  
**I want to** upload my coaching session audio files  
**So that** I can get them transcribed into text format

## Priority: P0 (Critical)

## Acceptance Criteria

### AC1: Upload Interface
- [ ] User can select audio files from their device
- [ ] Supported formats: MP3, WAV, M4A, OGG
- [ ] File size validation: Maximum 1GB per file
- [ ] Duration validation: Maximum 120 minutes per file
- [ ] Clear error messages for invalid files

### AC2: Direct Upload to Storage
- [ ] Generate signed URL for Google Cloud Storage
- [ ] Signed URL expires after 30 minutes
- [ ] Client-side direct upload to GCS (bypass server)
- [ ] Upload progress indicator (percentage)
- [ ] Ability to cancel upload in progress

### AC3: File Validation
- [ ] Validate file format before upload
- [ ] Check file size client-side before upload
- [ ] Verify audio duration (server-side after upload)
- [ ] Reject corrupted or invalid audio files
- [ ] Display user-friendly error messages

### AC4: Storage Management
- [ ] Files stored in organized structure: `sessions/{user_id}/{session_id}/{filename}`
- [ ] Automatic deletion after configurable period (default 24 hours)
- [ ] Warning message about auto-deletion displayed to users
- [ ] Audit log entry created for upload

### AC5: Session Creation
- [ ] Create session record in database upon successful upload
- [ ] Generate unique session ID
- [ ] Store metadata: filename, size, duration, upload timestamp
- [ ] Associate session with authenticated user

## Definition of Done

### Development
- [ ] Code implementation complete
- [ ] Unit tests written with >80% coverage
- [ ] Integration tests for upload flow
- [ ] API documentation updated
- [ ] Code reviewed and approved

### Testing
- [ ] Manual testing completed on staging
- [ ] Test with various file formats and sizes
- [ ] Test error scenarios (network failure, invalid files)
- [ ] Performance testing for large files (1GB)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)

### Security
- [ ] File type validation prevents malicious uploads
- [ ] Signed URLs properly scoped and time-limited
- [ ] User can only access their own sessions
- [ ] No sensitive data logged

### Documentation
- [ ] API endpoints documented in OpenAPI/Swagger
- [ ] User guide updated with upload instructions
- [ ] Error codes and messages documented
- [ ] Architecture decision record (ADR) created if needed

## Technical Notes

### API Endpoints
```
POST /api/v1/sessions
  Creates new session and returns upload URL

POST /api/v1/sessions/{id}/complete
  Marks upload as complete and triggers processing
```

### Dependencies
- Google Cloud Storage SDK
- FastAPI for API endpoints
- SQLAlchemy for database operations

### Configuration
```yaml
STORAGE_BUCKET: coaching-audio-{env}
MAX_FILE_SIZE_MB: 1024
MAX_DURATION_MINUTES: 120
RETENTION_DAYS: 1
SIGNED_URL_EXPIRY_MINUTES: 30
```

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large file upload fails | Poor UX | Implement chunked upload |
| GCS quota exceeded | Service unavailable | Monitor usage, set alerts |
| Malicious file upload | Security breach | Strict file validation |

## Related Stories
- US002: Audio Transcription Processing
- US005: Upload Status Tracking

## Specification by Example

### Example 1: Successful Upload
**Given** I am a logged-in coach  
**And** I have a 45-minute MP3 file (250 MB)  
**When** I select the file and click upload  
**Then** I should see a progress bar starting from 0%  
**And** the file should upload directly to GCS  
**And** a session record should be created with status "pending"  
**And** I should see "Upload complete" when finished  

### Example 2: File Too Large
**Given** I am a logged-in coach  
**And** I have a 1.5 GB MP3 file  
**When** I try to select the file  
**Then** I should see error: "File size exceeds 1 GB limit"  
**And** the upload should not start  
**And** no session record should be created  

### Example 3: Invalid Format
**Given** I am a logged-in coach  
**And** I have a PDF file named "session.pdf"  
**When** I try to upload it  
**Then** I should see error: "Invalid file format. Supported: MP3, WAV, M4A, OGG"  
**And** the upload should be prevented  

### Example 4: Duration Too Long
**Given** I am a logged-in coach  
**And** I have a 3-hour MP3 file (500 MB)  
**When** I upload the file  
**Then** the upload should complete  
**But** validation should fail with: "Audio duration exceeds 120 minutes limit"  
**And** the file should be deleted from storage  
**And** session status should be "failed"  

### Example 5: Auto-Deletion Warning
**Given** I am uploading an audio file  
**When** the upload interface loads  
**Then** I should see warning: "Files will be automatically deleted after 24 hours"  
**And** the warning should be in orange/yellow color  
**And** there should be a link to "Learn more about data retention"  

### Example 6: Network Interruption
**Given** I am uploading a 500 MB file  
**And** the upload is at 50% progress  
**When** the network connection is lost  
**Then** I should see error: "Upload interrupted. Please check your connection"  
**And** there should be a "Retry" button  
**When** I click "Retry" after reconnecting  
**Then** the upload should resume from where it stopped  

## Notes for QA
- Test with edge cases: 0-byte files, exactly 1GB files, 120-minute files
- Verify cleanup job deletes files after retention period
- Check audit logs capture all upload events
- Test concurrent uploads from same user