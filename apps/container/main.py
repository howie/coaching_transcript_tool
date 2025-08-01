
"""
Container deployment entry point for Coaching Assistant.

Uses shared core logic from packages/core-logic.
Container-specific configuration for Docker deployment.
"""
import uvicorn
from coaching_assistant.main import app

if __name__ == "__main__":
    print("🐳 Starting Coaching Assistant in Container mode")
    print("📦 Using shared core logic from packages/core-logic")
    print("🌐 Server running on http://0.0.0.0:8000")
    
    uvicorn.run(
        "coaching_assistant.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
