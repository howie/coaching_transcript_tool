# 系統架構模式 (System Patterns)

**更新時間：** 2025-08-04 22:45  
**架構版本：** v3.0 (Coach Assistant MVP - Render + PostgreSQL + GCS)

## 🏗️ 總體架構模式

### 混合雲架構 (Hybrid Cloud Architecture)
```
┌─────────────────────────────────────────────────────────────┐
│                    Cloudflare Workers                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Frontend                                │ │
│  │  • Next.js 14 + Tailwind CSS                          │ │
│  │  • React Hook Form + Zustand                          │ │
│  │  • SWR + JWT refresh                                  │ │
│  │  • Global Edge Distribution                           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │ HTTPS API calls
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Render.com                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                Backend Services                         │ │
│  │  • FastAPI + OAuth2 Bearer                            │ │
│  │  • Celery + Redis (Background Tasks)                  │ │
│  │  • SQLAlchemy ORM + Alembic                          │ │
│  │  • PostgreSQL Database                                │ │
│  │  • WebSocket 進度推播                                  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │ GCS SDK calls
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Google Cloud Platform                     │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ Cloud Storage   │    │     Speech-to-Text v2          │ │
│  │ • Audio Files   │    │ • 自動語音轉文字                  │ │
│  │ • Signed URLs   │    │ • Speaker Diarization          │ │
│  │ • Lifecycle     │    │ • 多語言支援                     │ │
│  │   Rules (1 day) │    │ • Phrase Hints                 │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Monorepo 模式 (Apps + Packages)
```
coaching_transcript_tool/
├── Makefile                # 🔧 統一專案管理
├── apps/                   # 可獨立部署的應用程式
│   ├── web/                # 前端 (Next.js on Cloudflare Workers)
│   │   ├── app/            # Next.js App Router
│   │   ├── components/     # React 組件庫
│   │   ├── contexts/       # State Management
│   │   ├── wrangler.toml   # Cloudflare 部署配置
│   │   └── package.json    # 前端依賴管理
│   │
│   ├── api-server/         # 後端 API (FastAPI on Render)
│   │   ├── main.py         # FastAPI 應用入口
│   │   ├── requirements.txt# Python 依賴
│   │   └── render.yaml     # Render 部署配置
│   │
│   └── cli/                # 命令列工具 (保留現有功能)
│
├── packages/               # 共用套件
│   └── core-logic/         # 核心業務邏輯
│       ├── src/coaching_assistant/
│       │   ├── models/     # 資料模型 (SQLAlchemy)
│       │   ├── repositories/ # Repository Pattern
│       │   ├── services/   # 業務邏輯服務
│       │   └── integrations/ # 外部服務整合
│       └── tests/          # 測試檔案
│
├── docs/                   # 正式專案文檔
└── memory-bank/            # Cline 工作記憶
```

**混合雲架構優勢：**
- **前端最佳化**：Cloudflare Workers 全球邊緣網路
- **後端靈活性**：Render 簡化部署和資料庫管理
- **服務整合**：Google Cloud 深度 AI 服務整合
- **成本效益**：各取所長，避免單一平台鎖定

## 📊 資料模型與 Repository Pattern

### 核心資料模型
```python
# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    avatar_url = Column(String)
    google_id = Column(String, unique=True)
    plan = Column(Enum(UserPlan), default=UserPlan.FREE)
    usage_minutes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    audio_filename = Column(String)
    duration_sec = Column(Integer)
    language = Column(String, default="auto")
    status = Column(Enum(SessionStatus), default=SessionStatus.UPLOADING)
    gcs_audio_path = Column(String)  # Google Cloud Storage path
    transcription_job_id = Column(String)  # Google STT job ID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    segments = relationship("TranscriptSegment", back_populates="session", cascade="all, delete-orphan")
    roles = relationship("SessionRole", back_populates="session", cascade="all, delete-orphan")

class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    speaker_id = Column(Integer, nullable=False)  # From STT diarization
    start_sec = Column(Float, nullable=False)
    end_sec = Column(Float, nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Float)  # STT confidence score
    
    # Relationships
    session = relationship("Session", back_populates="segments")

