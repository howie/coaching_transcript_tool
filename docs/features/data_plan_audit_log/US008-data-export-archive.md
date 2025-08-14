# US008: Data Export & Archive

## 📋 User Story

**As a** platform user and administrator  
**I want** comprehensive data export and archival capabilities  
**So that** I can comply with data portability requirements, create backups, and migrate data as needed

## 💼 Business Value

### Current Problem
- Limited data export capabilities for users and administrators
- No structured data archival system for long-term storage
- Difficult to comply with GDPR Article 20 (Right to Data Portability)
- Manual processes for data migration and backup operations

### Business Impact
- **Compliance Risk**: GDPR Article 20 requires machine-readable data portability
- **User Satisfaction**: Users cannot easily export their data for personal use
- **Operational Overhead**: Manual data extraction and migration processes
- **Business Continuity**: Limited backup and disaster recovery capabilities

### Value Delivered
- **GDPR Compliance**: Full compliance with data portability requirements
- **User Empowerment**: Self-service data export for users
- **Operational Efficiency**: Automated archival and backup processes
- **Business Flexibility**: Easy data migration and system integration capabilities

## 🎯 Acceptance Criteria

### User Data Export
1. **Personal Data Export**
   - [ ] Complete user profile and settings export
   - [ ] All client data and coaching session history
   - [ ] Usage analytics and billing information
   - [ ] Structured formats: JSON, CSV, PDF options

2. **Transcription Data Export**
   - [ ] Individual session transcriptions with metadata
   - [ ] Bulk export of multiple sessions
   - [ ] Multiple formats: VTT, SRT, JSON, TXT, XLSX
   - [ ] Include speaker role assignments and timestamps

3. **Self-Service Export Interface**
   - [ ] User-friendly export wizard with preview
   - [ ] Progress tracking for large exports
   - [ ] Download links with secure access tokens
   - [ ] Export history and re-download capabilities

### Administrative Data Export
4. **System-Wide Data Export**
   - [ ] User data export for specific users or date ranges
   - [ ] Usage analytics and business intelligence data
   - [ ] Audit logs and compliance reports
   - [ ] System configuration and metadata

5. **Bulk Export Operations**
   - [ ] Background processing for large datasets
   - [ ] Batch export with progress notifications
   - [ ] Compressed archive formats (ZIP, TAR.GZ)
   - [ ] Incremental exports for ongoing backups

### Data Archival System
6. **Automated Archival**
   - [ ] Cold storage integration for old data
   - [ ] Configurable archival policies by data age
   - [ ] Compressed storage with integrity verification
   - [ ] Retrieval mechanisms for archived data

## 🏗️ Technical Implementation

