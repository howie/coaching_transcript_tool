"""
Main entry point for the Coaching Transcript Tool Backend API v2.0.

重構後的 FastAPI 應用，移除了 Flask 依賴，純 FastAPI 架構。
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import text

from .api import (
    debug,
    format_routes,
    health,
)
from .api.v1 import (
    admin,
    admin_reports,
    auth,
    billing_analytics,
    clients,
    coach_profile,
    coaching_sessions,
    plan_limits,
    plans,
    sessions,
    subscriptions,
    summary,
    transcript_smoothing,
    usage,
    usage_history,
    user,
)
from .api.webhooks import ecpay
from .core.config import settings
from .core.env_validator import validate_environment
from .middleware.error_handler import error_handler
from .middleware.logging import setup_api_logging
from .version import DISPLAY_VERSION, VERSION

# 在任何其他初始化之前驗證環境變數
print("🚀 Starting Coaching Transcript Tool Backend API...")
validate_environment()

# 設定日誌
# 在 production/container/CI 環境中，只輸出到 stdout，不寫檔案
is_container = os.getenv("IS_CONTAINER", "false").lower() == "true"
is_production = os.getenv("ENVIRONMENT", "development") == "production"
is_github_actions = os.getenv("GITHUB_ACTIONS", "false").lower() == "true"
is_test_mode = os.getenv("TEST_MODE", "false").lower() == "true"

if is_container or is_production or is_github_actions or is_test_mode:
    # Container/Production/CI: 只輸出到 stdout
    setup_api_logging(log_file=None)
else:
    # Local Development: 輸出到檔案和 stdout
    from pathlib import Path

    api_log_file = Path("logs") / "api.log"
    setup_api_logging(log_file=str(api_log_file))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Coaching Transcript Tool Backend API {DISPLAY_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Suppress SQLAlchemy query logs BEFORE importing engine
    # This must be done before any database operations
    if not settings.SQL_ECHO:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)
        # Also suppress pool and dialect logs
        logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)

    # Validate database connectivity on startup
    from .core.database import engine

    try:
        logger.info("🔌 Testing database connectivity...")
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error("💡 Please ensure PostgreSQL is running:")
        logger.error("   - brew services start postgresql@14")
        logger.error("   - or docker-compose up -d postgres")
        raise RuntimeError(f"Failed to connect to database: {e}") from e

    try:
        yield
    finally:
        logger.info("Shutting down Coaching Transcript Tool Backend API")


app = FastAPI(
    title="Coaching Transcript Tool API",
    description=f"Backend API for processing coaching transcripts - {DISPLAY_VERSION} Unified",
    version=VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
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
app.include_router(
    coach_profile.router, prefix="/api/coach-profile", tags=["coach-profile"]
)
app.include_router(usage_history.router, prefix="/api/v1/usage", tags=["usage-history"])
app.include_router(
    usage.router, prefix="/api/v1/usage-tracking", tags=["usage-tracking"]
)
app.include_router(plans.router, prefix="/api/v1/plans", tags=["plans"])
app.include_router(plan_limits.router, prefix="/api/v1/plan", tags=["plan-limits"])
app.include_router(
    transcript_smoothing.router,
    prefix="/api/v1/transcript",
    tags=["transcript-smoothing"],
)
app.include_router(
    subscriptions.router,
    prefix="/api/v1/subscriptions",
    tags=["subscriptions"],
)
app.include_router(ecpay.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(
    admin_reports.router, prefix="/admin/reports", tags=["admin-reports"]
)
app.include_router(
    billing_analytics.router,
    prefix="/api/v1/billing-analytics",
    tags=["billing-analytics"],
)

# 僅在開發環境中載入偵錯路由
if settings.ENVIRONMENT == "development":
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "coaching_assistant.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=settings.DEBUG,
        log_level="info",
    )