class SessionRole(Base):
    __tablename__ = "session_roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    speaker_id = Column(Integer, nullable=False)
    role = Column(Enum(SpeakerRole), nullable=False)  # COACH, CLIENT
    
    # Relationships
    session = relationship("Session", back_populates="roles")
```

### Repository Pattern 實作
```python
# Abstract Repository Interface
class BaseRepository(ABC):
    def __init__(self, db: Session):
        self.db = db
    
    @abstractmethod
    def create(self, **kwargs):
        pass
    
    @abstractmethod
    def get_by_id(self, id: UUID):
        pass
    
    @abstractmethod
    def update(self, id: UUID, **kwargs):
        pass
    
    @abstractmethod
    def delete(self, id: UUID):
        pass

# User Repository Implementation
class UserRepository(BaseRepository):
    def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_google_id(self, google_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.google_id == google_id).first()
    
    def update_usage(self, user_id: UUID, minutes: int) -> bool:
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.usage_minutes += minutes
            user.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

# Session Repository Implementation
class SessionRepository(BaseRepository):
    def create(self, **kwargs) -> Session:
        session = Session(**kwargs)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_user_sessions(self, user_id: UUID, limit: int = 50) -> List[Session]:
        return self.db.query(Session)\
            .filter(Session.user_id == user_id)\
            .order_by(Session.created_at.desc())\
            .limit(limit)\
            .all()
    
    def update_status(self, session_id: UUID, status: SessionStatus) -> bool:
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if session:
            session.status = status
            self.db.commit()
            return True
        return False
```

## 🔄 服務層模式 (Service Layer Pattern)

### 認證服務
```python
class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.google_client = GoogleOAuthClient()
    
    async def authenticate_google_user(self, id_token: str) -> AuthResult:
        # Verify Google ID token
        google_user = await self.google_client.verify_token(id_token)
        
        # Get or create user
        user = self.user_repo.get_by_google_id(google_user.id)
        if not user:
            user = self.user_repo.create(
                email=google_user.email,
                name=google_user.name,
                avatar_url=google_user.picture,
                google_id=google_user.id
            )
        
        # Generate JWT
        access_token = self._generate_jwt(user)
        refresh_token = self._generate_refresh_token(user)
        
        return AuthResult(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token
        )
```

### 轉錄服務
```python
class TranscriptionService:
    def __init__(
        self, 
        session_repo: SessionRepository,
        gcs_client: GCSClient,
        stt_client: GoogleSTTClient,
        celery_app: Celery
    ):
        self.session_repo = session_repo
        self.gcs_client = gcs_client
        self.stt_client = stt_client
        self.celery = celery_app
    
    async def start_transcription(self, session_id: UUID, audio_file: UploadFile) -> TranscriptionJob:
        # Upload to Google Cloud Storage
        gcs_path = await self.gcs_client.upload_audio(audio_file, session_id)
        
        # Update session with GCS path
        self.session_repo.update(session_id, gcs_audio_path=gcs_path)
        
        # Start background transcription job
        job = self.celery.send_task(
            'transcription.process_audio',
            args=[str(session_id), gcs_path],
            queue='transcription'
        )
        
        return TranscriptionJob(
            job_id=job.id,
            session_id=session_id,
            status=JobStatus.QUEUED
        )
    
    async def get_transcription_result(self, session_id: UUID) -> TranscriptionResult:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFound(session_id)
        
        if session.status == SessionStatus.COMPLETED:
            segments = self.session_repo.get_segments(session_id)
            return TranscriptionResult(
                session=session,
                segments=segments,
                download_urls=self._generate_download_urls(session_id)
            )
        
        return TranscriptionResult(
            session=session,
            segments=[],
            progress=self._get_job_progress(session.transcription_job_id)
        )
```

## 🎯 背景任務模式 (Celery + Redis)

### Celery 任務定義
```python
from celery import Celery

