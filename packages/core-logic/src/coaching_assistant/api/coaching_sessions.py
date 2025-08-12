"""Coaching sessions API endpoints."""

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as FastAPIFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func
from pydantic import BaseModel, Field
import logging
import re
import json

from ..core.database import get_db
from ..models import CoachingSession, Client, User, SessionSource
from ..models.session import Session, SessionStatus
from ..models.transcript import TranscriptSegment
from ..api.auth import get_current_user_dependency

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class CoachingSessionCreate(BaseModel):
    session_date: date
    client_id: UUID
    source: SessionSource = SessionSource.CLIENT  # Default to CLIENT
    duration_min: int = Field(..., gt=0)
    fee_currency: str = Field(..., min_length=3, max_length=3)
    fee_amount: int = Field(..., ge=0)
    notes: Optional[str] = None


class CoachingSessionUpdate(BaseModel):
    session_date: Optional[date] = None
    client_id: Optional[UUID] = None
    source: Optional[SessionSource] = None
    duration_min: Optional[int] = Field(None, gt=0)
    fee_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    fee_amount: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None
    audio_timeseq_id: Optional[UUID] = None  # TECHNICAL DEBT: Confusing name - actually stores session.id (transcription session ID)


class ClientSummary(BaseModel):
    id: UUID
    name: str
    is_anonymized: bool


