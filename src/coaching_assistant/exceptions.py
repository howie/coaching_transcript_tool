"""Custom exceptions for the coaching assistant application."""


class DomainException(Exception):
    """Exception raised for domain-specific business logic violations.
    
    This exception is used to signal violations of business rules
    within the domain layer of the Clean Architecture.
    """
    pass


class PlanLimitExceededException(DomainException):
    """Exception raised when a user exceeds their plan limits."""
    pass


class InvalidStatusTransitionException(DomainException):
    """Exception raised when attempting an invalid status transition."""
    pass


class SubscriptionException(DomainException):
    """Exception raised for subscription-related errors."""
    pass


class AuthorizationException(DomainException):
    """Exception raised for authorization-related errors."""
    pass