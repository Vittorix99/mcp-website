from unittest.mock import MagicMock

import repositories.newsletter_repository as newsletter_repository_module
from repositories.newsletter_repository import NewsletterRepository


class TestUnsubscribeByEmail:
    """Unit tests for NewsletterRepository.unsubscribe_by_email."""

    def _build_repo(self, signup_docs, consent_docs, monkeypatch):
        signup_collection = MagicMock()
        consent_collection = MagicMock()

        signup_collection.where.return_value.stream.return_value = signup_docs
        consent_collection.where.return_value.stream.return_value = consent_docs

        fake_db = MagicMock()

        def _collection(name):
            if name == "newsletter_signups":
                return signup_collection
            if name == "newsletter_consents":
                return consent_collection
            raise AssertionError(f"Unexpected collection: {name}")

        fake_db.collection.side_effect = _collection
        monkeypatch.setattr(newsletter_repository_module, "db", fake_db)

        repo = NewsletterRepository()
        return repo, signup_collection, consent_collection

    def test_marks_signups_inactive(self, monkeypatch):
        s1, s2 = MagicMock(), MagicMock()
        repo, signup_collection, _ = self._build_repo([s1, s2], [], monkeypatch)

        repo.unsubscribe_by_email("x@t.com")

        s1.reference.update.assert_called_once_with({"active": False})
        s2.reference.update.assert_called_once_with({"active": False})
        signup_collection.where.assert_called_once_with("email", "==", "x@t.com")

    def test_marks_consents_inactive(self, monkeypatch):
        c1 = MagicMock()
        repo, _, consent_collection = self._build_repo([], [c1], monkeypatch)

        repo.unsubscribe_by_email("x@t.com")

        c1.reference.update.assert_called_once_with({"active": False})
        consent_collection.where.assert_called_once_with("email", "==", "x@t.com")

    def test_no_matching_docs_no_error(self, monkeypatch):
        repo, _, _ = self._build_repo([], [], monkeypatch)

        repo.unsubscribe_by_email("x@t.com")

    def test_both_collections_updated(self, monkeypatch):
        s1 = MagicMock()
        c1 = MagicMock()
        repo, signup_collection, consent_collection = self._build_repo([s1], [c1], monkeypatch)

        repo.unsubscribe_by_email("x@t.com")

        s1.reference.update.assert_called_once_with({"active": False})
        c1.reference.update.assert_called_once_with({"active": False})
        signup_collection.where.assert_called_once_with("email", "==", "x@t.com")
        consent_collection.where.assert_called_once_with("email", "==", "x@t.com")

    def test_email_query_correct(self, monkeypatch):
        repo, signup_collection, consent_collection = self._build_repo([], [], monkeypatch)

        repo.unsubscribe_by_email("query@test.com")

        signup_collection.where.assert_called_once_with("email", "==", "query@test.com")
        consent_collection.where.assert_called_once_with("email", "==", "query@test.com")
