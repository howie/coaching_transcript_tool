"""
Custom exceptions for the coaching assistant application.
"""

from typing import Optional, Dict, Any


class CoachingAssistantException(Exception):
    """Base exception for all coaching assistant errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PlanLimitExceeded(CoachingAssistantException):
    """Raised when a user exceeds their plan limits."""
    
    def __init__(
        self,
        message: str,
        limit_type: str,
        current_value: int,
        limit_value: int,
        upgrade_suggestion: Optional[str] = None
    ):
        details = {
            "limit_type": limit_type,
            "current_value": current_value,
            "limit_value": limit_value,
            "upgrade_suggestion": upgrade_suggestion
        }
        super().__init__(message, details)
        self.limit_type = limit_type
        self.current_value = current_value
        self.limit_value = limit_value
        self.upgrade_suggestion = upgrade_suggestion


class PaymentRequired(CoachingAssistantException):
    """Raised when payment is required to proceed."""
    
    def __init__(self, message: str, required_plan: Optional[str] = None):
        details = {"required_plan": required_plan}
        super().__init__(message, details)
        self.required_plan = required_plan


class InvalidPlanConfiguration(CoachingAssistantException):
    """Raised when plan configuration is invalid."""
    pass


class UsageTrackingError(CoachingAssistantException):
    """Raised when there's an error tracking usage."""
    pass


class SubscriptionError(CoachingAssistantException):
    """Raised when there's an error with subscription management."""
    pass


class TranscriptionError(CoachingAssistantException):
    """Raised when transcription fails."""
    
    def __init__(self, message: str, provider: Optional[str] = None, error_code: Optional[str] = None):
        details = {
            "provider": provider,
            "error_code": error_code
        }
        super().__init__(message, details)
        self.provider = provider
        self.error_code = error_code


class AuthenticationError(CoachingAssistantException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(CoachingAssistantException):
    """Raised when authorization fails."""
    pass


class ValidationError(CoachingAssistantException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        details = {
            "field": field,
            "value": value
        }
        super().__init__(message, details)
        self.field = field
        self.value = value


class ResourceNotFound(CoachingAssistantException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} with id '{resource_id}' not found"
        details = {
            "resource_type": resource_type,
            "resource_id": resource_id
        }
        super().__init__(message, details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ConcurrentProcessingLimitExceeded(PlanLimitExceeded):
    """Raised when concurrent processing limit is exceeded."""
    
    def __init__(self, current_processing: int, max_concurrent: int):
        message = f"Concurrent processing limit exceeded: {current_processing}/{max_concurrent}"
        super().__init__(
            message=message,
            limit_type="concurrent_processing",
            current_value=current_processing,
            limit_value=max_concurrent
        )


class ExportFormatNotAllowed(PlanLimitExceeded):
    """Raised when export format is not allowed for the user's plan."""
    
    def __init__(self, format: str, allowed_formats: list[str], required_plan: str):
        message = f"Export format '{format}' not allowed. Allowed formats: {', '.join(allowed_formats)}"
        super().__init__(
            message=message,
            limit_type="export_format",
            current_value=0,
            limit_value=0,
            upgrade_suggestion=required_plan
        )
        self.format = format
        self.allowed_formats = allowed_formats