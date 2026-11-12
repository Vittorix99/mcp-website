from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from google.api_core.exceptions import AlreadyExists

from errors.service_errors import ConflictError
from models import EventPurchase, EventParticipant
from repositories.purchase_repository import PurchaseRepository
from repositories.participant_repository import ParticipantRepository


def snapshot(model, identifier='existing'):
    return SimpleNamespace(id=identifier, exists=True, to_dict=lambda: model.to_firestore())


@pytest.mark.parametrize('existing', [False, True])
def test_event_purchase_create_reuses_one_order_and_never_overwrites(existing):
    repo = PurchaseRepository()
    repo.collection = MagicMock()
    query = repo.collection.where.return_value.limit.return_value
    purchase = EventPurchase(order_id='o', transaction_id='c', event_id='e', ref_id='e',
                             amount_total='12.00', currency='EUR', status='COMPLETED')
    query.get.return_value = [snapshot(purchase)] if existing else []
    ref = repo.collection.document.return_value
    ref.id = 'stable'
    if existing:
        assert repo.create_for_order(purchase) == 'existing'
        ref.create.assert_not_called()
    else:
        assert repo.create_for_order(purchase) == 'stable'
        first_key = repo.collection.document.call_args.args[0]
        ref.create.side_effect = AlreadyExists('Created by another caller')
        ref.get.return_value = snapshot(purchase)
        assert repo.create_for_order(purchase) == 'existing'
        assert repo.collection.document.call_args.args[0] == first_key
    ref.set.assert_not_called()


def test_duplicate_legacy_purchases_require_manual_resolution():
    repo = PurchaseRepository()
    repo.collection = MagicMock()
    repo.collection.where.return_value.limit.return_value.get.return_value = [object(), object()]
    with pytest.raises(ConflictError):
        repo.find_by_order('o')


def test_purchase_from_another_capture_is_not_reused():
    repo = PurchaseRepository()
    repo.collection = MagicMock()
    existing = EventPurchase(order_id='o', transaction_id='other')
    repo.collection.where.return_value.limit.return_value.get.return_value = [snapshot(existing)]
    with pytest.raises(ConflictError):
        repo.create_for_order(EventPurchase(order_id='o', transaction_id='c'))
    repo.collection.document.return_value.create.assert_not_called()


def test_checkout_participant_create_race_reuses_record_without_resetting_ticket_state(monkeypatch):
    repo = ParticipantRepository()
    repo.base_collection = MagicMock()
    collection = repo.base_collection.document.return_value.collection.return_value
    collection.where.return_value.stream.return_value = []
    participant = EventParticipant(event_id='e', purchase_id='p', email='a@example.test', price=10)
    existing = EventParticipant(event_id='e', purchase_id='p', email='a@example.test', price=10,
                                entered=True, ticket_sent=True)
    ref = collection.document.return_value
    client = MagicMock()
    hold = client.collection.return_value.document.return_value.collection.return_value.document.return_value
    hold.get.return_value = SimpleNamespace(exists=True, reference=hold, update_time='h1',
        to_dict=lambda: {'state': 'capturing', 'purchaseId': 'p'})
    monkeypatch.setattr('repositories.participant_repository.db', client)
    batch = client.batch.return_value
    batch.commit.side_effect = AlreadyExists('Created concurrently')
    ref.get.return_value = snapshot(existing)
    assert repo.create_for_purchase('e', participant, capacity_reservation_id='hold-1') == 'existing'
    ref.set.assert_not_called()


def test_legacy_participant_is_reused_but_changed_price_is_a_conflict():
    repo = ParticipantRepository()
    repo.base_collection = MagicMock()
    collection = repo.base_collection.document.return_value.collection.return_value
    existing = EventParticipant(event_id='e', purchase_id='p', email='a@example.test', price=10)
    collection.where.return_value.stream.return_value = [snapshot(existing)]
    assert repo.create_for_purchase('e', existing) == 'existing'
    with pytest.raises(ConflictError):
        repo.create_for_purchase('e', EventParticipant(event_id='e', purchase_id='p', email=existing.email, price=11))
    collection.document.return_value.create.assert_not_called()


def test_inconsistent_stored_checkout_position_requires_manual_verification():
    existing = EventParticipant(event_id='e', purchase_id='p', email='a@example.test', price=10)
    expected = EventParticipant(event_id='e', purchase_id='p', email='a@example.test', price=10)
    existing.checkout_index = 1
    expected.checkout_index = 0
    with pytest.raises(ConflictError):
        ParticipantRepository.assert_same_checkout(existing, expected)


@pytest.mark.parametrize('field,value', [
    ('timestamp', '2026-05-01T10:00:00Z'), ('payment_method', 'apple_pay'),
    ('payer_email', 'another@example.test'), ('payer_name', 'Other'), ('payer_surname', 'Other'),
])
def test_altered_legacy_capture_metadata_cannot_be_reused(field, value):
    from copy import deepcopy
    expected = EventPurchase(order_id='o', transaction_id='c', event_id='e', ref_id='e',
        amount_total='12.00', currency='EUR', status='COMPLETED', timestamp='2026-04-01T10:00:00Z',
        payment_method='paypal', payer_email='payer@example.test', payer_name='Mario', payer_surname='Rossi')
    existing = deepcopy(expected)
    setattr(existing, field, value)
    with pytest.raises(ConflictError):
        PurchaseRepository.assert_same_checkout(existing, expected)


def test_equivalent_capture_timestamp_timezones_preserve_legacy_identity():
    from copy import deepcopy
    expected = EventPurchase(order_id='o', transaction_id='c', timestamp='2026-04-01T10:00:00Z')
    existing = deepcopy(expected)
    existing.timestamp = '2026-04-01T12:00:00+02:00'
    PurchaseRepository.assert_same_checkout(existing, expected)