### Data Export Models
```python
# packages/core-logic/src/coaching_assistant/models/data_export.py

import enum
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import BaseModel

class ExportType(enum.Enum):
    """Types of data exports"""
    USER_DATA = "user_data"              # Complete user data export
    TRANSCRIPTIONS = "transcriptions"    # Transcription sessions only
    ANALYTICS = "analytics"              # Usage analytics data
    AUDIT_LOGS = "audit_logs"           # Audit trail data
    SYSTEM_BACKUP = "system_backup"     # System-wide backup
    COMPLIANCE_REPORT = "compliance_report"  # GDPR compliance report

class ExportFormat(enum.Enum):
    """Export file formats"""
    JSON = "json"        # Structured JSON format
    CSV = "csv"          # Comma-separated values
    XLSX = "xlsx"        # Excel spreadsheet
    PDF = "pdf"          # PDF document
    ZIP = "zip"          # Compressed archive
    TAR_GZ = "tar.gz"    # Compressed tar archive

class ExportStatus(enum.Enum):
    """Export processing status"""
    PENDING = "pending"      # Export request queued
    PROCESSING = "processing"  # Export being generated
    COMPLETED = "completed"   # Export ready for download
    FAILED = "failed"        # Export failed
    EXPIRED = "expired"      # Download link expired

class DataExport(BaseModel):
    """Data export request and tracking"""
    
    # Export configuration
    export_type = Column(Enum(ExportType), nullable=False)
    export_format = Column(Enum(ExportFormat), nullable=False)
    
    # Requestor information
    requested_by = Column(UUID(as_uuid=True), nullable=False, index=True)
    is_admin_export = Column(Boolean, default=False)
    
    # Export scope and filters
    export_filters = Column(JSONB, default={})  # Date ranges, user IDs, etc.
    include_metadata = Column(Boolean, default=True)
    include_personal_data = Column(Boolean, default=True)
    
    # Processing status
    status = Column(Enum(ExportStatus), default=ExportStatus.PENDING, nullable=False)
    
    # Processing metadata
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Export results
    file_path = Column(String(500), nullable=True)  # Path to generated file
    file_size_bytes = Column(Integer, default=0)
    record_count = Column(Integer, default=0)
    
    # Access control
    download_token = Column(String(64), nullable=True)  # Secure download token
    download_expires_at = Column(DateTime(timezone=True), nullable=True)
    download_count = Column(Integer, default=0)
    max_downloads = Column(Integer, default=5)
    
    # Cleanup
    auto_delete_after_days = Column(Integer, default=7)
    
    def __repr__(self):
        return f"<DataExport(type={self.export_type.value}, status={self.status.value}, user={self.requested_by})>"
    
    @property
    def is_downloadable(self) -> bool:
        """Check if export is ready for download"""
        return (
            self.status == ExportStatus.COMPLETED and
            self.download_expires_at and
            self.download_expires_at > datetime.utcnow() and
            self.download_count < self.max_downloads
        )
    
    @property
    def processing_duration(self) -> timedelta:
        """Calculate export processing duration"""
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return datetime.utcnow() - self.started_at
        return timedelta(0)
    
    def generate_download_token(self) -> str:
        """Generate secure download token"""
        import secrets
        self.download_token = secrets.token_urlsafe(32)
        self.download_expires_at = datetime.utcnow() + timedelta(hours=24)
        return self.download_token
    
    def increment_download_count(self):
        """Increment download counter"""
        self.download_count += 1
        if self.download_count >= self.max_downloads:
            self.download_expires_at = datetime.utcnow()  # Expire immediately

class DataArchive(BaseModel):
    """Archived data storage tracking"""
    
    # Archive identification
    archive_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Archive content
    data_category = Column(String(50), nullable=False)  # "users", "sessions", "audit_logs"
    record_count = Column(Integer, nullable=False)
    date_range_start = Column(DateTime(timezone=True), nullable=True)
    date_range_end = Column(DateTime(timezone=True), nullable=True)
    
    # Storage information
    storage_path = Column(String(500), nullable=False)  # Cold storage path
    compressed_size_bytes = Column(Integer, nullable=False)
    original_size_bytes = Column(Integer, nullable=False)
    compression_ratio = Column(Float, nullable=False)
    
    # Integrity verification
    checksum_md5 = Column(String(32), nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    
    # Archive metadata
    archived_by = Column(UUID(as_uuid=True), nullable=False)
    retention_policy = Column(String(100), nullable=True)
    
    # Access tracking
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, default=0)
    
    def verify_integrity(self, file_path: str) -> bool:
        """Verify archive file integrity"""
        import hashlib
        
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)
        
        return (
            md5_hash.hexdigest() == self.checksum_md5 and
            sha256_hash.hexdigest() == self.checksum_sha256
        )
```

