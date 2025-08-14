# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Coaching Assistant Platform** - A comprehensive SaaS solution for ICF coaches to transcribe, analyze, and manage coaching sessions.

### Core Purpose
Transform audio recordings of coaching sessions into high-quality transcripts with speaker diarization, supporting future AI-powered coaching assessment and supervision features.

### Technology Stack
- **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind CSS
- **Backend**: FastAPI (Python 3.11+) 
- **Deployment**: Cloudflare Workers (Frontend) + Render.com (Backend)
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Task Queue**: Celery + Redis
- **STT Provider**: Google Speech-to-Text v2

## Quick Start

```bash
# Install all dependencies
make dev-setup && make install-frontend

# Start development servers
make run-api        # Backend at http://localhost:8000
make dev-frontend   # Frontend at http://localhost:3000

# Run tests
make test          # Backend tests
cd apps/web && npm test  # Frontend tests
```

## Key Development Commands

### Backend (Python/FastAPI)
- `make dev-setup` - Install Python dependencies
- `make run-api` - Start API server
- `make test` - Run pytest suite
- `make lint` - Run code linting

### Frontend (Next.js)
- `make install-frontend` - Install npm dependencies  
- `make dev-frontend` - Start dev server
- `make build-frontend` - Production build
- `make deploy-frontend` - Deploy to Cloudflare

### Docker
- `make docker` - Build all images
- `docker-compose up -d` - Run services

## Project Structure

```
coaching_transcript_tool/
├── apps/              
│   ├── api-server/    # FastAPI backend service
│   ├── cli/           # Command-line tool
│   └── web/           # Next.js frontend
├── packages/          
│   └── core-logic/    # Shared Python business logic
└── docs/              # Project documentation
```

## Architecture Decisions

The project follows a **monorepo architecture** with clear separation of concerns:

1. **Frontend-Backend Separation**: Complete decoupling for independent scaling and deployment
2. **Microservices Ready**: Each app can be deployed independently
3. **Code Reuse**: Shared business logic in packages/core-logic
4. **Serverless First**: Optimized for edge deployment on Cloudflare Workers

## API Endpoints

Key endpoints:
- `POST /auth/google` - Google SSO authentication
- `POST /sessions` - Create transcription session (supports `stt_provider` selection)
- `GET /sessions` - List user sessions
- `GET /sessions/{id}` - Get session details
- `GET /sessions/providers` - Get available STT providers (NEW)
- `POST /sessions/{id}/upload-url` - Get signed upload URL (supports FAILED sessions for re-upload)
- `POST /sessions/{id}/start-transcription` - Start transcription processing
- `POST /sessions/{id}/retry-transcription` - Retry failed transcription sessions (NEW)
- `GET /sessions/{id}/transcript` - Download transcript (VTT/SRT/JSON/XLSX)
- `GET /sessions/{id}/status` - Get transcription progress
- `PATCH /sessions/{id}/speaker-roles` - Update speaker role assignments
- `PATCH /sessions/{id}/segment-roles` - Update individual segment speaker roles

## Important Notes

- Use virtual environments for Python development (avoid `--break-system-packages`)
- **Environment variables required**: `DATABASE_URL`, `REDIS_URL`, `GOOGLE_APPLICATION_CREDENTIALS_JSON`
- **AssemblyAI integration**: Set `ASSEMBLYAI_API_KEY` to enable AssemblyAI provider
- Audio files auto-delete after 24 hours (GDPR compliance)
- Makefile provides unified interface for all operations
- **Database migration applied**: STT provider tracking in `session` table
- **Multi-provider support**: Seamless switching between Google STT and AssemblyAI

## Testing Philosophy

- Write tests for critical business logic
- Use pytest for backend, Jest for frontend
- Mock external services in tests
- Maintain >70% coverage for core-logic package

## Deployment

