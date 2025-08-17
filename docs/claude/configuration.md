# Configuration Guide

## Environment Variables

### Core Database Configuration
```env
# PostgreSQL connection (required)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis for Celery task queue (required)
REDIS_URL=redis://localhost:6379/0
```

### Authentication
```env
# Google Service Account for GCS and STT (required)
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type": "service_account", "project_id": "...", ...}

# Google OAuth for user authentication
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Session security
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
```

### STT Provider Configuration

#### Google Speech-to-Text (Default)
```env
# Provider selection
STT_PROVIDER=google  # Default provider

# Model configuration
GOOGLE_STT_MODEL=chirp_2  # Latest model with best accuracy
GOOGLE_STT_LOCATION=asia-southeast1  # Regional endpoint

# Language-specific regions (optional overrides)
GOOGLE_STT_LOCATION_EN=us-central1  # Better English diarization
GOOGLE_STT_LOCATION_ZH=asia-southeast1  # Chinese support
GOOGLE_STT_LOCATION_JA=asia-northeast1  # Japanese support
```

#### AssemblyAI Provider
```env
# Enable AssemblyAI
STT_PROVIDER=assemblyai  # Or set per-session

# API Key (required when using AssemblyAI)
ASSEMBLYAI_API_KEY=your-api-key-here

# Optional configuration
ASSEMBLYAI_WEBHOOK_URL=https://your-domain.com/webhooks/assemblyai
ASSEMBLYAI_TIMEOUT=3600  # Max processing time in seconds
```

### Storage Configuration
```env
# Google Cloud Storage
GCS_BUCKET_NAME=your-bucket-name
GCS_PROJECT_ID=your-project-id

# File retention
AUDIO_RETENTION_HOURS=24  # GDPR compliance, auto-delete after 24h
MAX_UPLOAD_SIZE_MB=500  # Maximum file size
```

### Application Settings
```env
# Environment
ENVIRONMENT=development  # development | staging | production

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,https://your-domain.com

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600  # seconds

# Feature Flags
ENABLE_ASSEMBLYAI=true
ENABLE_SPEAKER_DIARIZATION=true
ENABLE_AUTO_LANGUAGE_DETECTION=false
```

### Monitoring & Logging
```env
# Log Level
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR

# Sentry (optional)
SENTRY_DSN=https://xxx@sentry.io/yyy

# OpenTelemetry (optional)
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp.example.com
OTEL_SERVICE_NAME=coaching-assistant
```

## Configuration Classes

### Main Settings Class
```python
from pydantic import BaseSettings, Field, validator
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    
    # STT Configuration
    stt_provider: str = Field("google", env="STT_PROVIDER")
    google_stt_model: str = Field("chirp_2", env="GOOGLE_STT_MODEL")
    google_stt_location: str = Field("asia-southeast1", env="GOOGLE_STT_LOCATION")
    assemblyai_api_key: Optional[str] = Field(None, env="ASSEMBLYAI_API_KEY")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # Environment
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    
    @validator("stt_provider")
    def validate_stt_provider(cls, v):
        if v not in ["google", "assemblyai", "auto"]:
            raise ValueError(f"Invalid STT provider: {v}")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

## Environment-Specific Configurations

### Development (.env.development)
```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://localhost/coaching_dev
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:3000
```

### Staging (.env.staging)
```env
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://staging-db.example.com/coaching
REDIS_URL=redis://staging-redis.example.com:6379/0
CORS_ORIGINS=https://staging.example.com
```

### Production (.env.production)
```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://prod-db.example.com/coaching
REDIS_URL=redis://prod-redis.example.com:6379/0
CORS_ORIGINS=https://app.example.com
SENTRY_DSN=https://xxx@sentry.io/yyy
```

## Configuration Validation

### Startup Validation
```python
def validate_configuration():
    """Validate all required configuration on startup"""
    settings = Settings()
    
    # Check required services
    if settings.stt_provider == "assemblyai" and not settings.assemblyai_api_key:
        raise ValueError("ASSEMBLYAI_API_KEY required when using AssemblyAI")
    
    # Validate database connection
    try:
        engine = create_engine(settings.database_url)
        engine.connect()
    except Exception as e:
        raise ValueError(f"Database connection failed: {e}")
    
    # Validate Redis connection
    try:
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
    except Exception as e:
        raise ValueError(f"Redis connection failed: {e}")
    
    logger.info("✅ Configuration validated successfully")
```

## Security Best Practices

1. **Never commit .env files** - Use .env.example as template
2. **Use strong secret keys** - Generate with `openssl rand -hex 32`
3. **Rotate keys regularly** - Especially API keys and secrets
4. **Use environment-specific credentials** - Separate dev/staging/prod
5. **Encrypt sensitive data** - Use secret management services in production

## Provider Cost Considerations

### Google Speech-to-Text
- **Pricing**: ~$0.016 per minute (chirp_2 model)
- **Free tier**: 60 minutes/month
- **Batch processing**: 50% discount for async batch

### AssemblyAI
- **Pricing**: ~$0.015 per minute
- **Free tier**: None (pay-as-you-go)
- **Features**: Better Chinese support, built-in summarization

## Troubleshooting

### Common Issues

1. **Missing environment variables**
   - Error: `Field required [type=value_error.missing]`
   - Solution: Check .env file and ensure all required vars are set

2. **Invalid Google credentials**
   - Error: `Could not automatically determine credentials`
   - Solution: Verify GOOGLE_APPLICATION_CREDENTIALS_JSON is valid JSON

3. **Database connection failed**
   - Error: `could not connect to server`
   - Solution: Check DATABASE_URL format and network connectivity

4. **Redis connection timeout**
   - Error: `Connection refused`
   - Solution: Ensure Redis is running and REDIS_URL is correct