### Data Export Service
```python
# packages/core-logic/src/coaching_assistant/services/data_export_service.py

import os
import json
import csv
import zipfile
import tempfile
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataExportService:
    """Service for generating data exports"""
    
    def __init__(self, db: Session):
        self.db = db
        self.export_base_path = os.getenv('EXPORT_BASE_PATH', '/tmp/exports')
    
    def create_export_request(
        self,
        export_type: ExportType,
        export_format: ExportFormat,
        requested_by: UUID,
        export_filters: Optional[Dict] = None,
        is_admin_export: bool = False
    ) -> DataExport:
        """Create new data export request"""
        
        export_request = DataExport(
            export_type=export_type,
            export_format=export_format,
            requested_by=requested_by,
            is_admin_export=is_admin_export,
            export_filters=export_filters or {},
            status=ExportStatus.PENDING
        )
        
        self.db.add(export_request)
        self.db.commit()
        
        # Queue export processing
        from ..tasks.export_tasks import process_data_export
        process_data_export.delay(str(export_request.id))
        
        return export_request
    
    def process_export(self, export_id: UUID) -> DataExport:
        """Process data export request"""
        
        export_request = self.db.query(DataExport).filter(
            DataExport.id == export_id
        ).first()
        
        if not export_request:
            raise ValueError(f"Export request {export_id} not found")
        
        try:
            # Update status to processing
            export_request.status = ExportStatus.PROCESSING
            export_request.started_at = datetime.utcnow()
            self.db.commit()
            
            # Process based on export type
            if export_request.export_type == ExportType.USER_DATA:
                result = self._export_user_data(export_request)
            elif export_request.export_type == ExportType.TRANSCRIPTIONS:
                result = self._export_transcriptions(export_request)
            elif export_request.export_type == ExportType.ANALYTICS:
                result = self._export_analytics(export_request)
            elif export_request.export_type == ExportType.AUDIT_LOGS:
                result = self._export_audit_logs(export_request)
            else:
                raise ValueError(f"Unsupported export type: {export_request.export_type}")
            
            # Update export with results
            export_request.status = ExportStatus.COMPLETED
            export_request.completed_at = datetime.utcnow()
            export_request.file_path = result['file_path']
            export_request.file_size_bytes = result['file_size']
            export_request.record_count = result['record_count']
            export_request.generate_download_token()
            
            self.db.commit()
            
            logger.info(f"Export completed: {export_id} - {result['record_count']} records")
            
            return export_request
            
        except Exception as e:
            # Update status to failed
            export_request.status = ExportStatus.FAILED
            export_request.completed_at = datetime.utcnow()
            export_request.error_message = str(e)
            self.db.commit()
            
            logger.error(f"Export failed: {export_id} - {e}")
            raise
    
    def _export_user_data(self, export_request: DataExport) -> Dict:
        """Export complete user data"""
        
        user_id = export_request.requested_by
        filters = export_request.export_filters
        
        # Get user data
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Collect all user data
        export_data = {
            "export_info": {
                "export_type": export_request.export_type.value,
                "generated_at": datetime.utcnow().isoformat(),
                "user_id": str(user_id),
                "filters": filters
            },
            "user_profile": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "plan": user.plan.value,
                "usage_minutes": user.usage_minutes,
                "created_at": user.created_at.isoformat(),
                "preferences": user.get_preferences()
            },
            "clients": [],
            "sessions": [],
            "usage_history": []
        }
        
        # Get clients (including soft-deleted if admin export)
        clients_query = self.db.query(Client).filter(Client.user_id == user_id)
        if not export_request.is_admin_export:
            clients_query = clients_query.filter(Client.is_active == True)
        
        clients = clients_query.all()
        export_data["clients"] = [
            {
                "id": str(client.id),
                "name": client.name if not client.is_anonymized else "已匿名客戶",
                "email": client.email if not client.is_anonymized else None,
                "status": client.status,
                "created_at": client.created_at.isoformat(),
                "is_anonymized": client.is_anonymized,
                "is_active": client.is_active
            }
            for client in clients
        ]
        
        # Get sessions
        sessions = self.db.query(Session).filter(Session.user_id == user_id).all()
        export_data["sessions"] = [
            {
                "id": str(session.id),
                "title": session.title,
                "status": session.status.value,
                "language": session.language,
                "duration_minutes": session.duration_minutes,
                "stt_provider": session.stt_provider,
                "created_at": session.created_at.isoformat(),
                "completed_at": session.updated_at.isoformat() if session.is_processing_complete else None
            }
            for session in sessions
        ]
        
        # Get usage history
        usage_logs = self.db.query(UsageLog).filter(UsageLog.user_id == user_id).all()
        export_data["usage_history"] = [
            {
                "session_id": str(log.session_id),
                "duration_minutes": log.duration_minutes,
                "cost_usd": float(log.cost_usd) if log.cost_usd else 0,
                "stt_provider": log.stt_provider,
                "transcription_type": log.transcription_type.value,
                "created_at": log.created_at.isoformat()
            }
            for log in usage_logs
        ]
        
        # Generate file based on format
        if export_request.export_format == ExportFormat.JSON:
            file_path = self._write_json_export(export_data, f"user_data_{user_id}")
        elif export_request.export_format == ExportFormat.CSV:
            file_path = self._write_csv_export(export_data, f"user_data_{user_id}")
        elif export_request.export_format == ExportFormat.ZIP:
            file_path = self._write_zip_export(export_data, f"user_data_{user_id}")
        else:
            raise ValueError(f"Unsupported export format: {export_request.export_format}")
        
        return {
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'record_count': len(sessions) + len(clients) + len(usage_logs)
        }
    
    def _export_transcriptions(self, export_request: DataExport) -> Dict:
        """Export transcription data"""
        
        user_id = export_request.requested_by
        filters = export_request.export_filters
        
        # Build query with filters
        query = self.db.query(Session).filter(Session.user_id == user_id)
        
        if 'session_ids' in filters:
            query = query.filter(Session.id.in_(filters['session_ids']))
        
        if 'date_from' in filters:
            query = query.filter(Session.created_at >= datetime.fromisoformat(filters['date_from']))
        
        if 'date_to' in filters:
            query = query.filter(Session.created_at <= datetime.fromisoformat(filters['date_to']))
        
        sessions = query.filter(Session.status == SessionStatus.COMPLETED).all()
        
        export_data = {
            "export_info": {
                "export_type": "transcriptions",
                "generated_at": datetime.utcnow().isoformat(),
                "session_count": len(sessions),
                "filters": filters
            },
            "transcriptions": []
        }
        
        for session in sessions:
            # Get transcript segments
            segments = self.db.query(TranscriptSegment).filter(
                TranscriptSegment.session_id == session.id
            ).order_by(TranscriptSegment.start_seconds).all()
            
            # Get speaker roles
            roles = {role.speaker_id: role.role.value for role in session.roles}
            
            session_data = {
                "session_id": str(session.id),
                "title": session.title,
                "language": session.language,
                "duration_minutes": session.duration_minutes,
                "created_at": session.created_at.isoformat(),
                "stt_provider": session.stt_provider,
                "segments": [
                    {
                        "start_seconds": segment.start_seconds,
                        "end_seconds": segment.end_seconds,
                        "speaker_id": segment.speaker_id,
                        "speaker_role": roles.get(segment.speaker_id, f"Speaker {segment.speaker_id}"),
                        "content": segment.content,
                        "confidence": segment.confidence
                    }
                    for segment in segments
                ]
            }
            
            export_data["transcriptions"].append(session_data)
        
        # Generate file
        if export_request.export_format == ExportFormat.JSON:
            file_path = self._write_json_export(export_data, f"transcriptions_{user_id}")
        elif export_request.export_format == ExportFormat.XLSX:
            file_path = self._write_transcriptions_xlsx(export_data, f"transcriptions_{user_id}")
        else:
            file_path = self._write_json_export(export_data, f"transcriptions_{user_id}")
        
        return {
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'record_count': len(sessions)
        }
    
    def _write_json_export(self, data: Dict, filename: str) -> str:
        """Write data as JSON file"""
        
        os.makedirs(self.export_base_path, exist_ok=True)
        file_path = os.path.join(self.export_base_path, f"{filename}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    def _write_zip_export(self, data: Dict, filename: str) -> str:
        """Write data as ZIP archive with multiple files"""
        
        os.makedirs(self.export_base_path, exist_ok=True)
        zip_path = os.path.join(self.export_base_path, f"{filename}.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add main data file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_f:
                json.dump(data, temp_f, indent=2, ensure_ascii=False)
                temp_f.flush()
                zipf.write(temp_f.name, 'user_data.json')
                os.unlink(temp_f.name)
            
            # Add separate files for different data types
            if 'sessions' in data:
                sessions_data = {"sessions": data['sessions']}
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_f:
                    json.dump(sessions_data, temp_f, indent=2, ensure_ascii=False)
                    temp_f.flush()
                    zipf.write(temp_f.name, 'sessions.json')
                    os.unlink(temp_f.name)
        
        return zip_path
    
    def get_download_url(self, export_id: UUID, download_token: str) -> Optional[str]:
        """Get secure download URL for export"""
        
        export_request = self.db.query(DataExport).filter(
            and_(
                DataExport.id == export_id,
                DataExport.download_token == download_token
            )
        ).first()
        
        if not export_request or not export_request.is_downloadable:
            return None
        
        # Generate time-limited download URL
        from ..utils.url_signer import generate_signed_url
        return generate_signed_url(
            path=f"/api/v1/exports/{export_id}/download",
            params={"token": download_token},
            expires_in=3600  # 1 hour
        )
```

