# Local values for common environment variables
locals {
  common_env_vars_raw = merge(
    var.common_env_vars,
    {
      # Version info
      APP_VERSION = var.app_version
      BUILD_ID    = var.build_id
      COMMIT_SHA  = var.commit_sha

      # Monitoring
      SENTRY_DSN = var.sentry_dsn

      # Feature flags
      ENABLE_SPEAKER_DIARIZATION = var.enable_speaker_diarization
      ENABLE_PUNCTUATION         = var.enable_punctuation

      # Storage configuration
      AUDIO_STORAGE_BUCKET      = var.audio_storage_bucket

      # STT configuration
      STT_PROVIDER        = var.stt_provider
      GOOGLE_STT_MODEL    = var.google_stt_model
      GOOGLE_STT_LOCATION = var.google_stt_location
      ASSEMBLYAI_API_KEY  = var.assemblyai_api_key

      # GCP configuration
      GOOGLE_PROJECT_ID                   = var.gcp_project_id
      GCP_PROJECT_ID                      = var.gcp_project_id  # Keep legacy for compatibility
      GOOGLE_APPLICATION_CREDENTIALS_JSON = var.gcp_service_account_json

      # Authentication
      GOOGLE_CLIENT_ID     = var.google_client_id
      GOOGLE_CLIENT_SECRET = var.google_client_secret
      FRONTEND_URL         = var.frontend_url

      # reCAPTCHA
      RECAPTCHA_ENABLED   = var.recaptcha_enabled
      RECAPTCHA_SECRET    = var.recaptcha_secret
      RECAPTCHA_MIN_SCORE = var.recaptcha_min_score

      # ECPay Configuration
      ECPAY_MERCHANT_ID = var.ecpay_merchant_id
      ECPAY_HASH_KEY    = var.ecpay_hash_key
      ECPAY_HASH_IV     = var.ecpay_hash_iv
      ECPAY_ENVIRONMENT = var.ecpay_environment

      # Admin Security
      ADMIN_WEBHOOK_TOKEN = var.admin_webhook_token

      # File upload limits
      MAX_FILE_SIZE      = var.max_file_size
      MAX_AUDIO_DURATION = var.max_audio_duration

      # Database configuration - Use internal URLs for production efficiency
      DATABASE_URL = render_postgres.main.connection_info.internal_connection_string
      REDIS_URL    = render_redis.main.connection_info.internal_connection_string

      # Celery configuration - Use internal URLs for production efficiency
      CELERY_BROKER_URL     = render_redis.main.connection_info.internal_connection_string
      CELERY_RESULT_BACKEND = render_redis.main.connection_info.internal_connection_string

      # Logging
      LOG_LEVEL  = var.log_level
      LOG_FORMAT = "json"
    }
  )

  # Convert string values to Render provider format
  common_env_vars = {
    for key, value in local.common_env_vars_raw : key => {
      value = value
    }
  }

  # API-specific environment variables (merge common + api-specific)
  api_env_vars = {
    for key, value in merge(local.common_env_vars_raw, var.api_env_vars) : key => {
      value = value
    }
  }

  # Worker-specific environment variables (merge common + worker-specific)  
  worker_env_vars = {
    for key, value in merge(local.common_env_vars_raw, var.worker_env_vars) : key => {
      value = value
    }
  }
}

# PostgreSQL Database
resource "render_postgres" "main" {
  name    = "${var.project_name}-db-${var.environment}"
  plan    = var.database_plan
  region  = var.region
  version = var.postgres_version

  # Database configuration
  database_name = var.database_name
  database_user = var.database_user
}


# Redis Instance
resource "render_redis" "main" {
  name              = "${var.project_name}-redis-${var.environment}"
  plan              = var.redis_plan
  region            = var.region
  max_memory_policy = "allkeys_lru"
}

# API Web Service
resource "render_web_service" "api" {
  name           = "${var.project_name}-api-${var.environment}"
  plan           = var.api_plan
  region         = var.region

  # Runtime source configuration - Use Docker for consistent environment
  runtime_source = {
    docker = {
      repo_url           = var.github_repo_url
      branch             = var.branch
      dockerfile_path    = "apps/api-server/Dockerfile.api"
      docker_context     = "."
      docker_build_args  = {}
    }
  }

  # Environment variables - Use API-specific env vars (includes common + API-specific)
  env_vars = local.api_env_vars
}

# Celery Worker Service
resource "render_background_worker" "celery" {
  name           = "${var.project_name}-worker-${var.environment}"
  plan           = var.worker_plan
  region         = var.region
  start_command  = "celery -A coaching_assistant.core.celery_app worker --loglevel=info"
  root_directory = "."

  # Runtime source configuration - Background workers use native runtime
  runtime_source = {
    native_runtime = {
      repo_url      = var.github_repo_url
      branch        = var.branch
      runtime       = "python"
      build_command = "pip install -r requirements.txt && pip install -e ."
    }
  }

  # Environment variables - Use worker-specific env vars (includes common + worker-specific)
  env_vars = local.worker_env_vars
}



