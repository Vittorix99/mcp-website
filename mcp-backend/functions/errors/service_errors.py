class ServiceError(Exception):
    """Base exception for service-layer errors."""


class ValidationError(ServiceError):
    """Input or domain validation failed."""


class NotFoundError(ServiceError):
    """Requested entity does not exist."""


class ConflictError(ServiceError):
    """Conflict with existing resources."""


class ForbiddenError(ServiceError):
    """Operation is not permitted."""


class ExternalServiceError(ServiceError):
    """Upstream provider failed or returned an unexpected response."""