### Export API Endpoints
```python
# packages/core-logic/src/coaching_assistant/api/exports.py

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from ..services.data_export_service import DataExportService
from ..models.data_export import ExportType, ExportFormat

router = APIRouter()

@router.post("/user-data")
async def request_user_data_export(
    export_format: ExportFormat = ExportFormat.JSON,
    include_transcriptions: bool = True,
    include_analytics: bool = True,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Request complete user data export (GDPR Article 20)"""
    
    export_service = DataExportService(db)
    
    export_filters = {
        "include_transcriptions": include_transcriptions,
        "include_analytics": include_analytics
    }
    
    export_request = export_service.create_export_request(
        export_type=ExportType.USER_DATA,
        export_format=export_format,
        requested_by=current_user.id,
        export_filters=export_filters
    )
    
    return {
        "message": "Data export requested successfully",
        "export_id": str(export_request.id),
        "estimated_processing_time_minutes": 5,
        "status": export_request.status.value
    }

@router.post("/transcriptions")
async def request_transcriptions_export(
    request: TranscriptionExportRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Request transcriptions export"""
    
    # Validate session ownership
    if request.session_ids:
        user_sessions = db.query(Session.id).filter(
            and_(
                Session.id.in_(request.session_ids),
                Session.user_id == current_user.id
            )
        ).all()
        
        if len(user_sessions) != len(request.session_ids):
            raise HTTPException(status_code=403, detail="Access denied to some sessions")
    
    export_service = DataExportService(db)
    
    export_filters = {
        "session_ids": request.session_ids,
        "date_from": request.date_from.isoformat() if request.date_from else None,
        "date_to": request.date_to.isoformat() if request.date_to else None
    }
    
    export_request = export_service.create_export_request(
        export_type=ExportType.TRANSCRIPTIONS,
        export_format=request.export_format,
        requested_by=current_user.id,
        export_filters=export_filters
    )
    
    return {
        "message": "Transcription export requested successfully",
        "export_id": str(export_request.id),
        "status": export_request.status.value
    }

@router.get("/status/{export_id}")
async def get_export_status(
    export_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get export processing status"""
    
    export_request = db.query(DataExport).filter(
        and_(
            DataExport.id == export_id,
            DataExport.requested_by == current_user.id
        )
    ).first()
    
    if not export_request:
        raise HTTPException(status_code=404, detail="Export not found")
    
    response = {
        "export_id": str(export_request.id),
        "status": export_request.status.value,
        "export_type": export_request.export_type.value,
        "export_format": export_request.export_format.value,
        "created_at": export_request.created_at.isoformat(),
        "processing_duration": str(export_request.processing_duration),
    }
    
    if export_request.status == ExportStatus.COMPLETED:
        response.update({
            "record_count": export_request.record_count,
            "file_size_bytes": export_request.file_size_bytes,
            "download_expires_at": export_request.download_expires_at.isoformat(),
            "downloads_remaining": export_request.max_downloads - export_request.download_count,
            "download_available": export_request.is_downloadable
        })
    elif export_request.status == ExportStatus.FAILED:
        response["error_message"] = export_request.error_message
    
    return response

@router.get("/{export_id}/download")
async def download_export(
    export_id: UUID,
    token: str = Query(..., description="Download token"),
    db: Session = Depends(get_db)
):
    """Download export file"""
    
    export_request = db.query(DataExport).filter(
        and_(
            DataExport.id == export_id,
            DataExport.download_token == token
        )
    ).first()
    
    if not export_request:
        raise HTTPException(status_code=404, detail="Export not found or invalid token")
    
    if not export_request.is_downloadable:
        raise HTTPException(status_code=410, detail="Export download expired or exhausted")
    
    if not os.path.exists(export_request.file_path):
        raise HTTPException(status_code=404, detail="Export file not found")
    
    # Update download counter
    export_request.increment_download_count()
    db.commit()
    
    # Determine filename and media type
    filename = f"export_{export_request.export_type.value}_{export_request.created_at.strftime('%Y%m%d')}"
    
    if export_request.export_format == ExportFormat.JSON:
        filename += ".json"
        media_type = "application/json"
    elif export_request.export_format == ExportFormat.CSV:
        filename += ".csv"
        media_type = "text/csv"
    elif export_request.export_format == ExportFormat.ZIP:
        filename += ".zip"
        media_type = "application/zip"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(
        path=export_request.file_path,
        filename=filename,
        media_type=media_type
    )

@router.get("/history")
async def get_export_history(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get user's export history"""
    
    exports = db.query(DataExport).filter(
        DataExport.requested_by == current_user.id
    ).order_by(DataExport.created_at.desc()).limit(limit).all()
    
    return {
        "exports": [
            {
                "export_id": str(export.id),
                "export_type": export.export_type.value,
                "export_format": export.export_format.value,
                "status": export.status.value,
                "created_at": export.created_at.isoformat(),
                "completed_at": export.completed_at.isoformat() if export.completed_at else None,
                "record_count": export.record_count,
                "file_size_bytes": export.file_size_bytes,
                "download_available": export.is_downloadable,
                "downloads_remaining": export.max_downloads - export.download_count if export.status == ExportStatus.COMPLETED else 0
            }
            for export in exports
        ]
    }

# Request models
class TranscriptionExportRequest(BaseModel):
    session_ids: Optional[List[UUID]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    export_format: ExportFormat = ExportFormat.JSON
```

