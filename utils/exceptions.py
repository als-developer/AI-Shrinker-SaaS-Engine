"""
Custom Exceptions - Application-specific Error Classes
For structured error handling and API responses
Version: 31.0
"""


class SovereignGridException(Exception):
    """Base exception for all Sovereign Grid errors"""
    pass


class AuthenticationError(SovereignGridException):
    """Authentication related errors (401)"""
    pass


class AuthorizationError(SovereignGridException):
    """Authorization/permission errors (403)"""
    pass


class RateLimitError(SovereignGridException):
    """Rate limit exceeded errors (429)"""
    pass


class InsufficientCreditsError(SovereignGridException):
    """Insufficient credits error (402)"""
    pass


class ValidationError(SovereignGridException):
    """Input validation errors (400)"""
    pass


class NotFoundError(SovereignGridException):
    """Resource not found errors (404)"""
    pass


class ConflictError(SovereignGridException):
    """Resource conflict errors (409)"""
    pass


class ServiceUnavailableError(SovereignGridException):
    """Service unavailable errors (503)"""
    pass


class DatabaseError(SovereignGridException):
    """Database operation errors"""
    pass


class CacheError(SovereignGridException):
    """Cache operation errors"""
    pass


class WebhookDeliveryError(SovereignGridException):
    """Webhook delivery failures"""
    pass


class PaymentProcessingError(SovereignGridException):
    """Payment processing failures"""
    pass


class CompressionError(SovereignGridException):
    """Model compression failures"""
    pass


class SLABreachError(SovereignGridException):
    """SLA breach detection"""
    pass


# Exception to status code mapping
EXCEPTION_STATUS_MAP = {
    AuthenticationError: 401,
    AuthorizationError: 403,
    RateLimitError: 429,
    InsufficientCreditsError: 402,
    ValidationError: 400,
    NotFoundError: 404,
    ConflictError: 409,
    ServiceUnavailableError: 503,
}
