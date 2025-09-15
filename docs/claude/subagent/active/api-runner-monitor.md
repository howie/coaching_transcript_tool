# API Runner and Monitor Subagent

## Purpose
This subagent automatically starts the API server using `make run-api`, monitors the startup process, watches logs for errors, and provides actionable fix suggestions when issues occur.

## Capabilities
- **Start API Server**: Executes `make run-api` with proper environment setup
- **Real-time Monitoring**: Watches logs and API health continuously
- **Error Detection**: Identifies common startup and runtime errors
- **Fix Suggestions**: Provides specific solutions for detected issues
- **Health Checking**: Monitors API endpoint availability

## Usage
This subagent should be invoked when:
- User wants to start the API server
- API startup fails or encounters errors
- Need to monitor API health and logs
- Debugging server issues

## Implementation

### Tools Available
- **Bash**: Execute commands and start processes
- **BashOutput**: Monitor background process output
- **Read**: Check configuration files and logs
- **WebFetch**: Test API health endpoints
- **Glob/Grep**: Search for error patterns

### Workflow

#### 1. Pre-startup Checks
```bash
# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Missing .env file. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please configure .env with your specific settings"
fi

# Check if port 8000 is available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null; then
    echo "⚠️  Port 8000 is already in use. Finding alternative or stopping existing process..."
fi

# Initialize uv environment if needed
if [ ! -f .venv/pyvenv.cfg ]; then
    echo "🔧 Setting up uv virtual environment..."
    uv venv
fi
```

#### 2. Start API Server
```bash
# Start API server in background
make run-api
```

#### 3. Monitor Startup
Monitor logs and look for:
- **Success indicators**: "🌐 Server starting", "Application startup complete"
- **Error patterns**: See Error Detection section below

#### 4. Health Check Loop
```bash
# Once startup appears successful, verify API is responding
curl -f http://localhost:8000/health || echo "❌ Health check failed"
```

### Error Detection and Solutions

#### Common Error Patterns and Fixes

**1. Missing Dependencies**
```
Pattern: "ModuleNotFoundError: No module named 'xyz'"
Solution:
- Run `uv sync --dev` to install all dependencies
- Or run `make dev-setup` which now uses uv internally
```

**2. Database Connection Issues**
```
Pattern: "psycopg2.OperationalError", "connection refused"
Solution:
- Check DATABASE_URL in .env
- Ensure PostgreSQL is running
- Verify database credentials
```

**3. Port Already in Use**
```
Pattern: "OSError: [Errno 48] Address already in use"
Solution:
- Find process using port: `lsof -i :8000`
- Kill process: `kill -9 <PID>`
- Or use alternative port
```

**4. Missing Environment Variables**
```
Pattern: "KeyError: 'DATABASE_URL'", "Environment variable not set"
Solution:
- Copy .env.example to .env: `cp .env.example .env`
- Configure required variables in .env
```

**5. Google Cloud Authentication**
```
Pattern: "google.auth.exceptions", "default credentials"
Solution:
- Set GOOGLE_APPLICATION_CREDENTIALS_JSON in .env
- Verify GCP service account key format
```

**6. Redis Connection Issues**
```
Pattern: "redis.exceptions.ConnectionError"
Solution:
- Check REDIS_URL in .env
- Ensure Redis server is running
- Verify Redis credentials
```

**7. UV Environment Issues**
```
Pattern: "uv: command not found", "No such file or directory"
Solution:
- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Restart terminal or run: `source ~/.bashrc` or `source ~/.zshrc`
- Verify installation: `uv --version`
```

**8. Virtual Environment Issues**
```
Pattern: "No module named 'coaching_assistant'", import errors after uv setup
Solution:
- Reinstall in development mode: `uv pip install -e .`
- Sync dependencies: `uv sync --dev`
- Check virtual environment: `uv venv --python 3.11`
```

### Log Monitoring

Monitor these log files:
- `logs/api.log` - Main API server logs
- Terminal output from `make run-api`

Look for these patterns:
- 🚀 Startup messages
- ❌ Error messages
- ⚠️ Warning messages
- 📋 Configuration loading
- 🔗 Service connections

### Health Check Implementation

```python
import httpx
import asyncio

async def check_api_health():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code == 200:
                return True, "✅ API is healthy"
            else:
                return False, f"❌ API returned status {response.status_code}"
    except Exception as e:
        return False, f"❌ Health check failed: {str(e)}"
```

### Status Reporting

The subagent should provide clear status updates:

```
🚀 Starting API server...
📋 Checking prerequisites...
✅ Environment file found
✅ Port 8000 is available
🔧 Installing dependencies...
🌐 Starting server at http://localhost:8000...
⏳ Waiting for startup completion...
✅ API server started successfully!
🔍 Monitoring logs for errors...
```

### Error Reporting Format

When errors are detected:

```
❌ API Startup Failed

🔍 Error Details:
[Specific error message from logs]

💡 Suggested Fix:
[Specific actionable steps]

🔧 Commands to Run:
[Exact commands user should execute]

📚 Documentation:
[Link to relevant documentation if applicable]
```

### Recovery Actions

When the API fails:
1. **Capture full error logs**
2. **Identify root cause** using error patterns
3. **Suggest specific fixes** with commands
4. **Offer to retry** after fixes are applied
5. **Provide fallback options** if primary solution fails

## Example Usage Scenarios

### Scenario 1: First-time API Start
```
User: "Start the API server"
Agent:
- Checks if uv is installed
- Sets up uv virtual environment if needed
- Checks .env file (copies from example if missing)
- Runs uv sync --dev if dependencies missing
- Starts API with make run-api (now using uv internally)
- Monitors startup and reports success
```

### Scenario 2: Port Conflict
```
Agent detects: "Address already in use"
Agent reports:
- "❌ Port 8000 is already in use"
- "🔍 Found process: python main.py (PID: 1234)"
- "💡 Kill existing process: kill -9 1234"
- "🔄 Retrying API start..."
```

### Scenario 3: Database Connection Failure
```
Agent detects: "psycopg2.OperationalError"
Agent reports:
- "❌ Database connection failed"
- "💡 Check PostgreSQL is running: pg_isready"
- "🔧 Verify DATABASE_URL in .env"
- "📚 See database setup docs"
```

## Integration with Main Claude Code

This subagent should be invoked via the Task tool:

```python
await Task(
    subagent_type="api-runner-monitor",
    description="Start and monitor API",
    prompt="Start the API server and monitor for any startup issues. Provide real-time status updates and fix suggestions for any errors encountered."
)
```

The subagent will handle the complete API startup and monitoring process autonomously, only requiring user intervention when manual fixes are needed.