
"""
Container deployment entry point for Coaching Assistant.

Uses shared core logic from packages/core-logic.
Container-specific configuration for Docker deployment.
"""
import os
import uvicorn
from coaching_assistant.main import app

# 直接暴露 app 實例，讓 Render 可以使用 main:app 啟動
__all__ = ["app"]

if __name__ == "__main__":
    print("🐳 Starting Coaching Assistant in Container mode")
    print("📦 Using shared core logic from packages/core-logic")
    
    # 從環境變數讀取 PORT，預設為 8000
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("API_HOST", "0.0.0.0")
    
    print(f"🌐 Server running on http://{host}:{port}")
    
    uvicorn.run(
        "coaching_assistant.main:app",
        host=host,
        port=port,
        reload=os.environ.get("ENVIRONMENT", "development") == "development",
        log_level=os.environ.get("LOG_LEVEL", "info").lower()
    )
