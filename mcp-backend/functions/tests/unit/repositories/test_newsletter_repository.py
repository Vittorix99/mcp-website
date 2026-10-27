from unittest.mock import MagicMock

import repositories.newsletter_repository as newsletter_repository_module
from repositories.newsletter_repository import NewsletterRepository


def _build_repo(signup_docs=(), consent_docs=(), monkeypatch=None):
    signup_collection = MagicMock()
    consent_collection = MagicMock()
    participants_collection = MagicMock()
    signup_collection.where.return_value.stream.return_value = signup_docs
    consent_collection.where.return_value.stream.return_value = consent_docs

    fake_db = MagicMock()
    collections = {
        "newsletter_signups": signup_collection,
        "newsletter_consents": consent_collection,
        "newsletter_participants": participants_collection,
    }
    fake_db.collection.side_effect = lambda name: collections[name]
    monkeypatch.setattr(newsletter_repository_module, "db", fake_db)

    return NewsletterRepository(), signup_collection, consent_collection


def _assert_email_filter(collection, email):
    collection.where.assert_called_once()
    kwargs = collection.where.call_args.kwargs
    assert set(kwargs) == {"filter"}
    filter_ = kwargs["filter"]
    assert filter_.field_path == "email"
    assert filter_.op_string == "=="
    assert filter_.value == email


def test_unsubscribe_marks_matching_signups_inactive(monkeypatch):
    signup = MagicMock()
    repo, signup_collection, _ = _build_repo([signup], monkeypatch=monkeypatch)

    repo.unsubscribe_by_email("x@example.com")

    signup.reference.update.assert_called_once_with({"active": False})
    _assert_email_filter(signup_collection, "x@example.com")


def test_unsubscribe_marks_matching_consents_inactive(monkeypatch):
    consent = MagicMock()
    repo, _, consent_collection = _build_repo(consent_docs=[consent], monkeypatch=monkeypatch)

    repo.unsubscribe_by_email("x@example.com")

    consent.reference.update.assert_called_once_with({"active": False})
    _assert_email_filter(consent_collection, "x@example.com")


def test_unsubscribe_with_no_matches_is_a_noop(monkeypatch):
    repo, signup_collection, consent_collection = _build_repo(monkeypatch=monkeypatch)

    repo.unsubscribe_by_email("x@example.com")

    _assert_email_filter(signup_collection, "x@example.com")
    _assert_email_filter(consent_collection, "x@example.com")


def test_unsubscribe_updates_both_collections(monkeypatch):
    signup, consent = MagicMock(), MagicMock()
    repo, signup_collection, consent_collection = _build_repo(
        signup_docs=[signup], consent_docs=[consent], monkeypatch=monkeypatch
    )

    repo.unsubscribe_by_email("query@example.com")

    signup.reference.update.assert_called_once_with({"active": False})
    consent.reference.update.assert_called_once_with({"active": False})
    _assert_email_filter(signup_collection, "query@example.com")
    _assert_email_filter(consent_collection, "query@example.com")
