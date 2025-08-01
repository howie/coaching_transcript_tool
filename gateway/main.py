"""
Cloudflare Workers entry point for Coaching Transcript Tool.
Integrates FastAPI backend with Next.js static frontend.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import os
from pathlib import Path

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

# 靜態文件服務 (Next.js 前端)
static_path = Path("./static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_frontend():
    """
    服務 Next.js 前端首頁
    """
    index_file = static_path / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    else:
        return {"message": "Coaching Transcript Tool API v2.2.0", "status": "running"}

@app.get("/{path:path}")
async def serve_frontend_routes(path: str):
    """
    處理前端路由，支援 Next.js 的客戶端路由
    """
    # 首先檢查是否為 API 路由
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # 檢查是否為靜態資源
    file_path = static_path / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    
    # 檢查是否為目錄下的 index.html
    index_path = static_path / path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    
    # 預設返回根目錄的 index.html (支援 SPA 路由)
    root_index = static_path / "index.html"
    if root_index.exists():
        return FileResponse(root_index)
    
    # 如果都找不到，返回 404
    raise HTTPException(status_code=404, detail="Page not found")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Coaching Transcript Tool on Cloudflare Workers v2.2.0")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
    logger.info(f"Static files directory: {static_path}")

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
