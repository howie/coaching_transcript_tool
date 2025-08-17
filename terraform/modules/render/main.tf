# Local values for common environment variables
locals {
  common_env_vars = merge(
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
      ENABLE_PUNCTUATION        = var.enable_punctuation
      
      # Storage configuration
      AUDIO_STORAGE_BUCKET     = var.audio_storage_bucket
      TRANSCRIPT_STORAGE_BUCKET = var.transcript_storage_bucket
      
      # STT configuration
      STT_PROVIDER        = var.stt_provider
      GOOGLE_STT_MODEL    = var.google_stt_model
      GOOGLE_STT_LOCATION = var.google_stt_location
      ASSEMBLYAI_API_KEY  = var.assemblyai_api_key
      
      # GCP configuration
      GCP_PROJECT_ID                     = var.gcp_project_id
      GOOGLE_APPLICATION_CREDENTIALS_JSON = var.gcp_service_account_json
      
      # Authentication
      GOOGLE_CLIENT_ID     = var.google_client_id
      GOOGLE_CLIENT_SECRET = var.google_client_secret
      
      # reCAPTCHA
      RECAPTCHA_ENABLED   = var.recaptcha_enabled
      RECAPTCHA_SECRET    = var.recaptcha_secret
      RECAPTCHA_MIN_SCORE = var.recaptcha_min_score
      
      # File upload limits
      MAX_FILE_SIZE      = var.max_file_size
      MAX_AUDIO_DURATION = var.max_audio_duration
      
      # Logging
      LOG_LEVEL  = var.log_level
      LOG_FORMAT = "json"
    }
  )
}

# PostgreSQL Database
resource "render_postgres" "main" {
  name                = "${var.project_name}-db-${var.environment}"
  plan               = var.database_plan
  region             = var.region
  version            = var.postgres_version
  
  # High availability (for production)
  high_availability  = var.environment == "production" ? var.database_ha : false
  
  # Database configuration
  database_name = var.database_name
  database_user = var.database_user
  
  # Backup configuration
  backup_enabled = var.backup_enabled
  backup_retention_days = var.backup_retention_days
  
  # Maintenance window
  maintenance_window {
    day_of_week = var.maintenance_day
    start_time  = var.maintenance_time
    duration    = var.maintenance_duration
  }
  
  # Performance settings
  shared_preload_libraries = ["pg_stat_statements"]
  
  tags = [
    "terraform",
    var.project_name,
    "database",
    var.environment
  ]
}

# Database read replica (Production only)
resource "render_postgres_read_replica" "main_replica" {
  count = var.environment == "production" && var.enable_read_replica ? 1 : 0
  
  name               = "${var.project_name}-db-replica-${var.environment}"
  primary_postgres_id = render_postgres.main.id
  region             = var.replica_region
  
  tags = [
    "terraform",
    var.project_name,
    "database-replica",
    var.environment
  ]
}

# Database backup policy
resource "render_postgres_backup_policy" "main" {
  count = var.backup_enabled ? 1 : 0
  
  postgres_id = render_postgres.main.id
  
  retention_days = var.backup_retention_days
  
  schedule {
    hour   = var.backup_hour
    minute = var.backup_minute
  }
  
  # Point-in-time recovery (Enterprise only)
  point_in_time_recovery_enabled = var.environment == "production" ? true : false
}

# Redis Instance
resource "render_redis" "main" {
  name   = "${var.project_name}-redis-${var.environment}"
  plan   = var.redis_plan
  region = var.region
  
  # Redis configuration
  max_memory_policy = "allkeys-lru"
  
  # High availability (for production)
  high_availability = var.environment == "production" ? true : false
  
  # Backup configuration
  backup_enabled = true
  backup_retention_days = var.redis_backup_retention_days
  
  tags = [
    "terraform",
    var.project_name,
    "redis",
    var.environment
  ]
}

# API Web Service
resource "render_web_service" "api" {
  name               = "${var.project_name}-api-${var.environment}"
  runtime           = "docker"
  repo              = var.github_repo_url
  branch            = var.branch
  root_directory    = "apps/api-server"
  dockerfile_path   = "Dockerfile.api"
  
  service_details {
    env              = var.environment
    plan             = var.api_plan
    region           = var.region
    num_instances    = var.api_instances
    
    auto_deploy      = var.auto_deploy
    
    # Build configuration
    build_command    = ""  # Docker build
    start_command    = ""  # Use Dockerfile CMD
    
    # Health check
    health_check_path = "/api/health"
    
    # Environment variables
    environment_variables = merge(
      local.common_env_vars,
      var.api_env_vars,
      {
        # Container specific
        IS_CONTAINER = "true"
        PORT         = "10000"
        
        # Database connections
        DATABASE_URL = render_postgres.main.connection_string
        REDIS_URL    = render_redis.main.connection_string
        
        # Application config
        ENVIRONMENT     = var.environment
        SECRET_KEY      = var.api_secret_key
        DEBUG           = var.environment == "development" ? "true" : "false"
        
        # CORS configuration
        ALLOWED_ORIGINS = join(",", var.allowed_origins)
        
        # Security
        JWT_ALGORITHM                    = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES      = "30"
        REFRESH_TOKEN_EXPIRE_DAYS        = "7"
      }
    )
    
    # Secret files
    secret_files = var.secret_files
  }
  
  # Custom domains
  custom_domains = var.api_custom_domains
  
  # Auto-scaling
  auto_scaling {
    enabled = var.enable_auto_scaling
    min_instances = var.min_instances
    max_instances = var.max_instances
    target_cpu_percent = var.target_cpu_percent
    target_memory_percent = var.target_memory_percent
  }
  
  tags = [
    "terraform",
    var.project_name,
    "api",
    var.environment
  ]
}

