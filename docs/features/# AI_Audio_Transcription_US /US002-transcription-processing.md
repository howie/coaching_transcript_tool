# User Story: US002 - Audio Transcription Processing

## Story
**As a** coach  
**I want to** have my audio files automatically transcribed  
**So that** I can review and analyze the coaching conversation in text format

## Priority: P0 (Critical)

## Acceptance Criteria

### AC1: Automatic Processing Trigger
- [ ] Transcription starts automatically after successful upload
- [ ] Job queued in Celery with unique task ID
- [ ] Session status updated to "processing"
- [ ] Estimated completion time calculated (4x audio duration)

### AC2: STT Provider Integration
- [ ] Integrate with Google Speech-to-Text v2 API
- [ ] Support for Traditional Chinese (zh-TW) as primary language
- [ ] Enable speaker diarization (2-4 speakers)
- [ ] Enable automatic punctuation
- [ ] Use "long" model for better accuracy

### AC3: Transcription Processing
- [ ] Retrieve audio file from GCS using URI
- [ ] Send to STT API for processing
- [ ] Handle long-running operations (up to 2 hours)
- [ ] Process response into structured segments
- [ ] Group consecutive words by speaker

### AC4: Error Handling
- [ ] Retry failed transcriptions (3 attempts with exponential backoff)
- [ ] Handle STT API errors gracefully
- [ ] Update session status to "failed" on permanent failure
- [ ] Log detailed error information for debugging
- [ ] Notify user of failure (future: email/notification)

### AC5: Result Storage
- [ ] Save transcript segments to database
- [ ] Store speaker ID (1, 2, 3...), content, start/end timestamps
- [ ] Calculate and store confidence scores
- [ ] Update session status to "completed"
- [ ] Record processing duration and cost
- [ ] Speaker IDs are numeric only (no role assignment)

## Definition of Done

### Development
- [ ] STT provider abstraction layer implemented
- [ ] Google STT provider implementation complete
- [ ] Celery worker configured and tested
- [ ] Database models for transcript segments created
- [ ] Unit tests with >80% coverage
- [ ] Integration tests for full processing flow

### Testing
- [ ] Test with various audio qualities
- [ ] Test with different languages (zh-TW, zh-CN, en)
- [ ] Test speaker separation accuracy (speaker 1, 2, 3...)
- [ ] Test error recovery mechanisms
- [ ] Load testing with concurrent transcriptions
- [ ] Verify cost tracking accuracy

### Performance
- [ ] P95 processing time ≤ 4x audio duration
- [ ] Support 10 concurrent transcriptions
- [ ] Memory usage stable during long transcriptions
- [ ] No memory leaks in worker processes

### Documentation
- [ ] Worker deployment guide created
- [ ] STT configuration documented
- [ ] Cost estimation formula documented
- [ ] Troubleshooting guide for common issues

## Technical Notes

### STT Provider Interface
```python
class STTProvider(ABC):
    @abstractmethod
    async def transcribe(
        audio_uri: str, 
        language: str,
        enable_diarization: bool
    ) -> List[TranscriptSegment]
    
    @abstractmethod
    def estimate_cost(duration_seconds: int) -> float
```

### Celery Task
```python
@celery.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def transcribe_audio(
    self,
    session_id: str,
    gcs_uri: str,
    language: str = "zh-TW"
)
```

### Database Schema
```sql
CREATE TABLE transcript_segments (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    speaker_id INTEGER,
    start_seconds DECIMAL(10,3),
    end_seconds DECIMAL(10,3),
    content TEXT,
    confidence DECIMAL(3,2)
);
```

### Configuration
```yaml
STT_PROVIDER: google
GOOGLE_STT_MODEL: long
MAX_SPEAKERS: 4
MIN_SPEAKERS: 2
ENABLE_PUNCTUATION: true
WORKER_CONCURRENCY: 4
TASK_TIME_LIMIT: 7200  # 2 hours
```

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| STT API quota exceeded | Processing delays | Implement rate limiting |
| High transcription costs | Budget overrun | Monitor usage, set alerts |
| Poor audio quality | Low accuracy | Set minimum quality thresholds |
| Worker crashes | Lost progress | Implement checkpointing |

## Dependencies
- US001: Audio Upload (must be complete)
- Google Cloud Speech-to-Text API access
- Celery + Redis infrastructure

## Related Stories
- US003: Speaker Role Detection
- US004: Transcript Export

## Specification by Example

### Example 1: Successful Transcription
**Given** a 30-minute Chinese coaching session is uploaded  
**And** the file is valid MP3 format  
**When** the transcription starts  
**Then** the session status should be "processing"  
**And** estimated completion time should be "~2 hours"  
**And** within 90 minutes, the status should be "completed"  
**And** the transcript should have 2 speakers identified  
**And** segments should have timestamps and confidence scores  

### Example 2: Speaker Separation
**Given** a conversation between two people  
**When** transcription completes  
**Then** segments should be labeled with Speaker 1, Speaker 2  
**And** Speaker 1 should have consistent segments like "你覺得這個問題如何？"  
**And** Speaker 2 should have consistent segments like "我覺得很困難"  
**And** speakers should not switch mid-sentence  
**And** each segment should have start/end timestamps  
**And** confidence scores should be >0.7 for clear speech  
**And** no role labels (Coach/Client) should be assigned yet  

### Example 3: Error Handling
**Given** a corrupted audio file is uploaded  
**When** STT processing begins  
**Then** the first attempt should fail  
**And** system should retry after 60 seconds  
**And** after 3 failed attempts, status should be "failed"  
**And** error message should be "Unable to process audio file"  
**And** user should see option to re-upload  

### Example 4: Language Processing
**Given** a Traditional Chinese audio file  
**And** language is set to "zh-TW"  
**When** transcription processes  
**Then** output should contain proper Chinese characters  
**And** punctuation should be automatically added  
**And** segments should preserve Traditional Chinese forms  
**And** numbers should be in Chinese format (e.g., "三十分鐘")  

### Example 5: Cost Calculation
**Given** a 45-minute audio file  
**When** transcription completes  
**Then** processing cost should be calculated as 45 * $0.016 = $0.72  
**And** cost should be logged for billing  
**And** duration should be stored as 2700 seconds  
**And** session metadata should include processing time  

### Example 6: Queue Management
**Given** 5 transcription jobs are queued simultaneously  
**When** worker processes them  
**Then** jobs should process concurrently (up to worker limit)  
**And** each job should have unique task ID  
**And** status should update independently  
**And** no job should be lost if worker restarts  

## Notes for QA
- Test with various accents and speaking speeds
- Verify speaker separation accuracy
- Test with background noise and music
- Check handling of silence periods
- Validate cost calculations against actual billing