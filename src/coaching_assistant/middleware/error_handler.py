"""
Error handling middleware for the Coaching Transcript Tool Backend API.
"""

import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    全域錯誤處理器。
    """
    if isinstance(exc, HTTPException):
        logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "status_code": exc.status_code},
        )

    if isinstance(exc, StarletteHTTPException):
        logger.warning(f"Starlette HTTP Exception: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "status_code": exc.status_code},
        )

    # 記錄未預期的錯誤
    logger.exception(f"Unexpected error occurred: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "detail": str(exc) if logger.isEnabledFor(logging.DEBUG) else None,
        },
    )
