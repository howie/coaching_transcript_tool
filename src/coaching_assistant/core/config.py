"""
Configuration management for the Coaching Transcript Tool Backend API.

統一的配置管理系統，支援環境變數和設定檔。
"""

import json
import os
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 基本設定
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "dev-secret-key"

    # SQL/Database debugging
    SQL_ECHO: bool = False  # Controls SQLAlchemy SQL statement logging

    # 測試模式設定 - 允許在不需要認證的情況下測試所有 API
    # ⚠️ 警告：此模式僅適用於開發和測試環境，絕不可在生產環境中啟用
    TEST_MODE: bool = False

    # API 設定
    API_V1_STR: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:8787",  # Cloudflare Workers preview
        "https://coachly-doxa-com-tw.howie-yu.workers.dev",  # Cloudflare Workers production  # noqa: E501
        "https://coachly.doxa.com.tw",  # Production frontend domain
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            raw_value = v.strip()

            if not raw_value:
                return []

            # Try to parse JSON formatted strings first
            try:
                parsed_json = json.loads(raw_value)
            except json.JSONDecodeError:
                parsed_json = None

            if isinstance(parsed_json, list):
                return [
                    str(origin).strip() for origin in parsed_json if str(origin).strip()
                ]
            if isinstance(parsed_json, str):
                return [parsed_json.strip()]

            # Support quoted single origin strings ("origin")
            if (raw_value.startswith('"') and raw_value.endswith('"')) or (
                raw_value.startswith("'") and raw_value.endswith("'")
            ):
                inner_value = raw_value[1:-1].strip()
                return [inner_value] if inner_value else []

            # 處理以逗號分隔的字串
            return [origin.strip() for origin in raw_value.split(",") if origin.strip()]

        return v

    # 資料庫設定
    DATABASE_URL: str = ""

    # JWT 認證設定
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google Cloud 設定
    GOOGLE_PROJECT_ID: str = ""
    GCP_REGION: str = "asia-southeast1"  # Default GCP region
    AUDIO_STORAGE_BUCKET: str = ""  # Used for both audio files and batch results
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_APPLICATION_CREDENTIALS_JSON: str = ""  # JSON 格式的服務帳號憑證

    # 向後相容性 - 將在未來版本移除
    GOOGLE_STORAGE_BUCKET: str = ""

    # Google reCAPTCHA 設定
    RECAPTCHA_ENABLED: bool = True  # Enable/disable reCAPTCHA verification
    RECAPTCHA_SITE_KEY: str = ""  # Frontend site key (not used in backend)
    RECAPTCHA_SECRET: str = os.getenv(
        "RECAPTCHA_SECRET", "6LeIxAcTAAAAABKJdbdotzKATjbpe4U93716OSsz"
    )  # Test secret key for development
    RECAPTCHA_MIN_SCORE: float = 0.5  # Minimum score to pass verification (0.0-1.0)

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

    # STT (Speech-to-Text) 設定
    STT_PROVIDER: str  # 必須設定，避免預設值 silently fallback
    SPEECH_API_VERSION: str = "v2"  # Google Speech-to-Text API version
    GOOGLE_STT_MODEL: str = "chirp_2"  # Default model (chirp supports more languages)
    GOOGLE_STT_LOCATION: str = "asia-southeast1"  # Default location for STT

    # AssemblyAI 設定
    ASSEMBLYAI_API_KEY: str = ""
    ASSEMBLYAI_MODEL: str = "best"  # "best" or "nano"
    ASSEMBLYAI_SPEAKERS_EXPECTED: int = 2  # Number of speakers expected for diarization
    ASSEMBLYAI_WEBHOOK_URL: str = ""  # Optional webhook URL for notifications

    # LeMUR (Large Language Model) 設定
    LEMUR_MODEL: str = "claude_sonnet_4_20250514"  # Claude 4 Sonnet as default
    LEMUR_FALLBACK_MODEL: str = "claude3_5_sonnet"  # Fallback to Claude 3.5 Sonnet
    LEMUR_MAX_OUTPUT_SIZE: int = 4000  # Maximum output size for LeMUR responses
    LEMUR_COMBINED_MODE: bool = True  # Enable combined speaker + punctuation processing
    LEMUR_PROMPTS_PATH: str = ""  # Custom path to prompts YAML file (optional)

    # Language-specific STT configurations (JSON format)
    # Example: {"zh-TW": {"location": "asia-southeast1", "model": "latest_long"}}
    STT_LANGUAGE_CONFIGS: str = ""

    # Speaker Diarization 設定
    ENABLE_SPEAKER_DIARIZATION: bool = True
    MAX_SPEAKERS: int = 4
    MIN_SPEAKERS: int = 2
    # Use streaming/synchronous recognition API for better diarization support
    USE_STREAMING_FOR_DIARIZATION: bool = False

    # 其他STT功能
    ENABLE_PUNCTUATION: bool = True

    # ECPay 金流設定
    ECPAY_MERCHANT_ID: str = ""  # 商店代號
    ECPAY_HASH_KEY: str = ""  # HashKey
    ECPAY_HASH_IV: str = ""  # HashIV
    ECPAY_ENVIRONMENT: str = "sandbox"  # "sandbox" or "production"

    # Frontend/Backend URLs for ECPay callbacks
    FRONTEND_URL: str = "http://localhost:3000"
    API_BASE_URL: str = "http://localhost:8000"

    # Admin webhook token for manual operations
    ADMIN_WEBHOOK_TOKEN: str = "change-me-in-production"

    # Email Configuration (for payment notifications)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    # Worker 設定
    WORKER_CONCURRENCY: int = 4
    TASK_TIME_LIMIT: int = 7200  # seconds

    # Storage 設定
    STORAGE_BUCKET: str = "coaching-audio-{env}"
    RETENTION_DAYS: int = 1
    SIGNED_URL_EXPIRY_MINUTES: int = 30

    # Cloudflare 設定
    CLOUDFLARE_API_TOKEN: str = ""
    CLOUDFLARE_ZONE_ID: str = ""
    CLOUDFLARE_ACCOUNT_ID: str = ""
    DOMAIN: str = ""

    class Config:
        # 只在非 production 環境載入 .env 檔案，避免覆蓋 Render.com 環境變數
        env_file = ".env" if os.getenv("ENVIRONMENT") != "production" else None
        case_sensitive = True

    @field_validator("STT_PROVIDER", mode="before")
    @classmethod
    def validate_stt_provider(cls, value: str) -> str:
        if value is None:
            raise ValueError("STT_PROVIDER 必須設定，請提供有效的 STT provider")

        if not isinstance(value, str):
            raise ValueError("STT_PROVIDER 必須是字串")

        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("STT_PROVIDER 不可為空白")

        allowed_providers = {
            "google",
            "google_stt_v2",
            "assemblyai",
            "whisper",
        }
        if normalized not in allowed_providers:
            raise ValueError(
                "STT_PROVIDER 必須為以下其中之一: "
                + ", ".join(sorted(allowed_providers))
            )

        return normalized

    @field_validator("TEST_MODE")
    @classmethod
    def validate_test_mode(cls, value: bool, values) -> bool:
        # 確保 TEST_MODE 在生產環境中不能啟用
        environment = os.getenv("ENVIRONMENT", "development")
        if value is True and environment == "production":
            raise ValueError("TEST_MODE 不可在生產環境中啟用！這會造成嚴重的安全漏洞。")
        return value


settings = Settings()