## 🧪 Test Scenarios

### Export Service Tests
```python
def test_user_data_export_creation():
    """Test complete user data export"""
    user = create_test_user(db)
    client = create_test_client(db, user.id)
    session = create_test_session(db, user.id)
    usage_log = create_usage_log(db, user.id, session.id)
    
    export_service = DataExportService(db)
    export_request = export_service.create_export_request(
        export_type=ExportType.USER_DATA,
        export_format=ExportFormat.JSON,
        requested_by=user.id
    )
    
    # Process export
    completed_export = export_service.process_export(export_request.id)
    
    assert completed_export.status == ExportStatus.COMPLETED
    assert completed_export.record_count > 0
    assert os.path.exists(completed_export.file_path)

def test_transcription_export_with_filters():
    """Test transcription export with date filters"""
    user = create_test_user(db)
    old_session = create_test_session(db, user.id, created_at=datetime.utcnow() - timedelta(days=10))
    new_session = create_test_session(db, user.id, created_at=datetime.utcnow() - timedelta(days=1))
    
    export_service = DataExportService(db)
    export_request = export_service.create_export_request(
        export_type=ExportType.TRANSCRIPTIONS,
        export_format=ExportFormat.JSON,
        requested_by=user.id,
        export_filters={
            "date_from": (datetime.utcnow() - timedelta(days=5)).isoformat()
        }
    )
    
    completed_export = export_service.process_export(export_request.id)
    
    # Should only include new session
    assert completed_export.record_count == 1
```

