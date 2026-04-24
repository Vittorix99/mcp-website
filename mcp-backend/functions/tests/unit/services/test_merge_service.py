from types import SimpleNamespace

import pytest

from models import Membership
from services.memberships.merge_service import MergeService
from errors.service_errors import NotFoundError, ValidationError


class _DummyMembershipRepo:
    def __init__(self):
        self.models = {}
        self.deleted = []
        self.updated_calls = []

    def get(self, membership_id):
        return self.models.get(membership_id)

    def update_fields(self, membership_id, payload):
        self.updated_calls.append((membership_id, payload))
        model = self.models.get(membership_id)
        if not model:
            return False
        for key, value in payload.items():
            if hasattr(model, key):
                try:
                    from google.cloud.firestore_v1 import DELETE_FIELD
                    if value is DELETE_FIELD:
                        setattr(model, key, None)
                        continue
                except Exception:
                    pass
                setattr(model, key, value)
        return True

    def delete(self, membership_id):
        self.deleted.append(membership_id)
        self.models.pop(membership_id, None)


class _DummyParticipantRepo:
    def __init__(self, updated=0):
        self.updated = updated
        self.calls = []

    def update_membership_reference(self, old_membership_id, new_membership_id):
        self.calls.append((old_membership_id, new_membership_id))
        return self.updated


def _membership(**kwargs):
    defaults = dict(
        name="Mario",
        surname="Rossi",
        email="mario@example.com",
        phone="+390000000000",
        birthdate="01-01-1990",
        start_date="2026-01-01T10:00:00+00:00",
        end_date="31-12-2026",
        subscription_valid=True,
        membership_sent=True,
        membership_type="manual",
        purchases=[],
        attended_events=[],
        renewals=[],
        membership_years=[],
    )
    defaults.update(kwargs)
    return Membership(**defaults)


def test_merge_combines_memberships_and_relinks_participants(monkeypatch):
    membership_repo = _DummyMembershipRepo()
    participant_repo = _DummyParticipantRepo(updated=3)
    service = MergeService(membership_repository=membership_repo, participant_repository=participant_repo)

    source = _membership(
        email="source@example.com",
        purchases=["p1"],
        attended_events=["e1"],
        renewals=[{"year": 2025, "start_date": "2025-01-01T10:00:00+00:00", "end_date": "31-12-2025", "purchase_id": "p1", "fee": 15.0}],
        membership_years=[2025],
        wallet_pass_id="old-pass",
        wallet_url="https://wallet.old",
    )
    source.id = "source-1"

    target = _membership(
        email="target@example.com",
        purchases=["p2"],
        attended_events=["e2"],
        renewals=[{"year": 2026, "start_date": "2026-01-01T10:00:00+00:00", "end_date": "31-12-2026", "purchase_id": "p2", "fee": 15.0}],
        membership_years=[2026],
        wallet_pass_id="target-old-pass",
        wallet_url="https://wallet.target.old",
    )
    target.id = "target-1"

    membership_repo.models[source.id] = source
    membership_repo.models[target.id] = target

    invalidated = []
    created = []

    class _Pass2UStub:
        def invalidate_membership_pass(self, pass_id):
            invalidated.append(pass_id)
            return True

        def create_membership_pass(self, membership_id, membership):
            created.append((membership_id, membership.email))
            return SimpleNamespace(pass_id="new-pass", wallet_url="https://wallet.new")

    monkeypatch.setattr("services.memberships.pass2u_service.Pass2UService", _Pass2UStub)

    result = service.merge("source-1", "target-1")

    assert result["participants_updated"] == 3
    assert participant_repo.calls == [("source-1", "target-1")]
    assert invalidated == ["old-pass"]
    assert created == [("target-1", "target@example.com")]
    assert "source-1" in membership_repo.deleted

    merged_target = membership_repo.models["target-1"]
    assert sorted(merged_target.purchases) == ["p1", "p2"]
    assert sorted(merged_target.attended_events) == ["e1", "e2"]
    assert merged_target.membership_years == [2025, 2026]
    assert merged_target.wallet_pass_id == "new-pass"
    assert merged_target.wallet_url == "https://wallet.new"


def test_merge_rejects_same_membership_id():
    service = MergeService(membership_repository=_DummyMembershipRepo(), participant_repository=_DummyParticipantRepo())
    with pytest.raises(ValidationError):
        service.merge("same-id", "same-id")


def test_merge_requires_existing_source_and_target():
    service = MergeService(membership_repository=_DummyMembershipRepo(), participant_repository=_DummyParticipantRepo())
    with pytest.raises(NotFoundError):
        service.merge("missing-source", "target")
