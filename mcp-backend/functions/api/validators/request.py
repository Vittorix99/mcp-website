from functools import wraps
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Union

from flask import jsonify


ValidationRule = Dict[str, Any]


def require_json_body(handler: Callable):
    """Ensure the request carries JSON and stash it on the request."""

    @wraps(handler)
    def wrapper(req, *args, **kwargs):
        payload = getattr(req, "json_data", None) or req.get_json(silent=True)
        if not payload:
            return jsonify({"error": "Missing request body"}), 400
        setattr(req, "json_data", payload)
        return handler(req, *args, **kwargs)

    return wrapper


def validate_body_fields(
    schema: Dict[str, ValidationRule],
    *,
    allow_extra: bool = True,
):
    """
    Validate keys and types inside the JSON body. Each schema entry may contain:
    - required: bool (default True)
    - types: type or tuple of types
    - validator: callable that returns bool
    - error: custom error message
    """

    def decorator(handler: Callable):
        @wraps(handler)
        def wrapper(req, *args, **kwargs):
            payload = getattr(req, "json_data", None) or req.get_json(silent=True)
            if not payload:
                return jsonify({"error": "Missing request body"}), 400

            errors = _validate_payload(payload, schema)
            if errors:
                return jsonify({"error": "validation_error", "messages": errors}), 400

            if not allow_extra:
                extra = set(payload.keys()) - set(schema.keys())
                if extra:
                    return jsonify(
                        {"error": "validation_error", "messages": [f"Unexpected fields: {', '.join(extra)}"]},
                    ), 400

            setattr(req, "json_data", payload)
            return handler(req, *args, **kwargs)

        return wrapper

    return decorator


def validate_query_params(
    schema: Dict[str, ValidationRule],
    *,
    allow_extra: bool = True,
):
    """
    Validate GET query parameters (req.args).
    """

    def decorator(handler: Callable):
        @wraps(handler)
        def wrapper(req, *args, **kwargs):
            params = req.args or {}
            errors = _validate_payload(params, schema, allow_missing=False)

            if errors:
                return jsonify({"error": "validation_error", "messages": errors}), 400

            if not allow_extra:
                extra = set(params.keys()) - set(schema.keys())
                if extra:
                    return jsonify(
                        {"error": "validation_error", "messages": [f"Unexpected params: {', '.join(extra)}"]},
                    ), 400

            return handler(req, *args, **kwargs)

        return wrapper

    return decorator


def inject_payload_fields(
    mapping: Iterable[Union[str, Tuple[str, str], Tuple[str, str, Any]]],
    *,
    source_attr: str = "json_data",
):
    """
    Pass selected payload fields to the handler.
    `mapping` entries can be either `field_name` or `(dest_name, field_name)`.
    """

    def decorator(handler: Callable):
        @wraps(handler)
        def wrapper(req, *args, **kwargs):
            payload = getattr(req, source_attr, {})
            injected = {}
            for entry in mapping:
                if isinstance(entry, tuple):
                    dest = entry[0]
                    source = entry[1]
                    default = entry[2] if len(entry) >= 3 else None
                else:
                    dest = source = entry
                    default = None

                value = payload.get(source, default)
                if value in (None, "") and default is None:
                    return jsonify({"error": f"Missing payload field '{source}'"}), 400
                injected[dest] = default if value in (None, "") and default is not None else value

            return handler(req, *args, **{**kwargs, **injected})

        return wrapper

    return decorator


def inject_payload_dto(
    dto_cls: Callable[..., Any],
    *,
    arg_name: str = "dto",
    exclude: Iterable[str] = (),
    include: Optional[Iterable[str]] = None,
    source_attr: str = "json_data",
):
    def decorator(handler: Callable):
        @wraps(handler)
        def wrapper(req, *args, **kwargs):
            payload = getattr(req, source_attr, {}) or {}
            data = {k: v for k, v in payload.items() if (include is None or k in include) and k not in exclude}
            if hasattr(dto_cls, "from_payload") and callable(getattr(dto_cls, "from_payload")):
                dto_instance = dto_cls.from_payload(data)
            else:
                dto_instance = dto_cls(**data)
            return handler(req, *args, **{**kwargs, arg_name: dto_instance})

        return wrapper

    return decorator


def inject_query_params(
    mapping: Iterable[Union[str, Tuple[str, str], Tuple[str, str, Any]]],
    *,
    source_attr: str = "args",
    allow_missing: bool = False,
):
    def decorator(handler: Callable):
        @wraps(handler)
        def wrapper(req, *args, **kwargs):
            params = getattr(req, source_attr, {}) or {}
            injected = {}
            for entry in mapping:
                if isinstance(entry, tuple):
                    dest = entry[0]
                    source = entry[1]
                    default = entry[2] if len(entry) >= 3 else None
                else:
                    dest = source = entry
                    default = None
                value = params.get(source, default)
                if value in (None, "") and default is None and not allow_missing:
                    return jsonify({"error": f"Missing query parameter '{source}'"}), 400
                injected[dest] = default if value in (None, "") and default is not None else value
            return handler(req, *args, **{**kwargs, **injected})
        return wrapper
    return decorator


def _validate_payload(payload: Dict[str, Any], schema: Dict[str, ValidationRule], *, allow_missing: bool = True):
    errors = []
    for field_name, rule in schema.items():
        required = rule.get("required", True)
        value = payload.get(field_name)

        if required and not allow_missing and value in (None, ""):
            errors.append(rule.get("error") or f"Missing required field '{field_name}'")
            continue
        if required and value in (None, ""):
            errors.append(rule.get("error") or f"Missing required field '{field_name}'")
            continue

        expected_type = rule.get("types")
        if value not in (None, "") and expected_type:
            types = expected_type if isinstance(expected_type, tuple) else (expected_type,)
            if not isinstance(value, tuple(types)):
                errors.append(
                    rule.get("error")
                    or f"Field '{field_name}' must be of type {', '.join(t.__name__ for t in types)}"
                )
                continue

        validator = rule.get("validator")
        if validator and value not in (None, "") and not validator(value):
            errors.append(rule.get("error") or f"Field '{field_name}' failed validation")

    return errors