celery_app = Celery(
    'coaching_assistant',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@celery_app.task(bind=True, max_retries=3)
def process_audio_transcription(self, session_id: str, gcs_audio_path: str):
    try:
        # Update status to processing
        session_repo.update_status(UUID(session_id), SessionStatus.PROCESSING)
        
        # Call Google Speech-to-Text API
        stt_client = GoogleSTTClient()
        transcription_result = stt_client.transcribe_with_diarization(
            gcs_uri=gcs_audio_path,
            language_code='zh-TW',
            enable_speaker_diarization=True,
            diarization_speaker_count=2
        )
        
        # Save segments to database
        segments = []
        for segment in transcription_result.segments:
            segment_data = TranscriptSegment(
                session_id=UUID(session_id),
                speaker_id=segment.speaker_tag,
                start_sec=segment.start_time,
                end_sec=segment.end_time,
                content=segment.transcript,
                confidence=segment.confidence
            )
            segments.append(segment_data)
        
        # Bulk insert segments
        session_repo.create_segments(segments)
        
        # Update session status
        session_repo.update_status(
            UUID(session_id), 
            SessionStatus.COMPLETED,
            duration_sec=transcription_result.duration
        )
        
        # Clean up GCS audio file (optional - lifecycle rule handles this)
        # gcs_client.delete_file(gcs_audio_path)
        
        return {
            'session_id': session_id,
            'segments_count': len(segments),
            'duration': transcription_result.duration
        }
        
    except Exception as exc:
        # Update status to failed
        session_repo.update_status(UUID(session_id), SessionStatus.FAILED)
        
        # Retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        raise exc
```

## 🔌 外部服務整合模式

### Google Cloud Storage 客戶端
```python
class GCSClient:
    def __init__(self, bucket_name: str, credentials_json: str):
        self.client = storage.Client.from_service_account_info(
            json.loads(credentials_json)
        )
        self.bucket = self.client.bucket(bucket_name)
    
    async def upload_audio(self, audio_file: UploadFile, session_id: UUID) -> str:
        # Generate unique file path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = f"audio/{session_id}/{timestamp}_{audio_file.filename}"
        
        # Upload to GCS
        blob = self.bucket.blob(file_path)
        await blob.upload_from_file(audio_file.file, content_type=audio_file.content_type)
        
        return f"gs://{self.bucket.name}/{file_path}"
    
    def generate_signed_upload_url(self, file_path: str, expiration_minutes: int = 15) -> str:
        blob = self.bucket.blob(file_path)
        return blob.generate_signed_url(
            version="v4",
            expiration=datetime.utcnow() + timedelta(minutes=expiration_minutes),
            method="PUT"
        )
```

### Google Speech-to-Text 客戶端
```python
class GoogleSTTClient:
    def __init__(self, credentials_json: str):
        self.client = speech.SpeechClient.from_service_account_info(
            json.loads(credentials_json)
        )
    
    def transcribe_with_diarization(
        self, 
        gcs_uri: str, 
        language_code: str = 'zh-TW',
        enable_speaker_diarization: bool = True,
        diarization_speaker_count: int = 2
    ) -> TranscriptionResult:
        
        # Configure recognition
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=44100,
            language_code=language_code,
            enable_speaker_diarization=enable_speaker_diarization,
            diarization_speaker_count=diarization_speaker_count,
            enable_automatic_punctuation=True,
            model='latest_long'
        )
        
        audio = speech.RecognitionAudio(uri=gcs_uri)
        
        # Long running operation for audio > 1 minute
        operation = self.client.long_running_recognize(
            config=config,
            audio=audio
        )
        
        # Wait for completion
        response = operation.result(timeout=3600)  # 1 hour timeout
        
        # Process results
        segments = []
        for result in response.results:
            for word in result.alternatives[0].words:
                segments.append(TranscriptSegment(
                    speaker_tag=word.speaker_tag,
                    start_time=word.start_time.total_seconds(),
                    end_time=word.end_time.total_seconds(),
                    transcript=word.word,
                    confidence=result.alternatives[0].confidence
                ))
        
        return TranscriptionResult(
            segments=self._merge_segments_by_speaker(segments),
            duration=response.total_billed_time.total_seconds()
        )
