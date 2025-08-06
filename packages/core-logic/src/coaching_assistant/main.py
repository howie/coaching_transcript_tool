"""
Main entry point for the Coaching Transcript Tool Backend API v2.0.

重構後的 FastAPI 應用，移除了 Flask 依賴，純 FastAPI 架構。
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging
import os

from .api import health, format_routes, user, auth, clients, coaching_sessions, summary
from .middleware.logging import setup_logging
from .middleware.error_handler import error_handler
from .core.config import settings

# 設定日誌
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Coaching Transcript Tool API",
    description="Backend API for processing coaching transcripts - v2.3.0 Unified",
    version="2.3.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# 中間件
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 錯誤處理
app.add_exception_handler(Exception, error_handler)

# 路由
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(format_routes.router, prefix="/api/v1", tags=["format"])
app.include_router(user.router, prefix="/api/v1/user", tags=["user"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(clients.router, prefix="/api/v1/clients", tags=["clients"])
app.include_router(coaching_sessions.router, prefix="/api/v1/sessions", tags=["coaching-sessions"])
app.include_router(summary.router, prefix="/api/v1/dashboard", tags=["summary"])

# 僅在開發環境中載入偵錯路由
if settings.ENVIRONMENT == "development":
    from .api import debug
    app.include_router(debug.router, prefix="/api/debug", tags=["debug"])

@app.get("/")
async def root():
    """
    API 根端點
    """
    return {"message": "Coaching Transcript Tool API v2.3.0", "status": "running"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Coaching Transcript Tool Backend API v2.3.0")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Coaching Transcript Tool Backend API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "coaching_assistant.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=settings.DEBUG,
        log_level="info"
    )
