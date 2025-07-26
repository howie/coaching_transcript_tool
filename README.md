# Coaching Transcript Tool

A command-line tool to process and format coaching transcript files (VTT) into structured Markdown or Excel documents.

## ✨ Features

- **Format Conversion**: Convert VTT files to either Markdown (`.md`) or Excel (`.xlsx`).
- **Speaker Anonymization**: Replace the names of the coach and client with 'Coach' and 'Client' for privacy.
- **Chinese Language Support**: Convert transcript text from Simplified Chinese to Traditional Chinese.

## Prerequisites

- Python 3.8 or higher

## 🚀 Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/howie/coaching_transcript_tool.git
    cd coaching_transcript_tool
    ```

2.  **Create and activate a virtual environment using `venv`:**
    ```bash
    # Create the virtual environment
    python3 -m venv venv

    # Activate the environment
    source venv/bin/activate
    # On Windows, use: .\venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -e .[dev]
    ```
    This will install the tool in editable mode along with development dependencies.

## 🐋 Docker Usage

### Quick Start with Docker

1. **Build the Docker image**:
   ```bash
   make docker
   ```

2. **Run a conversion**:
   ```bash
   # Convert VTT to Markdown
   make docker-run INPUT=./input.vtt OUTPUT=./output.md
   
   # Convert VTT to Excel
   make docker-run INPUT=./input.vtt OUTPUT=./output.xlsx FORMAT=excel
   
   # With additional options
   make docker-run INPUT=./input.vtt OUTPUT=./output.md COACH="John Doe" CLIENT="Jane Smith" TRADITIONAL=true
   ```

### Docker Compose

For running the API service:

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - PORT=8000
      # Add other environment variables as needed
```

Start the service:
```bash
docker-compose up -d
```

## 💻 Local Usage

The tool can also be run directly from the command line using `transcript-tool`.

### Basic Command

```bash
transcript-tool format-command [INPUT_FILE] [OUTPUT_FILE] [OPTIONS]
```

### Examples

1.  **Convert a VTT file to Markdown:**
    ```bash
    transcript-tool format-command input.vtt output.md
    ```

2.  **Convert to Excel and anonymize speakers:**
    ```bash
    transcript-tool format-command transcript.vtt formatted.xlsx --format excel --coach-name "John Doe" --client-name "Jane Smith"
    ```

3.  **Convert to Markdown with Traditional Chinese:**
    ```bash
    transcript-tool format-command simplified_chinese.vtt traditional_chinese.md --traditional
    ```

### Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `input_file` | Path to the input VTT transcript file (required) | `input.vtt` |
| `output_file` | Path to save the formatted output file (required) | `output.md` or `output.xlsx` |
| `--format` | Output format: `markdown` (default) or `excel` | `--format excel` |
| `--coach-name` | Name of the coach to be replaced with 'Coach' | `--coach-name "John Doe"` |
| `--client-name` | Name of the client to be replaced with 'Client' | `--client-name "Jane Smith"` |
| `--traditional` | Convert Simplified Chinese to Traditional Chinese | `--traditional` |

### Environment Variables

When running as a service, you can set these environment variables:

- `PORT`: Port to run the API server on (default: 8000)
- `LOG_LEVEL`: Logging level (default: info)
- `UPLOAD_FOLDER`: Folder to store uploaded files (default: ./data/uploads)

## 🔧 Development

This project uses `Makefile` to streamline common development tasks.

- **Install for development:**
  ```bash
  # Install development dependencies
  make dev-setup
  
  # Or install directly
  pip install -e .[dev]
  ```

- **Run tests:**
  ```bash
  # Run all tests
  make test
  
  # Run specific test
  pytest tests/test_processor.py -v
  
  # Run with coverage
  pytest --cov=src tests/
  ```

- **Docker Commands:**
  ```bash
  # Build Docker image
  make docker
  
  # Run container with volume mapping
  make docker-run INPUT=./input.vtt OUTPUT=./output.md
  
  # Run API service
  docker-compose up -d
  
  # View logs
  docker-compose logs -f
  ```

For a full list of commands, run `make help`.