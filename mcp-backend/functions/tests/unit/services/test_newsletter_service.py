import pytest
from pydantic import ValidationError

from dto.newsletter_api import (
    NewsletterParticipantsRequestDTO,
    NewsletterSignupRequestDTO,
    NewsletterUpdateRequestDTO,
)
from errors.service_errors import NotFoundError
from models import NewsletterSignup
from services.communications.newsletter_service import NewsletterService


class InMemoryNewsletterRepository:
    def __init__(self, signups=()):
        self.signups = {signup.id: signup for signup in signups}
        self.participants = []

    def find_signup_by_email(self, email):
        return next((s for s in self.signups.values() if s.email == email), None)

    def add_signup_from_model(self, signup):
        signup.id = f"signup-{len(self.signups) + 1}"
        self.signups[signup.id] = signup
        return signup.id

    def get_signup(self, signup_id):
        return self.signups.get(signup_id)

    def stream_signups(self):
        return iter(self.signups.values())

    def update_signup_from_model(self, signup_id, signup):
        self.signups[signup_id] = signup

    def delete_signup(self, signup_id):
        del self.signups[signup_id]

    def add_participants_batch(self, participants):
        self.participants.extend(participants)


class RecordingMailService:
    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)
        return True


def _make_service(signups=()):
    repository = InMemoryNewsletterRepository(signups)
    mail = RecordingMailService()
    return NewsletterService(repository, mail), repository, mail


def test_signup_persists_signup_and_sends_welcome_to_subscriber():
    service, repository, mail = _make_service()

    result = service.signup(NewsletterSignupRequestDTO(email="user@example.com"))

    assert result.message == "Signed up for newsletter successfully"
    assert len(repository.signups) == 1
    assert next(iter(repository.signups.values())).email == "user@example.com"
    assert len(mail.messages) == 1
    assert mail.messages[0].to_email == "user@example.com"
    assert mail.messages[0].subject == "Welcome to MCP Newsletter!"


def test_signup_existing_email_does_not_duplicate_but_sends_welcome():
    existing = NewsletterSignup(id="signup-existing", email="user@example.com")
    service, repository, mail = _make_service([existing])

    service.signup(NewsletterSignupRequestDTO(email="user@example.com"))

    assert list(repository.signups) == ["signup-existing"]
    assert len(mail.messages) == 1
    assert mail.messages[0].to_email == "user@example.com"


@pytest.mark.parametrize("email", ["", "not-an-email"])
def test_signup_rejects_missing_or_invalid_email(email):
    with pytest.raises(ValidationError):
        NewsletterSignupRequestDTO(email=email)


def test_get_signup_by_id_returns_signup_response():
    signup = NewsletterSignup(id="signup-1", email="user@example.com", active=False)
    service, _, _ = _make_service([signup])

    result = service.get_signup_by_id("signup-1")

    assert result.signup.id == "signup-1"
    assert result.signup.email == "user@example.com"
    assert result.signup.active is False


def test_get_signup_by_id_missing_raises_not_found():
    service, _, _ = _make_service()

    with pytest.raises(NotFoundError, match="Newsletter signup not found"):
        service.get_signup_by_id("missing")


def test_get_all_signups_maps_repository_results():
    service, _, _ = _make_service([
        NewsletterSignup(id="signup-1", email="one@example.com"),
        NewsletterSignup(id="signup-2", email="two@example.com", active=False),
    ])

    result = service.get_all_signups()

    assert [(s.id, s.email, s.active) for s in result.signups] == [
        ("signup-1", "one@example.com", True),
        ("signup-2", "two@example.com", False),
    ]


def test_update_signup_persists_active_value():
    signup = NewsletterSignup(id="signup-1", email="user@example.com", active=True)
    service, repository, _ = _make_service([signup])

    result = service.update_signup(NewsletterUpdateRequestDTO(id="signup-1", active=False))

    assert result.message == "Newsletter signup updated successfully"
    assert repository.signups["signup-1"].active is False


def test_update_signup_missing_raises_not_found():
    service, _, _ = _make_service()

    with pytest.raises(NotFoundError, match="Newsletter signup not found"):
        service.update_signup(NewsletterUpdateRequestDTO(id="missing", active=False))


@pytest.mark.parametrize("payload", [{"id": "signup-1"}, {"id": "", "active": False}, {"id": "signup-1", "active": "sometimes"}])
def test_update_request_rejects_invalid_fields(payload):
    with pytest.raises(ValidationError):
        NewsletterUpdateRequestDTO.model_validate(payload)


def test_delete_signup_removes_repository_record():
    signup = NewsletterSignup(id="signup-1", email="user@example.com")
    service, repository, _ = _make_service([signup])

    result = service.delete_signup("signup-1")

    assert result.message == "Newsletter signup deleted successfully"
    assert "signup-1" not in repository.signups


def test_delete_signup_missing_raises_not_found():
    service, _, _ = _make_service()

    with pytest.raises(NotFoundError, match="Newsletter signup not found"):
        service.delete_signup("missing")


def test_add_participants_preserves_extra_fields():
    service, repository, _ = _make_service()
    request = NewsletterParticipantsRequestDTO(participants=[
        {"email": "participant@example.com", "name": "Pat", "group": "guests"},
    ])

    result = service.add_participants(request)

    assert result.message == "Participants added successfully"
    assert len(repository.participants) == 1
    assert repository.participants[0].email == "participant@example.com"
    assert repository.participants[0].extra == {"name": "Pat", "group": "guests"}


@pytest.mark.parametrize("participants", [[], [{"email": "invalid"}]])
def test_participants_request_rejects_empty_list_and_invalid_email(participants):
    with pytest.raises(ValidationError):
        NewsletterParticipantsRequestDTO(participants=participants)
