from services.core.error_logs_service import _normalize_message


def test_normalize_message_handles_sender_error_payload():
    payload = {
        "error": "No existing subscriber emails provided",
        "invalid_emails": [],
        "non_existing_subscribers": ["angelojr.cascino@cascino.it"],
    }

    assert _normalize_message(payload) == (
        "No existing subscriber emails provided | Missing: angelojr.cascino@cascino.it"
    )


def test_normalize_message_serializes_unknown_objects():
    payload = {"nested": {"code": 400}}

    assert _normalize_message(payload) == '{"nested": {"code": 400}}'
