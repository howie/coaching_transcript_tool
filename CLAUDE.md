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
- `POST /sessions` - Create coaching session
- `POST /sessions/{id}/upload-url` - Get signed upload URL
- `GET /sessions/{id}/transcript` - Download transcript (VTT/SRT/JSON)

## Important Notes

- Use virtual environments for Python development (avoid `--break-system-packages`)
- Environment variables required: `DATABASE_URL`, `REDIS_URL`, `GOOGLE_APPLICATION_CREDENTIALS_JSON`
- Audio files auto-delete after 24 hours (GDPR compliance)
- Makefile provides unified interface for all operations

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

For detailed documentation, see `/docs/` directory.