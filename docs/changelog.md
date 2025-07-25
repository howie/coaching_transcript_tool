# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-07-25

### Added
- **FastAPI Service**: Introduced a new API service based on FastAPI to provide transcript formatting functionalities over HTTP.
- **Core Logic Module**: Created a dedicated `coaching_assistant.core` module to encapsulate all business logic, making it reusable and testable.
- **API Endpoint**: Implemented a `POST /format` endpoint that accepts VTT file uploads and returns formatted files in either Markdown or Excel format.
- **Excel Export**: Added functionality to export transcripts to a styled `.xlsx` file, with alternating colors for speakers.
- **Configuration**: Added `pyproject.toml` dependencies for the API, including `fastapi`, `uvicorn`, and `python-multipart`.
- **Containerization**: Included `Dockerfile.api` and `docker-compose.yml` for easy local development and future deployment.
- **Documentation**: Added `docs/roadmap.md` and `docs/todo.md` to track project progress.

### Changed
- **Project Structure**: Refactored the project from a single CLI script into a modular service-oriented architecture.
- **VTT Parser**: Modified `parser.py` to accept file content as a string directly, instead of a file path, to better integrate with the API.
- **Excel Exporter**: Reworked `exporters/excel.py` to return an in-memory `BytesIO` object instead of writing to a file, which is crucial for sending file responses via the API. The function was also refactored to improve code quality.

### Removed
- **CLI Script**: Deleted the original `src/vtt.py` CLI script, as its functionality is now provided by the API service.
