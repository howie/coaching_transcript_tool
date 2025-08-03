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

## 📁 Project Structure

```
coaching_transcript_tool/
├── apps/              # Applications layer
│   ├── api-server/    # FastAPI backend service
│   ├── web/           # Next.js frontend application  
│   ├── cloudflare/    # Cloudflare Workers gateway
│   └── cli/           # Command-line interface
├── packages/          # Shared packages
│   ├── core-logic/    # Core business logic
│   ├── shared-types/  # Shared TypeScript types
│   └── eslint-config/ # Shared ESLint configuration
├── docs/              # Project documentation
├── memory-bank/       # AI assistant's working memory
└── ...
```

## 🐋 Docker Usage

### Docker Compose

For running the API service:

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: apps/api-server/Dockerfile.api
    ports:
      - "8000:8000"
    volumes:
      - ./packages/core-logic/src:/app/src
    environment:
      - PORT=8000
      # Add other environment variables as needed
```

Start the service:
```bash
docker-compose up -d
```

## 💻 Local Usage

The tool is primarily designed to be used as a command-line interface. After installation, you can run it using the `transcript-tool` command.

## 🖥️ Command Line Interface

### Basic Command

```bash
transcript-tool format-command [INPUT_FILE] [OUTPUT_FILE] [OPTIONS]
```

### Getting Help

Show help message and available commands:
```bash
transcript-tool --help
```

Show version:
```bash
transcript-tool --version
```

### Examples

1. **Basic Conversion**
   ```bash
   # Convert VTT to Markdown (default format)
   transcript-tool format-command input.vtt output.md
   
   # Convert VTT to Excel
   transcript-tool format-command input.vtt output.xlsx --format excel
   ```

2. **Speaker Anonymization**
   ```bash
   # Replace specific names with 'Coach' and 'Client'
   transcript-tool format-command input.vtt output.md \
       --coach-name "Dr. Smith" \
       --client-name "Mr. Johnson"
   ```

3. **Chinese Language Support**
   ```bash
   # Convert Simplified Chinese to Traditional Chinese
   transcript-tool format-command input.vtt output.md --traditional
   ```

4. **Combined Options**
   ```bash
   # Multiple options together
   transcript-tool format-command meeting.vtt report.xlsx \
       --format excel \
       --coach-name "Dr. Lee" \
       --client-name "Ms. Chen" \
       --traditional
   ```

### Command Options

| Option | Short | Description | Required | Default |
|--------|-------|-------------|:--------:|:-------:|
| `INPUT_FILE` | - | Path to the input VTT transcript file | ✅ | - |
| `OUTPUT_FILE` | - | Path to save the formatted output file | ✅ | - |
| `--format`, `-f` | `-f` | Output format: `markdown` or `excel` | ❌ | `markdown` |
| `--coach-name` | - | Name of the coach to be replaced with 'Coach' | ❌ | - |
| `--client-name` | - | Name of the client to be replaced with 'Client' | ❌ | - |
| `--traditional` | `-t` | Convert Simplified Chinese to Traditional Chinese | ❌ | `False` |

### Output Formats

- **Markdown (`.md`)**
  - Clean, readable text format
  - Preserves speaker turns and timestamps
  - Easy to edit and version control

- **Excel (`.xlsx`)**
  - Structured tabular format
  - Multiple columns for speaker, timestamp, and content
  - Easy to sort, filter, and analyze

### Environment Variables

#### Backend API Service

When running as a service, you can set these environment variables:

- `PORT`: Port to run the API server on (default: 8000)
- `LOG_LEVEL`: Logging level (default: info)
- `UPLOAD_FOLDER`: Folder to store uploaded files (default: ./data/uploads)

#### Frontend Deployment

The frontend supports different environments with automatic API URL switching:

**Local Development** (`make dev-frontend`):
- Uses `http://localhost:8000` for API calls
- Next.js dev server on `http://localhost:3000`

**Cloudflare Preview** (`make preview-frontend`):
- Uses `http://localhost:8000` for API calls  
- Workers dev server on `http://localhost:8787`

**Production Deployment** (`make deploy-frontend`):
- Uses `https://api.doxa.com.tw` for API calls
- Deployed to Cloudflare Workers

Environment configuration is managed through:
- `apps/web/.env.production` - Production environment variables
- `apps/web/wrangler.toml` - Cloudflare Workers configuration

## 🔧 Development

This project uses `Makefile` to provide unified management for both Python backend and Node.js frontend development.

### Frontend Development (Node.js/Next.js)

- **Install frontend dependencies:**
  ```bash
  make install-frontend
  ```

- **Start development server:**
  ```bash
  make dev-frontend
  # Runs Next.js dev server at http://localhost:3000
  ```

- **Build for production:**
  ```bash
  make build-frontend
  ```

- **Deploy to Cloudflare Workers:**
  ```bash
  make deploy-frontend
  # Builds and deploys to production with https://api.doxa.com.tw
  ```

- **Preview with Cloudflare Workers:**
  ```bash
  make preview-frontend
  # Local preview server at http://localhost:8787 with localhost:8000 API
  ```

- **Build for Cloudflare Workers:**
  ```bash
  make build-frontend-cf
  # Builds both Next.js and OpenNext for Cloudflare Workers
  ```

### Backend Development (Python)

- **Install backend dependencies:**
  ```bash
  make dev-setup
  # Or install directly: pip install -e .[dev]
  ```

- **Start API server:**
  ```bash
  make run-api
  # Runs FastAPI server at http://localhost:8000
  ```

- **Run tests:**
  ```bash
  make test
  # Or run specific test: pytest tests/test_processor.py -v
  ```

### Full-stack Development

- **Install all dependencies:**
  ```bash
  make install-all
  ```

- **Build all services:**
  ```bash
  make build-all
  ```

- **Development workflow:**
  ```bash
  # Terminal 1: Start backend
  make run-api
  
  # Terminal 2: Start frontend  
  make dev-frontend
  ```

### Docker Commands

- **Build Docker images:**
  ```bash
  make docker        # Build both API and CLI images
  make docker-api    # Build API image only
  make docker-cli    # Build CLI image only
  ```

- **Run CLI container:**
  ```bash
  make docker-run-cli INPUT=./input.vtt OUTPUT=./output.md
  ```

- **Run API service:**
  ```bash
  docker-compose up -d
  docker-compose logs -f  # View logs
  ```

### Available Make Commands

For a complete list of available commands, run:
```bash
make help
```

This will show all backend, frontend, full-stack, and Docker commands with descriptions.
