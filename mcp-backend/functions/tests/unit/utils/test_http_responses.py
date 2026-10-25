from flask import Flask
from pydantic import BaseModel, ValidationError

from utils.http_responses import handle_pydantic_error
from tests.utils import unwrap_response


class _RequestDTO(BaseModel):
    email: str
    count: int


def test_pydantic_error_exposes_sanitized_field_details():
    app = Flask(__name__)

    try:
        _RequestDTO.model_validate({"count": "not-an-integer"})
    except ValidationError as err:
        with app.app_context():
            payload, status = unwrap_response(handle_pydantic_error(err))
    else:
        raise AssertionError("Expected Pydantic validation to fail")

    assert status == 400
    assert payload["error"] == "Invalid request data"
    assert payload["details"] == [
        {
            "field": "email",
            "message": "Field required",
            "type": "missing",
        },
        {
            "field": "count",
            "message": "Input should be a valid integer, unable to parse string as an integer",
            "type": "int_parsing",
        },
    ]
    assert all("input" not in detail for detail in payload["details"])
