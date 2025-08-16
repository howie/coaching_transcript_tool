"""
Celery task for resetting monthly usage counters.
Should be scheduled to run at midnight on the first day of each month.
"""

from celery import shared_task
from datetime import datetime
import logging
import requests
from coaching_assistant.core.config import settings

logger = logging.getLogger(__name__)


@shared_task(name="reset_monthly_usage")
def reset_monthly_usage():
    """
    Reset monthly usage counters for all users.
    This task should be scheduled to run at 00:00 UTC on the 1st of each month.
    """
    try:
        logger.info("Starting monthly usage reset task")
        
        # Call the API endpoint to reset usage
        # Using admin API key for authentication
        response = requests.post(
            f"{settings.API_BASE_URL}/api/v1/plan/reset-monthly-usage",
            params={"admin_key": settings.ADMIN_API_KEY},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Successfully reset usage for {result['users_reset']} users")
            return {
                "success": True,
                "users_reset": result['users_reset'],
                "reset_time": result['reset_time']
            }
        else:
            logger.error(f"Failed to reset usage: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"API returned {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"Error in monthly usage reset task: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@shared_task(name="check_usage_warnings")
def check_usage_warnings():
    """
    Check for users approaching their limits and send warnings.
    This could run daily to notify users at 80% and 90% usage.
    """
    try:
        from coaching_assistant.core.database import SessionLocal
        from coaching_assistant.core.models import User
        from coaching_assistant.services.usage_tracker import UsageTracker
        from coaching_assistant.services.plan_limits import PlanLimits, PlanName
        
        db = SessionLocal()
        tracker = UsageTracker(db)
        
        # Get all active users
        users = db.query(User).filter(User.is_active == True).all()
        
        warnings_sent = 0
        for user in users:
            try:
                # Get usage summary
                summary = tracker.get_usage_summary(user.id)
                
                # Check each metric for warning thresholds
                for metric in ['sessions', 'transcriptions', 'minutes']:
                    if summary[metric]['limit'] == -1:  # Skip unlimited
                        continue
                        
                    percentage = summary[metric]['percentage']
                    
                    # Send warning at 80% and 90%
                    if percentage >= 90 and not user.has_received_90_warning:
                        send_usage_warning(user, metric, 90, summary[metric])
                        user.has_received_90_warning = True
                        warnings_sent += 1
                    elif percentage >= 80 and not user.has_received_80_warning:
                        send_usage_warning(user, metric, 80, summary[metric])
                        user.has_received_80_warning = True
                        warnings_sent += 1
                        
            except Exception as e:
                logger.error(f"Error checking usage for user {user.id}: {str(e)}")
                continue
        
        db.commit()
        db.close()
        
        logger.info(f"Sent {warnings_sent} usage warnings")
        return {
            "success": True,
            "warnings_sent": warnings_sent
        }
        
    except Exception as e:
        logger.error(f"Error in usage warning task: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def send_usage_warning(user, metric: str, threshold: int, usage_info: dict):
    """
    Send usage warning email to user.
    
    Args:
        user: User object
        metric: The metric that triggered the warning
        threshold: Warning threshold (80 or 90)
        usage_info: Usage information for the metric
    """
    try:
        # This would integrate with your email service
        # For now, just log it
        logger.info(
            f"Usage warning for user {user.email}: "
            f"{metric} at {threshold}% "
            f"({usage_info['used']}/{usage_info['limit']})"
        )
        
        # TODO: Implement actual email sending
        # email_service.send_usage_warning(
        #     to=user.email,
        #     metric=metric,
        #     threshold=threshold,
        #     current=usage_info['used'],
        #     limit=usage_info['limit'],
        #     days_until_reset=usage_info.get('days_until_reset', 0)
        # )
        
    except Exception as e:
        logger.error(f"Failed to send usage warning: {str(e)}")


# Celery beat schedule configuration
# Add this to your celerybeat schedule:
"""
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    'reset-monthly-usage': {
        'task': 'reset_monthly_usage',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),  # First day of month at midnight
    },
    'check-usage-warnings': {
        'task': 'check_usage_warnings',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
}
"""