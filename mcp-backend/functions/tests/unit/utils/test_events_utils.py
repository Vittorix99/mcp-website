from utils.events_utils import validate_email_format


def test_validate_email_format_accepts_valid_email():
    assert validate_email_format("mario.rossi+test@gmail.com") is True


def test_validate_email_format_rejects_invalid_email():
    assert validate_email_format("mario.rossi.gmail.com") is False
    assert validate_email_format("mario@localhost") is False
    assert validate_email_format("mario@") is False
