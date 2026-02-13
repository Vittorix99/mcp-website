from types import SimpleNamespace

import pytest

from services.newsletter_service import NewsletterService


class _DummyDoc:
    def __init__(self, doc_id, data, exists=True):
        self.id = doc_id
        self._data = data
        self.exists = exists

    def to_dict(self):
        return self._data


class _DummyDocRef:
    def __init__(self, collection, doc_id):
        self.collection = collection
        self.id = doc_id

    def get(self):
        if self.id in self.collection.data:
            return _DummyDoc(self.id, self.collection.data[self.id], True)
        return _DummyDoc(self.id, {}, False)

    def set(self, data):
        self.collection.data[self.id] = data

    def delete(self):
        self.collection.data.pop(self.id, None)


class _DummyQuery:
    def __init__(self, collection, filter_email=None, order_by=None, limit_value=None):
        self.collection = collection
        self.filter_email = filter_email
        self.order_by_field = order_by
        self.limit_value = limit_value

    def limit(self, n):
        self.limit_value = n
        return self

    def get(self):
        items = list(self.collection.data.items())
        if self.filter_email is not None:
            items = [(doc_id, data) for doc_id, data in items if data.get("email") == self.filter_email]
        if self.order_by_field:
            items = sorted(items, key=lambda kv: kv[1].get(self.order_by_field))
        if self.limit_value:
            items = items[: self.limit_value]
        return [_DummyDoc(doc_id, data, True) for doc_id, data in items]

    def stream(self):
        return iter(self.get())


class _DummyCollection:
    def __init__(self):
        self.data = {}
        self.counter = 0

    def where(self, field, op, value):
        return _DummyQuery(self, filter_email=value)

    def order_by(self, field, direction=None):
        return _DummyQuery(self, order_by=field)

    def document(self, doc_id=None):
        if doc_id is None:
            self.counter += 1
            doc_id = f"doc-{self.counter}"
        return _DummyDocRef(self, doc_id)

    def add(self, data):
        self.counter += 1
        doc_id = f"doc-{self.counter}"
        self.data[doc_id] = data
        return (None, SimpleNamespace(id=doc_id))

    def stream(self):
        return iter([_DummyDoc(doc_id, data, True) for doc_id, data in self.data.items()])


class _DummyBatch:
    def __init__(self):
        self.sets = []

    def set(self, doc_ref, data):
        self.sets.append((doc_ref, data))
        doc_ref.set(data)

    def commit(self):
        return True


class _DummyDB:
    def __init__(self):
        self._batch = _DummyBatch()

    def batch(self):
        return self._batch


def _make_service():
    service = NewsletterService.__new__(NewsletterService)
    service.db = _DummyDB()
    service.collection = _DummyCollection()
    service.participants_collection = _DummyCollection()
    service.logger = SimpleNamespace(debug=lambda *a, **k: None, info=lambda *a, **k: None, error=lambda *a, **k: None)
    return service


def test_signup_missing_email():
    """Returns 400 when email is missing."""
    service = _make_service()
    payload, status = service.signup({})
    assert status == 400
    assert payload["error"] == "Missing required fields"


def test_signup_stores_and_sends(monkeypatch):
    """Stores signup and sends email."""
    service = _make_service()
    monkeypatch.setenv("USER_EMAIL", "owner@example.com")
    monkeypatch.setattr("services.newsletter_service.mail_service.send", lambda *args, **kwargs: True)
    payload, status = service.signup({"email": "user@example.com"})
    assert status == 200
    assert payload["message"]
    assert service.collection.data


def test_signup_skips_existing(monkeypatch):
    """Does not duplicate existing signup."""
    service = _make_service()
    service.collection.data["doc-1"] = {"email": "user@example.com"}
    monkeypatch.setenv("USER_EMAIL", "owner@example.com")
    monkeypatch.setattr("services.newsletter_service.mail_service.send", lambda *args, **kwargs: True)
    payload, status = service.signup({"email": "user@example.com"})
    assert status == 200
    assert len(service.collection.data) == 1


def test_get_by_id_not_found():
    """Returns 404 when signup is missing."""
    service = _make_service()
    payload, status = service.get_by_id("missing")
    assert status == 404
    assert payload["error"] == "Newsletter signup not found"


def test_get_all_returns_list():
    """Returns list of signups."""
    service = _make_service()
    service.collection.data["doc-1"] = {"email": "user@example.com"}
    payload, status = service.get_all()
    assert status == 200
    assert len(payload["signups"]) == 1


def test_update_missing_signup():
    """Returns 404 when updating missing signup."""
    service = _make_service()
    payload, status = service.update("missing", {"active": False})
    assert status == 404
    assert payload["error"] == "Newsletter signup not found"


def test_update_invalid_fields():
    """Returns 400 when no valid fields are provided."""
    service = _make_service()
    service.collection.data["doc-1"] = {"email": "user@example.com"}
    payload, status = service.update("doc-1", {"foo": "bar"})
    assert status == 400
    assert payload["error"] == "No valid fields to update"


def test_update_happy_path():
    """Updates signup active flag."""
    service = _make_service()
    service.collection.data["doc-1"] = {"email": "user@example.com", "active": True}
    payload, status = service.update("doc-1", {"active": False})
    assert status == 200
    assert payload["message"]


def test_delete_missing_signup():
    """Returns 404 when deleting missing signup."""
    service = _make_service()
    payload, status = service.delete("missing")
    assert status == 404
    assert payload["error"] == "Newsletter signup not found"


def test_delete_happy_path():
    """Deletes signup successfully."""
    service = _make_service()
    service.collection.data["doc-1"] = {"email": "user@example.com"}
    payload, status = service.delete("doc-1")
    assert status == 200
    assert payload["message"]
    assert "doc-1" not in service.collection.data


def test_add_participants_invalid_input():
    """Rejects empty participant list."""
    service = _make_service()
    payload, status = service.add_participants([])
    assert status == 400
    assert payload["error"]


def test_add_participants_happy_path():
    """Adds participants with valid emails."""
    service = _make_service()
    participants = [{"email": "user@example.com"}, {"email": "invalid"}]
    payload, status = service.add_participants(participants)
    assert status == 200
    assert payload["message"]
