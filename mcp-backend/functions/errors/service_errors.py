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


class SoundCloudAuthError(ExternalServiceError):
    """SoundCloud OAuth token request failed."""


class SoundCloudTrackNotFoundError(NotFoundError):
    """SoundCloud track not found at the given URL."""


class SoundCloudTrackNotPlayableError(ValidationError):
    """SoundCloud track exists but is not streamable/playable."""


class SoundCloudAPIError(ExternalServiceError):
    """Unexpected error from the SoundCloud API."""


class RadioSeasonNotFoundError(NotFoundError):
    """Radio season document does not exist."""


class RadioEpisodeNotFoundError(NotFoundError):
    """Radio episode document does not exist."""
