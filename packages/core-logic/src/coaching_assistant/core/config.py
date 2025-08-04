"""
Configuration management for the Coaching Transcript Tool Backend API.

統一的配置管理系統，支援環境變數和設定檔。
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
import os

class Settings(BaseSettings):
    # 基本設定
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "dev-secret-key"
    
    # API 設定
    API_V1_STR: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",      # Next.js dev server
        "http://localhost:8787",      # Cloudflare Workers preview
        "https://coachly-doxa-com-tw.howie-yu.workers.dev", # Cloudflare Workers production
        "https://coachly.doxa.com.tw" # Production frontend domain
    ]
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            # 處理逗號分隔的字串
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # 資料庫設定
    DATABASE_URL: str = ""
    
    # JWT 認證設定
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Google Cloud 設定
    GOOGLE_PROJECT_ID: str = ""
    GOOGLE_STORAGE_BUCKET: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_APPLICATION_CREDENTIALS_JSON: str = ""  # JSON 格式的服務帳號憑證
    
    # 檔案上傳限制
    MAX_FILE_SIZE: int = 500  # MB
    MAX_AUDIO_DURATION: int = 3600  # seconds (1 hour)
    
    # 日誌設定
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "text"
    
    # AWS 設定 (向後相容)
    S3_BUCKET_NAME: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = ""
    
    # Redis/Celery 設定 (可選)
    REDIS_URL: str = ""
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    
    # 監控設定
    SENTRY_DSN: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
