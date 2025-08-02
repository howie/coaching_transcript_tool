"""
Cloudflare Workers entry point for Coaching Transcript Tool.
Integrates FastAPI backend with Next.js static frontend.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging
import os

# Import backend modules
from src.coaching_assistant.api import health, format_routes, user
from src.coaching_assistant.middleware.logging import setup_logging
from src.coaching_assistant.middleware.error_handler import error_handler
from src.coaching_assistant.core.config import settings

# 設定日誌
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Coaching Transcript Tool - Full Stack",
    description="Full-stack application on Cloudflare Workers",
    version="2.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# 中間件
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在 CF Workers 上需要更寬鬆的 CORS 設定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 錯誤處理
app.add_exception_handler(Exception, error_handler)

# API 路由
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(format_routes.router, prefix="/api/v1", tags=["format"])
app.include_router(user.router, prefix="/api/v1/user", tags=["user"])

@app.get("/")
async def root():
    """
    API 根端點
    """
    return {"message": "Coaching Transcript Tool API v2.2.0", "status": "running"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Coaching Transcript Tool API on Cloudflare Workers v2.2.0")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Coaching Transcript Tool")

# Cloudflare Workers 相容性
# 當在 CF Workers 環境中運行時，app 會被直接使用
# 本地開發時可以用 uvicorn 運行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
