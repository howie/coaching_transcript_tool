"""
Main entry point for the Coaching Transcript Tool Backend API v2.0.

重構後的 FastAPI 應用，移除了 Flask 依賴，純 FastAPI 架構。
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging
import os

from .api import (
    admin,
    admin_reports,
    health,
    format_routes,
    user,
    auth,
    clients,
    coaching_sessions,
    summary,
    coach_profile,
    sessions,
    usage,
    usage_history,
    plans,
    plan_limits,
    transcript_smoothing,
)
from .api.v1 import subscriptions, plans as plans_v1
from .api.webhooks import ecpay
from .middleware.logging import setup_api_logging
from .middleware.error_handler import error_handler
from .core.config import settings
from .core.env_validator import validate_environment
from .version import VERSION, DISPLAY_VERSION, DESCRIPTION

# 在任何其他初始化之前驗證環境變數
print("🚀 Starting Coaching Transcript Tool Backend API...")
validate_environment()

# 設定日誌
# 在 production/container 環境中，只輸出到 stdout，不寫檔案
is_container = os.getenv('IS_CONTAINER', 'false').lower() == 'true'
is_production = os.getenv('ENVIRONMENT', 'development') == 'production'

if is_container or is_production:
    # Container/Production: 只輸出到 stdout
    setup_api_logging(log_file=None)
else:
    # Development: 輸出到檔案和 stdout
    import pathlib
    project_root = pathlib.Path(__file__).parent.parent.parent.parent.parent
    api_log_file = project_root / "logs" / "api.log"
    setup_api_logging(log_file=str(api_log_file))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Coaching Transcript Tool API",
    description=f"Backend API for processing coaching transcripts - {DISPLAY_VERSION} Unified",
    version=VERSION,
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
app.include_router(
    coaching_sessions.router,
    prefix="/api/v1/coaching-sessions",
    tags=["coaching-sessions"],
)
app.include_router(
    sessions.router, prefix="/api/v1/sessions", tags=["transcription-sessions"]
)
app.include_router(summary.router, prefix="/api/v1/dashboard", tags=["summary"])
app.include_router(coach_profile.router, tags=["coach-profile"])
app.include_router(usage.router, tags=["usage"])
app.include_router(usage_history.router, prefix="/api/v1/usage", tags=["usage-history"])
app.include_router(plans.router, tags=["plans"])
app.include_router(plan_limits.router, tags=["plan-limits"])
app.include_router(transcript_smoothing.router, tags=["transcript-smoothing"])
app.include_router(plans_v1.router, tags=["plans-v1"])
app.include_router(subscriptions.router, tags=["subscriptions"])
app.include_router(ecpay.router, tags=["webhooks"])
app.include_router(admin.router, tags=["admin"])
app.include_router(admin_reports.router, tags=["admin-reports"])

# 僅在開發環境中載入偵錯路由
if settings.ENVIRONMENT == "development":
    from .api import debug

    app.include_router(debug.router, prefix="/api/debug", tags=["debug"])


@app.get("/")
async def root():
    """
    API 根端點
    """
    return {
        "message": f"Coaching Transcript Tool API {DISPLAY_VERSION}",
        "status": "running",
    }


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting Coaching Transcript Tool Backend API {DISPLAY_VERSION}")
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
        log_level="info",
    )