class CoachingSessionResponse(BaseModel):
    id: UUID
    session_date: str
    client: ClientSummary
    client_id: UUID  # Add missing client_id field  
    source: SessionSource
    duration_min: int
    fee_currency: str
    fee_amount: int
    fee_display: str
    duration_display: str
    transcript_timeseq_id: Optional[UUID]  # TECHNICAL DEBT: Purpose unclear, consider removing
    audio_timeseq_id: Optional[UUID]  # TECHNICAL DEBT: Confusing name - actually stores session.id (transcription session ID)
    notes: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CoachingSessionListResponse(BaseModel):
    items: List[CoachingSessionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SessionSourceOption(BaseModel):
    value: str
    label: str


@router.get("", response_model=CoachingSessionListResponse)
async def list_coaching_sessions(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    client_id: Optional[UUID] = None,
    currency: Optional[str] = None,
    sort: str = Query("-session_date", regex="^-?(session_date|fee)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """List coaching sessions for the current user."""
    query_filter = and_(CoachingSession.coach_id == current_user.id)
    
    # Apply filters
    if from_date:
        query_filter = and_(query_filter, CoachingSession.session_date >= from_date)
    if to_date:
        query_filter = and_(query_filter, CoachingSession.session_date <= to_date)
    if client_id:
        query_filter = and_(query_filter, CoachingSession.client_id == client_id)
    if currency:
        query_filter = and_(query_filter, CoachingSession.fee_currency == currency)
    
    # Build query with joins
    query = (
        db.query(CoachingSession)
        .join(Client, CoachingSession.client_id == Client.id)
        .filter(query_filter)
    )
    
    # Apply sorting
    if sort == "session_date":
        query = query.order_by(asc(CoachingSession.session_date))
    elif sort == "-session_date":
        query = query.order_by(desc(CoachingSession.session_date))
    elif sort == "fee":
        query = query.order_by(asc(CoachingSession.fee_currency), asc(CoachingSession.fee_amount))
    elif sort == "-fee":
        query = query.order_by(desc(CoachingSession.fee_currency), desc(CoachingSession.fee_amount))
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    sessions = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Build response
    session_responses = []
    for session in sessions:
        client_summary = ClientSummary(
            id=session.client.id,
            name=session.client.name,
            is_anonymized=session.client.is_anonymized
        )
        
        session_dict = {
            "id": session.id,
            "session_date": session.session_date.isoformat(),
            "client": client_summary,
            "client_id": session.client_id,
            "source": session.source,
            "duration_min": session.duration_min,
            "fee_currency": session.fee_currency,
            "fee_amount": session.fee_amount,
            "fee_display": session.fee_display,
            "duration_display": session.duration_display,
            "transcript_timeseq_id": session.transcript_timeseq_id,
            "audio_timeseq_id": session.audio_timeseq_id,
            "notes": session.notes,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
        session_responses.append(CoachingSessionResponse(**session_dict))
    
    total_pages = (total + page_size - 1) // page_size
    
    return CoachingSessionListResponse(
        items=session_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{session_id}", response_model=CoachingSessionResponse)
async def get_coaching_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get a specific coaching session."""
    session = (
        db.query(CoachingSession)
        .join(Client, CoachingSession.client_id == Client.id)
        .filter(
            and_(CoachingSession.id == session_id, CoachingSession.coach_id == current_user.id)
        ).first()
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Coaching session not found")
    
    client_summary = ClientSummary(
        id=session.client.id,
        name=session.client.name,
        is_anonymized=session.client.is_anonymized
    )
    
    session_dict = {
        "id": session.id,
        "session_date": session.session_date.isoformat(),
        "client": client_summary,
        "client_id": session.client_id,
        "source": session.source,
        "duration_min": session.duration_min,
        "fee_currency": session.fee_currency,
        "fee_amount": session.fee_amount,
        "fee_display": session.fee_display,
        "duration_display": session.duration_display,
        "transcript_timeseq_id": session.transcript_timeseq_id,
        "audio_timeseq_id": session.audio_timeseq_id,
        "notes": session.notes,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }
    
    return CoachingSessionResponse(**session_dict)


@router.post("", response_model=CoachingSessionResponse)
async def create_coaching_session(
    session_data: CoachingSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Create a new coaching session."""
    # Verify client belongs to current user
    client = db.query(Client).filter(
        and_(Client.id == session_data.client_id, Client.coach_id == current_user.id)
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    session = CoachingSession(
        coach_id=current_user.id,
        session_date=session_data.session_date,
        client_id=session_data.client_id,
        source=session_data.source,
        duration_min=session_data.duration_min,
        fee_currency=session_data.fee_currency.upper(),
        fee_amount=session_data.fee_amount,
        notes=session_data.notes
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Reload to get client data
    session = (
        db.query(CoachingSession)
        .join(Client, CoachingSession.client_id == Client.id)
        .filter(CoachingSession.id == session.id)
        .first()
    )
    
    client_summary = ClientSummary(
        id=session.client.id,
        name=session.client.name,
        is_anonymized=session.client.is_anonymized
    )
    
    session_dict = {
        "id": session.id,
        "session_date": session.session_date.isoformat(),
        "client": client_summary,
        "client_id": session.client_id,
        "source": session.source,
        "duration_min": session.duration_min,
        "fee_currency": session.fee_currency,
        "fee_amount": session.fee_amount,
        "fee_display": session.fee_display,
        "duration_display": session.duration_display,
        "transcript_timeseq_id": session.transcript_timeseq_id,
        "audio_timeseq_id": session.audio_timeseq_id,
        "notes": session.notes,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }
    
    return CoachingSessionResponse(**session_dict)


@router.patch("/{session_id}", response_model=CoachingSessionResponse)
async def update_coaching_session(
    session_id: UUID,
    session_data: CoachingSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Update a coaching session."""
    session = db.query(CoachingSession).filter(
        and_(CoachingSession.id == session_id, CoachingSession.coach_id == current_user.id)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Coaching session not found")
    
    # Verify client belongs to current user if client_id is being updated
    if session_data.client_id and session_data.client_id != session.client_id:
        client = db.query(Client).filter(
            and_(Client.id == session_data.client_id, Client.coach_id == current_user.id)
        ).first()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
    
    # Update fields
    update_data = session_data.dict(exclude_unset=True)
    if 'fee_currency' in update_data:
        update_data['fee_currency'] = update_data['fee_currency'].upper()
    
    # Convert audio_timeseq_id string to UUID if present
    if 'audio_timeseq_id' in update_data and update_data['audio_timeseq_id'] is not None:
        from uuid import UUID
        try:
            if isinstance(update_data['audio_timeseq_id'], str):
                update_data['audio_timeseq_id'] = UUID(update_data['audio_timeseq_id'])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid audio_timeseq_id format: {str(e)}")
    
    for field, value in update_data.items():
        setattr(session, field, value)
    
    db.commit()
    db.refresh(session)
    
    # Reload to get client data
    session = (
        db.query(CoachingSession)
        .join(Client, CoachingSession.client_id == Client.id)
        .filter(CoachingSession.id == session.id)
        .first()
    )
    
    client_summary = ClientSummary(
        id=session.client.id,
        name=session.client.name,
        is_anonymized=session.client.is_anonymized
    )
    
    session_dict = {
        "id": session.id,
        "session_date": session.session_date.isoformat(),
        "client": client_summary,
        "client_id": session.client_id,
        "source": session.source,
        "duration_min": session.duration_min,
        "fee_currency": session.fee_currency,
        "fee_amount": session.fee_amount,
        "fee_display": session.fee_display,
        "duration_display": session.duration_display,
        "transcript_timeseq_id": session.transcript_timeseq_id,
        "audio_timeseq_id": session.audio_timeseq_id,
        "notes": session.notes,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }
    
    return CoachingSessionResponse(**session_dict)


@router.delete("/{session_id}")
async def delete_coaching_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Delete a coaching session (hard delete)."""
    session = db.query(CoachingSession).filter(
        and_(CoachingSession.id == session_id, CoachingSession.coach_id == current_user.id)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Coaching session not found")
    
    db.delete(session)
    db.commit()
    
    return {"message": "Coaching session deleted successfully"}


@router.get("/options/currencies")
async def get_currencies():
    """Get available currency options."""
    return [
        {"value": "USD", "label": "USD - US Dollar"},
        {"value": "EUR", "label": "EUR - Euro"},
        {"value": "JPY", "label": "JPY - Japanese Yen"},
        {"value": "GBP", "label": "GBP - British Pound"},
        {"value": "AUD", "label": "AUD - Australian Dollar"},
        {"value": "CAD", "label": "CAD - Canadian Dollar"},
        {"value": "CHF", "label": "CHF - Swiss Franc"},
        {"value": "CNY", "label": "CNY - Chinese Yuan"},
        {"value": "SEK", "label": "SEK - Swedish Krona"},
        {"value": "NZD", "label": "NZD - New Zealand Dollar"},
        {"value": "MXN", "label": "MXN - Mexican Peso"},
        {"value": "SGD", "label": "SGD - Singapore Dollar"},
        {"value": "HKD", "label": "HKD - Hong Kong Dollar"},
        {"value": "NOK", "label": "NOK - Norwegian Krone"},
        {"value": "KRW", "label": "KRW - South Korean Won"},
        {"value": "TRY", "label": "TRY - Turkish Lira"},
        {"value": "RUB", "label": "RUB - Russian Ruble"},
        {"value": "INR", "label": "INR - Indian Rupee"},
        {"value": "BRL", "label": "BRL - Brazilian Real"},
        {"value": "ZAR", "label": "ZAR - South African Rand"},
        {"value": "TWD", "label": "TWD - Taiwan Dollar"}
    ]


@router.post("/{session_id}/transcript")
async def upload_session_transcript(
    session_id: UUID,
    file: UploadFile = FastAPIFile(...),
    speaker_roles: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Upload a VTT or SRT transcript file directly to a coaching session."""
    
    logger.info(f"🔍 Transcript upload request: session_id={session_id}, user_id={current_user.id}, filename={file.filename}")
    
    # Parse speaker role mapping if provided
    speaker_role_mapping = {}
    if speaker_roles:
        try:
            speaker_role_mapping = json.loads(speaker_roles)
            logger.info(f"📋 Speaker role mapping: {speaker_role_mapping}")
        except json.JSONDecodeError:
            logger.warning(f"⚠️ Invalid speaker roles JSON: {speaker_roles}")
            raise HTTPException(status_code=400, detail="Invalid speaker roles format")
    
    # Check if session exists at all
    session_exists = db.query(CoachingSession).filter(CoachingSession.id == session_id).first()
    if not session_exists:
        logger.warning(f"❌ Coaching session {session_id} does not exist in database")
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found in database")
    
    # Check if session belongs to user (note: coach_id actually stores user.id)
    session = db.query(CoachingSession).filter(
        CoachingSession.id == session_id,
        CoachingSession.coach_id == current_user.id
    ).first()
    
    if not session:
        logger.warning(f"❌ Coaching session {session_id} exists but does not belong to user {current_user.id}")
        logger.info(f"📊 Session owner: {session_exists.coach_id}, requesting user: {current_user.id}")
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    
    # Check file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ['vtt', 'srt']:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file format. Only VTT and SRT files are supported."
        )
    
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Parse the transcript with speaker role mapping
        segments = []
        if file_extension == 'vtt':
            segments = _parse_vtt_content(content_str, speaker_role_mapping)
        elif file_extension == 'srt':
            segments = _parse_srt_content(content_str, speaker_role_mapping)
        
        if not segments:
            raise HTTPException(status_code=400, detail="No valid transcript segments found in file")
        
        # Calculate total duration
        total_duration = 0
        for segment_data in segments:
            total_duration = max(total_duration, segment_data['end_sec'])
        
        # Create a transcription session for this manual upload
        transcription_session_id = uuid4()
        transcription_session = Session(
            id=transcription_session_id,
            user_id=current_user.id,
            title=f"Manual Upload - {session.session_date}",
            status=SessionStatus.COMPLETED,
            language="auto",  # Will be determined from content
            duration_sec=int(total_duration),
            audio_filename=file.filename.replace('.vtt', '.manual').replace('.srt', '.manual')
        )
        db.add(transcription_session)
        
        # Save segments to database (linked to transcription session)
        for i, segment_data in enumerate(segments):
            segment = TranscriptSegment(
                id=uuid4(),
                session_id=transcription_session_id,  # Link to transcription session
                speaker_id=segment_data.get('speaker_id', 1),  # Default to speaker 1
                start_sec=segment_data['start_sec'],
                end_sec=segment_data['end_sec'],
                content=segment_data['content'],
                confidence=1.0  # Manual upload, assume high confidence
            )
            db.add(segment)
        
        # Update coaching session to reference the transcription session
        session.audio_timeseq_id = str(transcription_session_id)
        session.duration_sec = int(total_duration)
        
        db.commit()
        
        logger.info(f"✅ Successfully uploaded transcript: {len(segments)} segments, {total_duration:.2f}s duration")
        
        return {
            "message": "Transcript uploaded successfully",
            "session_id": str(session_id),
            "transcription_session_id": transcription_session_id,
            "segments_count": len(segments),
            "duration_sec": total_duration
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported. Please use UTF-8 encoding.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading transcript: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process transcript: {str(e)}")


def _parse_vtt_content(content: str, speaker_role_mapping: dict = None) -> List[dict]:
    """Parse VTT file content and return segments."""
    segments = []
    lines = content.strip().split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip header and empty lines
        if line == 'WEBVTT' or line == '' or line.startswith('NOTE'):
            i += 1
            continue
        
        # Look for timestamp line
        if '-->' in line:
            # Parse timestamp
            timestamp_match = re.match(r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})', line)
            if timestamp_match:
                start_time = _parse_timestamp(timestamp_match.group(1))
                end_time = _parse_timestamp(timestamp_match.group(2))
                
                # Get the content (next line)
                i += 1
                if i < len(lines):
                    content_line = lines[i].strip()
                    
                    # Extract speaker and content from VTT format like "<v jolly shih>content</v>" or "<v Speaker>content</v>"
                    speaker_id = 1
                    content_text = content_line
                    speaker_key = None
                    
                    # Match the frontend logic for extracting speaker names
                    speaker_match = re.match(r'<v\s+([^>]+)>\s*(.*?)(?:</v>)?$', content_line)
                    if speaker_match:
                        speaker_name = speaker_match.group(1).strip()
                        content_text = speaker_match.group(2)
                        # Create speaker key like the frontend: speaker_jolly_shih, speaker_howie_yu
                        speaker_key = f"speaker_{speaker_name.lower().replace(' ', '_')}"
                    
                    # Apply role mapping if provided, otherwise use default assignment
                    final_speaker_id = speaker_id
                    if speaker_role_mapping and speaker_key:
                        # Use the speaker key to look up the role
                        role = speaker_role_mapping.get(speaker_key, 'coach')
                        final_speaker_id = 1 if role == 'coach' else 2
                    elif speaker_match:
                        # Fallback to name-based assignment when no role mapping is provided
                        speaker_name = speaker_match.group(1).strip()
                        final_speaker_id = 2 if '客戶' in speaker_name or 'Client' in speaker_name else 1
                    
                    segments.append({
                        'start_sec': start_time,
                        'end_sec': end_time,
                        'content': content_text,
                        'speaker_id': final_speaker_id
                    })
        
        i += 1
    
    return segments


def _parse_srt_content(content: str, speaker_role_mapping: dict = None) -> List[dict]:
    """Parse SRT file content and return segments."""
    segments = []
    
    # Split by double newline to get individual subtitle blocks
    blocks = re.split(r'\n\s*\n', content.strip())
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        # Skip sequence number (line 0)
        # Parse timestamp (line 1)
        timestamp_line = lines[1].strip()
        timestamp_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', timestamp_line)
        
        if timestamp_match:
            start_time = _parse_timestamp(timestamp_match.group(1).replace(',', '.'))
            end_time = _parse_timestamp(timestamp_match.group(2).replace(',', '.'))
            
            # Content (lines 2+)
            content_lines = lines[2:]
            content_text = ' '.join(content_lines)
            
            # Extract speaker info if present
            speaker_id = 1
            
            # Look for speaker prefix like "教練: " or "Coach: " or "說話者 2:"
            speaker_match = re.match(r'(.*?):\s*(.*)', content_text)
            if speaker_match:
                speaker_name = speaker_match.group(1)
                content_text = speaker_match.group(2)
                
                # Try to extract speaker ID from name
                speaker_num_match = re.search(r'(\d+)', speaker_name)
                if speaker_num_match:
                    speaker_id = int(speaker_num_match.group(1))
                else:
                    # Fallback to name-based assignment
                    speaker_id = 2 if '客戶' in speaker_name or 'Client' in speaker_name else 1
            
            # Apply role mapping if provided, otherwise use default assignment
            final_speaker_id = speaker_id
            if speaker_role_mapping:
                role = speaker_role_mapping.get(str(speaker_id), 'coach')
                final_speaker_id = 1 if role == 'coach' else 2
            
            segments.append({
                'start_sec': start_time,
                'end_sec': end_time,
                'content': content_text,
                'speaker_id': final_speaker_id
            })
    
    return segments


def _parse_timestamp(timestamp_str: str) -> float:
    """Convert timestamp string to seconds."""
    # Handle format: HH:MM:SS.mmm
    time_parts = timestamp_str.split(':')
    if len(time_parts) != 3:
        raise ValueError(f"Invalid timestamp format: {timestamp_str}")
    
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds_str = time_parts[2]
    
    # Handle seconds with milliseconds
    if '.' in seconds_str:
        seconds, milliseconds = seconds_str.split('.')
        total_seconds = hours * 3600 + minutes * 60 + int(seconds) + int(milliseconds) / 1000
    else:
        total_seconds = hours * 3600 + minutes * 60 + int(seconds_str)
    
    return total_seconds