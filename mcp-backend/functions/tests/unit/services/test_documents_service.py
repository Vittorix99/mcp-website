from io import BytesIO

import pytest

from services.events.documents_service import DocumentsService, StoredDocument


class _DummyBlob:
    def __init__(self):
        self.public_url = "https://example.com/file.pdf"
        self.uploads = []

    def upload_from_string(self, data, content_type=None):
        self.uploads.append((data, content_type))


class _DummyStorage:
    def __init__(self):
        self.blobs = {}

    def blob(self, path):
        blob = self.blobs.get(path)
        if not blob:
            blob = _DummyBlob()
            self.blobs[path] = blob
        return blob


def _make_service():
    return DocumentsService(storage=_DummyStorage())


def test_create_membership_card_requires_valid_subscription(monkeypatch):
    """Rejects invalid subscriptions."""
    service = _make_service()
    with pytest.raises(ValueError):
        service.create_membership_card("mem-1", {"subscription_valid": False})


def test_create_membership_card_pdf_failure(monkeypatch):
    """Raises when PDF generation fails."""
    service = _make_service()
    monkeypatch.setattr("services.events.documents_service.generate_membership_pdf", lambda *args, **kwargs: None)
    with pytest.raises(RuntimeError):
        service.create_membership_card("mem-1", {"subscription_valid": True})


def test_create_membership_card_success(monkeypatch):
    """Stores membership PDF and returns StoredDocument."""
    service = _make_service()
    monkeypatch.setattr(
        "services.events.documents_service.generate_membership_pdf",
        lambda *args, **kwargs: BytesIO(b"pdf"),
    )
    doc = service.create_membership_card("mem-1", {"subscription_valid": True, "end_date": "31-12-2026"})
    assert isinstance(doc, StoredDocument)
    assert doc.storage_path.endswith("memberships/cards/mem-1.pdf")


def test_create_ticket_document_success(monkeypatch):
    """Stores ticket PDF and returns StoredDocument."""
    service = _make_service()
    monkeypatch.setattr(
        "services.events.documents_service.generate_ticket_pdf",
        lambda *args, **kwargs: BytesIO(b"pdf"),
    )
    doc = service.create_ticket_document({"name": "Mario"}, {"title": "Event"}, "tickets/test.pdf")
    assert doc.storage_path == "tickets/test.pdf"
    assert doc.public_url
