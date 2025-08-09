# User Story: US004 - Transcript Export

## Story
**As a** coach  
**I want to** export transcripts in various formats  
**So that** I can use them in different tools and share with clients

## Priority: P0 (Critical)

## Acceptance Criteria

### AC1: Export Formats
- [ ] Export as WebVTT (.vtt) with timestamps
- [ ] Export as SRT (.srt) subtitle format
- [ ] Export as JSON with full metadata
- [ ] Export as plain text (.txt) without timestamps
- [ ] Export as Markdown (.md) with speaker labels

### AC2: Speaker Role Labels
- [ ] Include speaker roles (Coach/Client) in exports
- [ ] Use detected or manually assigned roles
- [ ] Format: "[Coach]" or "[Client]" prefix
- [ ] Maintain consistent labeling across formats
- [ ] Handle unassigned speakers gracefully ("Speaker 1")

### AC3: Export Options
- [ ] Include/exclude timestamps option
- [ ] Include/exclude speaker labels option
- [ ] Choose date/time format (ISO 8601, local)
- [ ] Select segment grouping (by speaker, by time)
- [ ] Filter by speaker (export only Coach or Client)

### AC4: Download Experience
- [ ] Generate export file on-demand
- [ ] Proper filename: `session_{id}_{date}.{format}`
- [ ] Correct MIME types for each format
- [ ] Character encoding: UTF-8 with BOM for Chinese
- [ ] Immediate download (no waiting)

### AC5: Export Quality
- [ ] Preserve Chinese characters correctly
- [ ] Maintain proper line breaks and formatting
- [ ] Include session metadata (date, duration, speakers)
- [ ] Add export timestamp and version
- [ ] Ensure compatibility with common tools

## Definition of Done

### Development
- [ ] Export service implemented for all formats
- [ ] API endpoints created for each format
- [ ] Character encoding handled properly
- [ ] Unit tests with >80% coverage
- [ ] Integration tests for export flow

### Testing
- [ ] Test all export formats with Chinese content
- [ ] Verify in target applications (VLC, Word, etc.)
- [ ] Test large transcripts (2-hour sessions)
- [ ] Test special characters and emojis
- [ ] Cross-platform compatibility (Windows, Mac, Linux)

### Performance
- [ ] Export generation < 2 seconds for 1-hour transcript
- [ ] Streaming response for large files
- [ ] No memory spikes during export

### Documentation
- [ ] Export format specifications documented
- [ ] API endpoint documentation complete
- [ ] User guide for each format
- [ ] Compatibility matrix with tools

## Technical Notes

### API Endpoints
```
GET /api/v1/sessions/{id}/export?format=vtt
GET /api/v1/sessions/{id}/export?format=srt
GET /api/v1/sessions/{id}/export?format=json
GET /api/v1/sessions/{id}/export?format=txt
GET /api/v1/sessions/{id}/export?format=md
```

### VTT Format Example
```vtt
WEBVTT

1
00:00:00.000 --> 00:00:05.000
<v Coach>歡迎來到今天的教練會談

2
00:00:05.500 --> 00:00:10.000
<v Client>謝謝，我很期待這次討論
```

### SRT Format Example
```srt
1
00:00:00,000 --> 00:00:05,000
[Coach] 歡迎來到今天的教練會談

2
00:00:05,500 --> 00:00:10,000
[Client] 謝謝，我很期待這次討論
```

### Markdown Format Example
```markdown
# Coaching Session Transcript
Date: 2025-01-09
Duration: 60 minutes

## Transcript

**Coach** (00:00:00): 歡迎來到今天的教練會談

**Client** (00:00:05): 謝謝，我很期待這次討論
```

### Export Service Interface
```python
class TranscriptExportService:
    def to_vtt(segments, speaker_roles) -> str
    def to_srt(segments, speaker_roles) -> str
    def to_json(segments, speaker_roles) -> dict
    def to_text(segments, speaker_roles) -> str
    def to_markdown(segments, speaker_roles) -> str
```

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Character encoding issues | Corrupted exports | UTF-8 with BOM |
| Large file memory usage | Server crash | Stream response |
| Format compatibility | Can't use in tools | Test with target apps |

## Dependencies
- US002: Transcription Processing (segments must exist)
- US003: Speaker Role Detection (for role labels)

## Related Stories
- US005: Status Tracking (export availability)
- Future: US008 - Advanced Export Options

## Specification by Example

### Example 1: VTT Export with Chinese Characters
**Given** a completed transcript with Coach and Client roles  
**And** transcript contains Chinese text: "你覺得這個問題如何？"  
**When** user clicks "Export as VTT"  
**Then** file should download as "session_20250109_143000.vtt"  
**And** content should start with "WEBVTT"  
**And** Chinese characters should display correctly  
**And** timestamps should be in format "00:01:30.500 --> 00:01:35.000"  
**And** speaker tags should be "<v Coach>" and "<v Client>"  

### Example 2: SRT Export Compatibility
**Given** a 60-minute transcript  
**When** user exports as SRT  
**Then** file should be compatible with VLC media player  
**And** timestamps should use comma format "00:01:30,500"  
**And** speaker labels should be "[Coach]" and "[Client]"  
**And** file encoding should be UTF-8 with BOM  
**And** each subtitle should have sequential numbering  

### Example 3: JSON Export with Metadata
**Given** a completed transcript  
**When** user exports as JSON  
**Then** JSON should contain session metadata:  
```json
{
  "session_id": "uuid",
  "date": "2025-01-09T14:30:00Z",
  "duration": 3600,
  "speakers": {"1": "Coach", "2": "Client"},
  "segments": [...],
  "export_timestamp": "2025-01-09T15:30:00Z"
}
```
**And** segments should include confidence scores  

### Example 4: Markdown Format
**Given** a transcript with speaker roles assigned  
**When** user exports as Markdown  
**Then** file should have session header with date and duration  
**And** each segment should be formatted as "**Coach** (00:01:30): content"  
**And** file should be readable in any Markdown viewer  
**And** Chinese characters should render properly  

### Example 5: Export Options
**Given** user is on export page  
**When** they select "Exclude timestamps"  
**And** choose "Coach only" filter  
**Then** export should only contain Coach segments  
**And** no timestamps should be included  
**And** speaker labels should still show "[Coach]"  

### Example 6: Large File Handling
**Given** a 2-hour transcript with 500+ segments  
**When** user exports any format  
**Then** export should complete within 5 seconds  
**And** file should download immediately  
**And** no memory errors should occur  
**And** all segments should be included in export  

## Notes for QA
- Test with various media players (VLC, QuickTime)
- Import into subtitle editing tools
- Verify Chinese character display on Windows
- Test maximum file size limits
- Check timezone handling in timestamps

## Future Enhancements
- Export as Word document (.docx)
- Export as PDF with formatting
- Batch export multiple sessions
- Custom export templates
- API for third-party integrations