# Celery Worker Service
resource "render_background_worker" "celery" {
  name               = "${var.project_name}-worker-${var.environment}"
  runtime           = "docker"
  repo              = var.github_repo_url
  branch            = var.branch
  root_directory    = "apps/worker"
  dockerfile_path   = "Dockerfile"
  
  service_details {
    env              = var.environment
    plan             = var.worker_plan
    region           = var.region
    
    auto_deploy      = var.auto_deploy
    
    # Worker specific configuration
    start_command    = "celery -A coaching_assistant.core.celery_app worker --loglevel=info --concurrency=${var.worker_concurrency}"
    
    # Environment variables (shared with API)
    environment_variables = merge(
      local.common_env_vars,
      var.worker_env_vars,
      {
        # Container specific
        IS_CONTAINER = "true"
        
        # Database connections
        DATABASE_URL = render_postgres.main.connection_string
        REDIS_URL    = render_redis.main.connection_string
        
        # Worker configuration
        WORKER_CONCURRENCY = tostring(var.worker_concurrency)
        TASK_TIME_LIMIT    = tostring(var.task_time_limit)
        
        # Same config as API for consistency
        ENVIRONMENT = var.environment
      }
    )
    
    secret_files = var.secret_files
  }
  
  # Auto-scaling for workers
  auto_scaling {
    enabled = var.enable_worker_auto_scaling
    min_instances = var.worker_min_instances
    max_instances = var.worker_max_instances
    target_cpu_percent = var.worker_target_cpu_percent
    target_memory_percent = var.worker_target_memory_percent
  }
  
  tags = [
    "terraform",
    var.project_name,
    "worker",
    var.environment
  ]
}

# Flower Monitoring (Optional)
resource "render_background_worker" "flower" {
  count = var.enable_flower_monitoring ? 1 : 0
  
  name               = "${var.project_name}-flower-${var.environment}"
  runtime           = "docker"
  repo              = var.github_repo_url
  branch            = var.branch
  root_directory    = "apps/worker"
  dockerfile_path   = "Dockerfile.flower"
  
  service_details {
    env              = var.environment
    plan             = "starter"  # Smaller plan for monitoring
    region           = var.region
    
    start_command    = "celery -A coaching_assistant.core.celery_app flower --port=5555"
    
    environment_variables = {
      REDIS_URL           = render_redis.main.connection_string
      FLOWER_BASIC_AUTH   = var.flower_auth
      FLOWER_PORT         = "5555"
    }
  }
  
  tags = ["terraform", "monitoring", var.environment]
}

# Environment Variable Groups
resource "render_env_var_group" "development" {
  count = var.environment == "development" ? 1 : 0
  
  name = "${var.project_name}-dev"
  
  environment_variables = {
    DEBUG           = "true"
    LOG_LEVEL      = "DEBUG"
    RECAPTCHA_ENABLED = "false"
    MAX_FILE_SIZE   = "50"  # Smaller limits for dev
  }
}

resource "render_env_var_group" "production" {
  count = var.environment == "production" ? 1 : 0
  
  name = "${var.project_name}-prod"
  
  environment_variables = {
    DEBUG           = "false"
    LOG_LEVEL      = "INFO"
    RECAPTCHA_ENABLED = "true"
    MAX_FILE_SIZE   = "500"  # Full limits for prod
  }
}

# Service Monitoring
resource "render_service_monitoring" "api" {
  count = var.monitoring_email != "" ? 1 : 0
  
  service_id = render_web_service.api.id
  
  # Health check configuration
  health_check_enabled = true
  health_check_path    = "/api/health"
  health_check_interval = 30  # seconds
  
  # Alert configuration
  alerts = [
    {
      type = "response_time"
      threshold = 5000  # 5 seconds
      notification_email = var.monitoring_email
    },
    {
      type = "error_rate"
      threshold = 5  # 5%
      notification_email = var.monitoring_email
    },
    {
      type = "cpu_usage"
      threshold = 80  # 80%
      notification_email = var.monitoring_email
    },
    {
      type = "memory_usage"
      threshold = 85  # 85%
      notification_email = var.monitoring_email
    }
  ]
}

resource "render_service_monitoring" "worker" {
  count = var.monitoring_email != "" ? 1 : 0
  
  service_id = render_background_worker.celery.id
  
  alerts = [
    {
      type = "cpu_usage"
      threshold = 80
      notification_email = var.monitoring_email
    },
    {
      type = "memory_usage"
      threshold = 85
      notification_email = var.monitoring_email
    }
  ]
}

# Database Monitoring
resource "render_postgres_monitoring" "main" {
  count = var.monitoring_email != "" ? 1 : 0
  
  postgres_id = render_postgres.main.id
  
  alerts = [
    {
      type = "connection_count"
      threshold = 80  # 80% of max connections
      notification_email = var.monitoring_email
    },
    {
      type = "storage_usage"
      threshold = 85  # 85% of disk space
      notification_email = var.monitoring_email
    },
    {
      type = "query_duration"
      threshold = 10000  # 10 seconds
      notification_email = var.monitoring_email
    }
  ]
}

# Redis Monitoring
resource "render_redis_monitoring" "main" {
  count = var.monitoring_email != "" ? 1 : 0
  
  redis_id = render_redis.main.id
  
  # Alert thresholds
  memory_usage_threshold = 80  # Alert at 80% memory usage
  cpu_usage_threshold    = 70  # Alert at 70% CPU usage
  
  notification_email = var.monitoring_email
}