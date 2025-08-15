"""
Debugging and diagnostic routes for development environments.
"""
from fastapi import APIRouter, HTTPException
from ..core.config import settings

router = APIRouter()

def mask_secret(secret: str, unmasked_chars: int = 4) -> str:
    """Masks a secret string, showing only the last few characters."""
    if not secret or len(secret) <= unmasked_chars:
        return "******"
    return f"{'*' * (len(secret) - unmasked_chars)}{secret[-unmasked_chars:]}"

@router.get("/settings")
async def get_debug_settings():
    """
    Returns a selection of current settings for debugging purposes.
    This endpoint should only be active in development environments.
    """
    if settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=404, detail="Not Found")

    return {
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "database_url": settings.DATABASE_URL,
        "allowed_origins": settings.ALLOWED_ORIGINS,
        "google_client_id": settings.GOOGLE_CLIENT_ID,
        "google_client_secret": mask_secret(settings.GOOGLE_CLIENT_SECRET),
        "audio_storage_bucket": settings.AUDIO_STORAGE_BUCKET,
        "transcript_storage_bucket": settings.TRANSCRIPT_STORAGE_BUCKET,
    }
