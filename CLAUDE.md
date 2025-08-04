# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend Development (Python)
- **Install dependencies**: `make dev-setup` or `pip install -e packages/core-logic --break-system-packages`
- **Run API server**: `make run-api` (starts FastAPI at http://localhost:8000)
- **Run tests**: `make test` or `pytest packages/core-logic/tests/`
- **Run linting**: `make lint` (runs flake8 on core-logic)
- **Run single test**: `pytest packages/core-logic/tests/test_processor.py::test_specific_function -v`

### Frontend Development (Next.js)
- **Install dependencies**: `make install-frontend` or `cd apps/web && npm install`
- **Run dev server**: `make dev-frontend` (starts Next.js at http://localhost:3000)
- **Build frontend**: `make build-frontend`
- **Deploy to Cloudflare**: `make deploy-frontend`
- **Run tests**: `cd apps/web && npm test`
- **Run linting**: `cd apps/web && npm run lint`

### Docker Operations
- **Build Docker images**: `make docker` (builds both API and CLI images)
- **Run CLI container**: `make docker-run-cli INPUT=./input.vtt OUTPUT=./output.md`
- **Run API service**: `docker-compose up -d`

## Architecture Overview

This is a monorepo project using Python (FastAPI) for backend and Next.js for frontend, designed for serverless deployment.

### Key Components

1. **apps/web/** - Next.js frontend application
   - Deployed to Cloudflare Workers using OpenNext
   - Uses Tailwind CSS, React Hook Form, and Zustand for state management
   - API client configured to use different endpoints based on environment

2. **apps/api-server/** - FastAPI backend service
   - Core transcript processing logic
   - Handles VTT to Markdown/Excel conversion
   - Supports Chinese language conversion (Simplified to Traditional)

3. **apps/cli/** - Command-line interface
   - Standalone tool for transcript processing
   - Uses the same core logic as API

4. **packages/core-logic/** - Shared Python business logic
   - VTT parser and processors
   - Excel and Markdown exporters
   - Chinese converter utilities

### API Environment Configuration
- **Local Development**: API runs on `http://localhost:8000`
- **Production**: API deployed to `https://api.doxa.com.tw`
- Environment detection is automatic based on build/runtime context

### File Processing Flow
1. User uploads VTT file through web interface
2. Frontend validates file and sends to API
3. API parses VTT content and applies transformations
4. Processed content returned as Markdown or Excel format
5. Frontend allows user to download the result

### Testing Strategy
- Backend: pytest with test data in `packages/core-logic/tests/data/`
- Frontend: Jest with Testing Library
- Always verify test framework before running tests

### Important Notes
- The project uses `--break-system-packages` for pip installs due to Python environment setup
- Makefile provides unified interface for all common operations
- Memory bank files in `memory-bank/` contain detailed context about the project
- CORS is enabled in production for cross-origin API requests