- **Frontend**: Auto-deploy to Cloudflare on main branch push
- **Backend**: Deploy to Render via GitHub Actions
- **Database**: Managed PostgreSQL on Render
- **Monitoring**: Render Metrics + custom logging

## STT Provider Architecture & Transcription

### Overview
The system supports **multiple STT providers** with intelligent fallback mechanisms and automatic speaker diarization across different languages and configurations.

### ✅ Supported STT Providers (August 2025)
1. **Google Speech-to-Text** (Default)
2. **AssemblyAI** - New provider with enhanced features

### Provider Selection
Users can choose STT provider per session:
- **API**: `POST /sessions` with `stt_provider: "google"|"assemblyai"|"auto"`
- **Environment**: `STT_PROVIDER=google` or `STT_PROVIDER=assemblyai`
- **Fallback**: Automatic failover from AssemblyAI to Google STT on errors

### Configuration
Key environment variables for transcription:

```env
# STT Provider Selection
STT_PROVIDER=google  # "google" (default) | "assemblyai"

# Google STT Configuration
GOOGLE_STT_MODEL=chirp_2
GOOGLE_STT_LOCATION=asia-southeast1

# AssemblyAI Configuration (NEW)
ASSEMBLYAI_API_KEY=your_api_key_here
ASSEMBLYAI_MODEL=best  # "best" or "nano"
ASSEMBLYAI_SPEAKERS_EXPECTED=2

# Speaker Diarization Settings
ENABLE_SPEAKER_DIARIZATION=true
MAX_SPEAKERS=2
MIN_SPEAKERS=2
```

### Google STT API Methods
The system intelligently chooses between two Google STT v2 APIs:

1. **recognize API**: Used when diarization is supported (limited language/region combinations)
2. **batchRecognize API**: Used as fallback when diarization is not supported

### AssemblyAI Features
- **Automatic Speaker Diarization**: Built-in support without configuration
- **Chinese Language Processing**: Traditional Chinese conversion with space removal
- **Speaker Role Assignment**: Automatic coach/client role detection using heuristics
- **Real-time Progress**: Async transcription with polling and progress callbacks

### Language Support Matrix

| Language | Region | Model | Diarization Support | API Used |
|----------|--------|--------|-------------------|----------|
| English (en-US) | us-central1 | chirp_2 | ✅ Supported | recognize |
| English (en-US) | asia-southeast1 | chirp_2 | ❌ Auto-fallback | batchRecognize |
| Chinese (cmn-Hant-TW) | asia-southeast1 | chirp_2 | ❌ Auto-fallback | batchRecognize |
| Japanese (ja) | asia-southeast1 | chirp_2 | ❌ Auto-fallback | batchRecognize |

### Manual Role Assignment
When automatic diarization is not available, the frontend provides:
- **Segment-level editing**: Each transcript segment can be individually assigned to "Coach" or "Client"
- **Real-time updates**: Statistics update immediately after role assignment changes
- **Export support**: All export formats (JSON/VTT/SRT/TXT) include role information

### Best Practices
- **For English sessions**: Use `GOOGLE_STT_LOCATION=us-central1` for optimal diarization
- **For Chinese/Asian languages**: Current `asia-southeast1` setting provides excellent transcription with manual role assignment
- **Mixed language support**: System automatically detects and uses the best configuration per language

For detailed documentation, see `/docs/` directory.

## AssemblyAI Provider Integration (August 2025)

### ✅ Implementation Status: COMPLETED
The AssemblyAI provider is fully integrated and production-ready with comprehensive features:

### Core Features
- **Multi-Provider Support**: Users can choose between Google STT and AssemblyAI per session
- **Automatic Fallback**: System falls back from AssemblyAI to Google STT on failures
- **Chinese Language Processing**: Traditional Chinese conversion with proper spacing
- **Speaker Intelligence**: Automatic coach/client role assignment using analysis heuristics
- **Real-time Progress**: Async transcription with detailed progress callbacks

