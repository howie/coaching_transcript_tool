"""
Configuration management for the Coaching Transcript Tool Backend API.

統一的配置管理系統，支援環境變數和設定檔。
"""
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # 基本設定
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "dev-secret-key"
    
    # API 設定
    API_V1_STR: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",      # Next.js dev server
        "http://localhost:8787",      # Cloudflare Workers preview
        "https://yourdomain.com"      # Production domain
    ]
    
    # 資料庫設定
    DATABASE_URL: str = ""
    
    # Google Cloud 設定
    GOOGLE_PROJECT_ID: str = ""
    GOOGLE_STORAGE_BUCKET: str = ""
    
    # 認證設定
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    JWT_SECRET: str = "jwt-secret-key"
    
    # AWS 設定 (向後相容)
    S3_BUCKET_NAME: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = ""
    
    # 監控設定
    SENTRY_DSN: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
