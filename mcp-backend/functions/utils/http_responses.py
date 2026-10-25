from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from errors.service_errors import ConflictError, ExternalServiceError, ForbiddenError, NotFoundError, ServiceError, ValidationError


def handle_pydantic_error(err: PydanticValidationError):
    details = []
    for item in err.errors(include_context=False):
        location = ".".join(str(part) for part in item.get("loc", ()))
        details.append(
            {
                "field": location,
                "message": item.get("msg", "Invalid value"),
                "type": item.get("type", "validation_error"),
            }
        )
    return jsonify({"error": "Invalid request data", "details": details}), 400


def handle_service_error(err: Exception):
    if isinstance(err, ValidationError):
        details = getattr(err, "details", None)
        if details:
            return jsonify({"error": str(err), "messages": details}), 400
        return jsonify({"error": str(err)}), 400
    if isinstance(err, ForbiddenError):
        return jsonify({"error": str(err)}), 403
    if isinstance(err, NotFoundError):
        return jsonify({"error": str(err)}), 404
    if isinstance(err, ConflictError):
        payload = {"error": str(err)}
        details = getattr(err, "payload", None)
        if isinstance(details, dict):
            payload.update(details)
        return jsonify(payload), 409
    if isinstance(err, ExternalServiceError):
        return jsonify({"error": str(err)}), 502
    if isinstance(err, ServiceError):
        return jsonify({"error": str(err)}), 500
    return jsonify({"error": "Internal server error"}), 500