### Technical Implementation
- **Provider Interface**: `AssemblyAIProvider` class in `services/assemblyai_stt.py`
- **Factory Pattern**: `STTProviderFactory` with fallback support in `services/stt_factory.py`
- **Speaker Analysis**: `SpeakerAnalyzer` utility in `utils/speaker_analysis.py`
- **Database Migration**: Added `stt_provider` and `provider_metadata` fields to session table
- **API Enhancement**: New `/providers` endpoint and provider selection in session creation

### Usage Examples
```python
# Create session with specific provider
POST /sessions
{
  "title": "Coaching Session",
  "language": "cmn-Hant-TW",
  "stt_provider": "assemblyai"  # "google", "assemblyai", or "auto"
}

# Get available providers
GET /sessions/providers
# Returns: {"available_providers": [...], "default_provider": "google"}
```

### Chinese Language Processing
- **Input**: Simplified Chinese from AssemblyAI API
- **Processing**: Remove spaces + Convert to Traditional Chinese using OpenCC
- **Output**: Properly formatted Traditional Chinese matching Google STT format

### Provider Selection Logic
1. **Per-Session**: API clients can specify `stt_provider` in session creation
2. **Environment Default**: `STT_PROVIDER` environment variable sets system default
3. **Auto Fallback**: If primary provider fails, automatically tries fallback provider
4. **Provider Tracking**: All sessions track which provider was actually used

### Files Modified/Created
- **NEW**: `packages/core-logic/src/coaching_assistant/services/assemblyai_stt.py`
- **NEW**: `packages/core-logic/src/coaching_assistant/utils/speaker_analysis.py`
- **NEW**: `packages/core-logic/alembic/versions/49515d3a1515_add_stt_provider_tracking_fields.py`
- **MODIFIED**: `packages/core-logic/src/coaching_assistant/services/stt_factory.py`
- **MODIFIED**: `packages/core-logic/src/coaching_assistant/models/session.py`
- **MODIFIED**: `packages/core-logic/src/coaching_assistant/core/config.py`
- **MODIFIED**: `packages/core-logic/src/coaching_assistant/tasks/transcription_tasks.py`
- **MODIFIED**: `packages/core-logic/src/coaching_assistant/api/sessions.py`

### Testing & Verification
- ✅ Unit tests for AssemblyAI provider
- ✅ Integration tests for provider factory and fallback
- ✅ Database migration applied and tested
- ✅ API endpoints verified with authentication
- ✅ CORS configuration confirmed for frontend integration
- ✅ Provider switching and fallback mechanism validated

### Configuration Reference
```env
# Provider Selection
STT_PROVIDER=assemblyai  # or "google" (default)

# AssemblyAI Settings
ASSEMBLYAI_API_KEY=your_api_key_here
ASSEMBLYAI_MODEL=best  # or "nano" for faster/cheaper
ASSEMBLYAI_SPEAKERS_EXPECTED=2
```

### Error Handling & Recovery (NEW - August 2025)
- **Failed Session Recovery**: Added `/retry-transcription` endpoint for failed sessions
- **Automatic Re-upload Support**: Failed sessions can request new upload URLs
- **Clean State Reset**: Retry clears previous transcript segments and processing status
- **File Verification**: Checks audio file existence before retry attempt
- **Graceful Degradation**: If audio file missing, resets session to allow re-upload

### Session Status Management
- **FAILED → PROCESSING**: Retry transcription with existing audio file
- **FAILED → UPLOADING**: If audio file missing, reset to allow new upload
- **Comprehensive Cleanup**: Clears transcript segments, processing status, and error messages

### Next Steps & Production Readiness
- 🚀 **Ready for Production**: Full implementation with comprehensive error handling
- ✅ **Error Recovery**: Complete retry mechanism for failed transcriptions
- 📊 **Monitor Usage**: Track provider performance and costs in production
- 🔄 **Provider Analytics**: Consider adding provider comparison metrics
- 🎯 **Future Enhancement**: Support for multiple speakers (group coaching)