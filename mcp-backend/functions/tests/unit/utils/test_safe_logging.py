from utils.safe_logging import mask_email, redact_sensitive


def test_redact_sensitive_masks_tokens_paths_and_emails():
    payload = {
        "api_key": "secret-value",
        "path": "/workspace/service_account.json",
        "context": {
            "to_email": "mario.rossi@example.com",
            "authorization": "Bearer abcdef1234567890abcdef1234567890",
        },
    }

    redacted = redact_sensitive(payload)

    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["path"] == "[REDACTED_PATH]"
    assert redacted["context"]["to_email"] == "ma***@example.com"
    assert redacted["context"]["authorization"] == "[REDACTED]"


def test_mask_email_keeps_domain_and_hides_local_part():
    assert mask_email("user@example.com") == "us***@example.com"