### API Integration Tests
```bash
# Test: Request user data export
curl -X POST "/api/v1/exports/user-data?export_format=json" \
  -H "Authorization: Bearer $TOKEN"

# Expected: Returns export_id and status

# Test: Check export status
curl -X GET "/api/v1/exports/status/$EXPORT_ID" \
  -H "Authorization: Bearer $TOKEN"

# Expected: Returns processing status and progress

# Test: Download completed export
curl -X GET "/api/v1/exports/$EXPORT_ID/download?token=$DOWNLOAD_TOKEN" \
  -H "Authorization: Bearer $TOKEN" \
  -o export_data.json

# Expected: Downloads export file
```

## 📊 Success Metrics

### Export Performance
- **Processing Speed**: <5 minutes for standard user data export
- **File Generation**: Support for datasets up to 100MB
- **Download Success Rate**: >99% successful downloads
- **Format Accuracy**: 100% data integrity across all export formats

### User Satisfaction
- **Self-Service Usage**: 90% of export requests completed without support
- **GDPR Compliance**: 100% compliance with data portability requirements
- **Export Completeness**: 100% of user data included in exports

## 📋 Definition of Done

- [ ] **Export Models**: Comprehensive data export and archive tracking models
- [ ] **Export Service**: Complete export processing for all data types
- [ ] **Multiple Formats**: Support for JSON, CSV, XLSX, ZIP formats
- [ ] **Secure Downloads**: Token-based secure download system
- [ ] **Background Processing**: Async export processing for large datasets
- [ ] **User Interface**: Self-service export request and download interface
- [ ] **Admin Exports**: System-wide export capabilities for administrators
- [ ] **Data Archival**: Cold storage integration for long-term archives
- [ ] **Unit Tests**: >85% coverage for export components
- [ ] **Integration Tests**: End-to-end export and download workflows
- [ ] **Documentation**: User guide for data export and portability features

## 🔄 Dependencies & Risks

### Dependencies
- ✅ User authentication and authorization system
- ⏳ File storage infrastructure for export files
- ⏳ Background task processing (Celery) for large exports
- ⏳ Cold storage integration for archival system

### Risks & Mitigations
- **Risk**: Large exports impacting system performance
  - **Mitigation**: Background processing, rate limiting, resource monitoring
- **Risk**: Export file security and access control
  - **Mitigation**: Secure tokens, time-limited downloads, access logging
- **Risk**: Storage costs for export and archive files
  - **Mitigation**: Automatic cleanup, compression, cold storage tiers

## 📞 Stakeholders

**Product Owner**: Product Team, Legal/Compliance  
**Technical Lead**: Backend Engineering, DevOps  
**Reviewers**: Data Protection Officer, Security Team, Infrastructure  
**QA Focus**: Data completeness, GDPR compliance, Security testing