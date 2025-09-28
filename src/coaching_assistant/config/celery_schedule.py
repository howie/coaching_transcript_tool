"""Celery beat schedule configuration for admin reports and subscription maintenance."""

from celery.schedules import crontab

# Celery Beat Schedule Configuration
CELERYBEAT_SCHEDULE = {
    # Daily report at 8:00 AM UTC (covers previous day)
    "daily-admin-report": {
        "task": (
            "coaching_assistant.tasks.admin_report_tasks.generate_and_send_daily_report"
        ),
        "schedule": crontab(hour=8, minute=0),  # 8:00 AM UTC daily
        "options": {
            "expires": 3600,  # Expire after 1 hour
            "retry": True,
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 0,
                "interval_step": 300,  # 5 minutes
                "interval_max": 1800,  # 30 minutes
            },
        },
    },
    # Weekly report every Monday at 9:00 AM UTC
    "weekly-admin-report": {
        "task": (
            "coaching_assistant.tasks.admin_report_tasks.schedule_weekly_summary_report"
        ),
        "schedule": crontab(hour=9, minute=0, day_of_week=1),  # Monday 9:00 AM UTC
        "options": {
            "expires": 7200,  # Expire after 2 hours
            "retry": True,
            "retry_policy": {
                "max_retries": 2,
                "interval_start": 0,
                "interval_step": 600,  # 10 minutes
                "interval_max": 3600,  # 1 hour
            },
        },
    },
    # Health check report (optional) - every 6 hours
    "system-health-check": {
        "task": (
            "coaching_assistant.tasks.admin_report_tasks.generate_and_send_daily_report"
        ),
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        "kwargs": {
            "target_date_str": None,  # Current day
            "recipient_emails": None,  # Use default admin emails
        },
        "options": {
            "expires": 1800,  # Expire after 30 minutes
            "enabled": False,  # Disabled by default - enable if needed
        },
    },
    # Subscription maintenance - runs every 6 hours
    "subscription-maintenance": {
        "task": (
            "coaching_assistant.tasks.subscription_maintenance_tasks."
            "process_subscription_maintenance"
        ),
        "schedule": crontab(
            minute=0, hour="*/6"
        ),  # Every 6 hours at the top of the hour
        "options": {
            "expires": 3600,  # Expire after 1 hour
            "retry": True,
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 300,  # Start with 5 minutes
                "interval_step": 300,  # Increase by 5 minutes each retry
                "interval_max": 1800,  # Max 30 minutes
            },
        },
    },
    # Webhook log cleanup - runs daily at 2:00 AM UTC
    "webhook-log-cleanup": {
        "task": (
            "coaching_assistant.tasks.subscription_maintenance_tasks.cleanup_old_webhook_logs"
        ),
        "schedule": crontab(hour=2, minute=0),  # 2:00 AM UTC daily
        "options": {
            "expires": 1800,  # Expire after 30 minutes
            "retry": False,  # Don't retry cleanup tasks
        },
    },
    # Failed payment retry processing - runs every 2 hours
    "failed-payment-processing": {
        "task": (
            "coaching_assistant.tasks.subscription_maintenance_tasks."
            "process_subscription_maintenance"
        ),
        "schedule": crontab(
            minute=30, hour="*/2"
        ),  # Every 2 hours at 30 minutes past the hour
        "options": {
            "expires": 1800,  # Expire after 30 minutes
            "retry": True,
            "retry_policy": {
                "max_retries": 2,
                "interval_start": 300,  # 5 minutes
                "interval_step": 300,  # 5 minutes
                "interval_max": 900,  # 15 minutes max
            },
        },
    },
}

# Timezone for schedule
CELERY_TIMEZONE = "UTC"

# Beat scheduler settings
CELERYBEAT_SCHEDULER = (
    "django_celery_beat.schedulers:DatabaseScheduler"  # If using Django
)
# For pure Celery without Django:
# CELERYBEAT_SCHEDULER = 'celery.beat:PersistentScheduler'

# Additional Celery configurations for admin reports and subscription tasks
CELERY_TASK_ROUTES = {
    "coaching_assistant.tasks.admin_report_tasks.generate_and_send_daily_report": {
        "queue": "admin_reports",
        "routing_key": "admin_reports",
        "priority": 8,  # High priority
    },
    "coaching_assistant.tasks.admin_report_tasks.schedule_weekly_summary_report": {
        "queue": "admin_reports",
        "routing_key": "admin_reports",
        "priority": 7,  # High priority
    },
    "coaching_assistant.tasks.subscription_maintenance_tasks.process_subscription_maintenance": {
        "queue": "subscription_maintenance",
        "routing_key": "subscription_maintenance",
        "priority": (9),  # Very high priority for critical subscription processing
    },
    "coaching_assistant.tasks.subscription_maintenance_tasks.process_failed_payment_retry": {
        "queue": "payment_retry",
        "routing_key": "payment_retry",
        "priority": 8,  # High priority
    },
    "coaching_assistant.tasks.subscription_maintenance_tasks.send_payment_failure_notifications": {
        "queue": "notifications",
        "routing_key": "notifications",
        "priority": 6,  # Medium-high priority
    },
    "coaching_assistant.tasks.subscription_maintenance_tasks.cleanup_old_webhook_logs": {
        "queue": "maintenance",
        "routing_key": "maintenance",
        "priority": 3,  # Low priority
    },
}

# Task expiry settings
CELERY_TASK_RESULT_EXPIRES = 3600  # 1 hour

# Queue configuration for admin reports
CELERY_TASK_QUEUES = {
    "admin_reports": {
        "exchange": "admin_reports",
        "exchange_type": "direct",
        "routing_key": "admin_reports",
        "queue_arguments": {"x-max-priority": 10, "x-queue-mode": "default"},
    }
}

# Task annotations for better monitoring
CELERY_TASK_ANNOTATIONS = {
    "coaching_assistant.tasks.admin_report_tasks.generate_and_send_daily_report": {
        "rate_limit": "10/m",  # Max 10 reports per minute
        "time_limit": 1800,  # 30 minutes timeout
        "soft_time_limit": 1500,  # 25 minutes soft timeout
    },
    "coaching_assistant.tasks.admin_report_tasks.schedule_weekly_summary_report": {
        "rate_limit": "2/h",  # Max 2 weekly reports per hour
        "time_limit": 3600,  # 1 hour timeout
        "soft_time_limit": 3300,  # 55 minutes soft timeout
    },
}