```

## 🌐 API 路由模式

### RESTful API 設計
```python
from fastapi import APIRouter, Depends, UploadFile, File
from .dependencies import get_current_user, get_db

router = APIRouter(prefix="/api/v1", tags=["transcription"])

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    session_data: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_repo = SessionRepository(db)
    session = session_repo.create(
        user_id=current_user.id,
        title=session_data.title,
        language=session_data.language
    )
    return SessionResponse.from_orm(session)

@router.post("/sessions/{session_id}/upload")
async def upload_audio(
    session_id: UUID,
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    transcription_service: TranscriptionService = Depends()
):
    # Validate file
    if not audio_file.content_type.startswith('audio/'):
        raise HTTPException(400, "Only audio files are allowed")
    
    if audio_file.size > 500 * 1024 * 1024:  # 500MB limit
        raise HTTPException(400, "File too large")
    
    # Start transcription
    job = await transcription_service.start_transcription(session_id, audio_file)
    return {"job_id": job.job_id, "status": "queued"}

@router.get("/sessions/{session_id}/progress")
async def get_transcription_progress(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    transcription_service: TranscriptionService = Depends()
):
    result = await transcription_service.get_transcription_result(session_id)
    return {
        "status": result.session.status,
        "progress": result.progress,
        "segments_count": len(result.segments)
    }

@router.patch("/sessions/{session_id}/roles")
async def assign_speaker_roles(
    session_id: UUID,
    role_assignments: List[SpeakerRoleAssignment],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_repo = SessionRepository(db)
    session_repo.assign_speaker_roles(session_id, role_assignments)
    return {"message": "Roles assigned successfully"}

@router.get("/sessions/{session_id}/transcript")
async def download_transcript(
    session_id: UUID,
    format: str = Query(..., regex="^(vtt|srt|json|txt)$"),
    current_user: User = Depends(get_current_user),
    transcript_service: TranscriptService = Depends()
):
    transcript_data = await transcript_service.export_transcript(session_id, format)
    
    return Response(
        content=transcript_data,
        media_type=f"application/{format}",
        headers={
            "Content-Disposition": f"attachment; filename=transcript.{format}"
        }
    )
```

## 🔗 WebSocket 進度推播模式

### WebSocket Manager
```python
from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
    
    async def send_progress_update(self, session_id: str, data: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await connection.send_json(data)

manager = ConnectionManager()

@router.websocket("/ws/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

# Background task 中使用
@celery_app.task
def update_transcription_progress(session_id: str, progress: int):
    asyncio.run(manager.send_progress_update(session_id, {
        "type": "progress_update",
        "session_id": session_id,
        "progress": progress,
        "timestamp": datetime.utcnow().isoformat()
    }))
```

## 🛡️ 安全模式

### JWT 認證
```python
from jose import JWTError, jwt
from passlib.context import CryptContext

class JWTService:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

# Dependency for protected routes
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    jwt_service = JWTService(settings.SECRET_KEY)
    payload = jwt_service.verify_token(token)
    
    if payload is None:
        raise HTTPException(401, "Invalid authentication credentials")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(401, "Invalid authentication credentials")
    
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(UUID(user_id))
    
    if user is None:
        raise HTTPException(401, "User not found")
    
    return user
```

## 📊 監控與日誌模式

### 結構化日誌
```python
import structlog

logger = structlog.get_logger()

class LoggingMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            # Log request
            logger.info(
                "http_request_start",
                method=scope["method"],
                path=scope["path"],
                user_agent=dict(scope["headers"]).get(b"user-agent", b"").decode()
            )
            
            # Process request
            await self.app(scope, receive, send)
            
            # Log response
            duration = time.time() - start_time
            logger.info(
                "http_request_complete",
                method=scope["method"],
                path=scope["path"],
                duration=duration
            )
```

---

**文件用途：** 幫助 Cline 理解 Coach Assistant MVP 系統架構  
**更新頻率：** 架構變更時更新  
**相關文件：** activeContext.md, techContext.md, mvp-v1.md
