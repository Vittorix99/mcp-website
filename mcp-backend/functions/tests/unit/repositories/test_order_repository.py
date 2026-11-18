"""Repository guards offline; real transaction contention is covered by PAY-12."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from google.api_core.exceptions import Aborted, FailedPrecondition
import pytest

import repositories.order_repository as module
from errors.service_errors import ConflictError, NotFoundError
from repositories.order_repository import OrderRepository


@pytest.fixture
def capture_repository(monkeypatch):
    doc = MagicMock()
    repo = OrderRepository()
    repo.collection = MagicMock()
    repo.collection.document.return_value = doc
    client = MagicMock()
    client.write_option.side_effect = lambda **kw: ('precondition', kw['last_update_time'])
    monkeypatch.setattr(module, 'db', client, raising=False)
    return repo, doc


def _snapshot(data, update_time='t1', exists=True):
    return SimpleNamespace(exists=exists, to_dict=lambda: data, update_time=update_time)


def test_mark_captured_writes_only_if_order_is_unchanged_since_it_was_read(capture_repository):
    repo, doc = capture_repository
    doc.get.return_value = _snapshot({'captured': False}, update_time='t1')

    repo.mark_captured('order-1', 'paypal')

    doc.update.assert_called_once_with({
        'captured': True, 'payment_method': 'paypal', 'orderStatus': 'PAYMENT_CAPTURED',
    }, option=('precondition', 't1'))


@pytest.mark.parametrize('status,purchase_id', [
    ('PAYMENT_CAPTURED', None), ('PURCHASE_CREATED', 'purchase-1'), ('COMPLETED', 'purchase-1'),
])
def test_mark_captured_rejects_previously_recorded_capture_without_writes(
        capture_repository, status, purchase_id):
    repo, doc = capture_repository
    doc.get.return_value = _snapshot({
        'captured': True, 'orderStatus': status, 'purchase_id': purchase_id,
    })

    with pytest.raises(ConflictError) as caught:
        repo.mark_captured('order-1', 'paypal')

    assert caught.value.payload == {
        'code': 'ORDER_CAPTURE_CONFLICT', 'order_id': 'order-1', 'purchase_id': purchase_id,
    }
    doc.update.assert_not_called()


def test_mark_captured_missing_order_does_not_write(capture_repository):
    repo, doc = capture_repository
    doc.get.return_value = _snapshot(None, exists=False)

    with pytest.raises(NotFoundError):
        repo.mark_captured('missing', 'paypal')

    doc.update.assert_not_called()


def test_losing_the_race_reports_the_winners_capture_as_a_conflict(capture_repository):
    repo, doc = capture_repository
    doc.get.side_effect = [_snapshot({'captured': False}),
                           _snapshot({'captured': True, 'purchase_id': 'purchase-9'})]
    doc.update.side_effect = FailedPrecondition('changed')

    with pytest.raises(ConflictError) as caught:
        repo.mark_captured('order-1', 'paypal')

    assert caught.value.payload['purchase_id'] == 'purchase-9'
    assert doc.update.call_count == 1


def test_unrelated_concurrent_change_is_retried_then_claimed(capture_repository):
    repo, doc = capture_repository
    doc.get.side_effect = [_snapshot({'captured': False}, 't1'), _snapshot({'captured': False}, 't2')]
    doc.update.side_effect = [FailedPrecondition('status updated'), None]

    repo.mark_captured('order-1', 'paypal')

    assert doc.update.call_args.kwargs['option'] == ('precondition', 't2')


def test_persistent_interference_ends_in_a_conflict_without_claiming(capture_repository):
    repo, doc = capture_repository
    doc.get.return_value = _snapshot({'captured': False})
    doc.update.side_effect = FailedPrecondition('changed')

    with pytest.raises(ConflictError) as caught:
        repo.mark_captured('order-1', 'paypal')

    assert caught.value.payload == {'code': 'ORDER_CAPTURE_RETRY', 'order_id': 'order-1'}
    assert doc.update.call_count == 3


def test_aborted_write_is_retried_like_a_failed_precondition(capture_repository):
    repo, doc = capture_repository
    doc.get.return_value = _snapshot({'captured': False})
    doc.update.side_effect = [Aborted('contention'), None]

    repo.mark_captured('order-1', 'paypal')

    assert doc.update.call_count == 2


def test_linking_same_purchase_never_regresses_completed_order(capture_repository):
    repo, doc = capture_repository
    doc.get.return_value = _snapshot({'captured': True, 'orderStatus': 'COMPLETED', 'purchase_id': 'p'})
    repo.set_purchase_id('order-1', 'p')
    doc.update.assert_not_called()


def test_linking_a_different_purchase_is_rejected(capture_repository):
    repo, doc = capture_repository
    doc.get.return_value = _snapshot({'captured': True, 'purchase_id': 'other'})
    with pytest.raises(ConflictError):
        repo.set_purchase_id('order-1', 'p')
    doc.update.assert_not_called()


def test_capture_start_is_written_with_version_precondition(capture_repository):
    repo, doc = capture_repository
    doc.get.return_value = _snapshot({'captured': False, 'captureStarted': False}, 't1')
    repo.mark_capture_started('order-1')
    doc.update.assert_called_once_with({'captureStarted': True}, option=('precondition', 't1'))


def test_repeated_capture_start_does_not_overwrite_a_payment(capture_repository):
    repo, doc = capture_repository
    doc.get.return_value = _snapshot({'captured': False, 'captureStarted': True})
    repo.mark_capture_started('order-1')
    doc.update.assert_not_called()
    doc.get.return_value = _snapshot({'captured': True})
    with pytest.raises(ConflictError):
        repo.mark_capture_started('order-1')
    doc.update.assert_not_called()


def test_deleted_order_cannot_start_capture(capture_repository):
    repo, doc = capture_repository
    doc.get.return_value = _snapshot({}, exists=False)
    with pytest.raises(NotFoundError):
        repo.mark_capture_started('order-1')
    doc.update.assert_not_called()


@pytest.mark.parametrize('error', [FailedPrecondition, Aborted])
def test_capture_start_cas_rechecks_a_concurrent_start(capture_repository, error):
    repo, doc = capture_repository
    doc.get.side_effect = [_snapshot({'captured': False, 'captureStarted': False}),
                           _snapshot({'captured': False, 'captureStarted': True}, 't2')]
    doc.update.side_effect = error('Changed')
    repo.mark_capture_started('order-1')
    assert doc.update.call_count == 1


def test_capture_start_persistent_contention_stops_before_provider(capture_repository):
    repo, doc = capture_repository
    doc.get.return_value = _snapshot({'captured': False, 'captureStarted': False})
    doc.update.side_effect = FailedPrecondition('Changed')
    with pytest.raises(ConflictError):
        repo.mark_capture_started('order-1')
    assert doc.update.call_count == 3
