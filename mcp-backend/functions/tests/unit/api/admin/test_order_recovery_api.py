from types import SimpleNamespace

import pytest

from dto.preorder import OrderCaptureResponseDTO
from services.core import auth_service
from tests.utils import DummyRequest, unwrap_response


def call_api(request):
    from api.admin.order_recovery_api import recover_order_event
    return unwrap_response(recover_order_event(request))


def test_recovery_requires_admin_and_never_calls_service_without_it(monkeypatch):
    from api.admin import order_recovery_api
    monkeypatch.setattr(order_recovery_api, 'recovery_service', SimpleNamespace(
        recover_order=lambda _: pytest.fail('Unauthenticated recovery executed')))
    request = DummyRequest(method='POST', json={'order_id': 'o'})
    request.headers = {}
    _, status = call_api(request)
    assert status == 401
    monkeypatch.setattr(auth_service.auth, 'verify_id_token', lambda _: {'uid': 'member', 'admin': False})
    _, status = call_api(DummyRequest(method='POST', json={'order_id': 'o'}))
    assert status == 401


@pytest.mark.parametrize('method,body,status', [('GET', {'order_id': 'o'}, 405), ('POST', {}, 400)])
def test_recovery_validates_method_and_order_dto(method, body, status):
    _, actual = call_api(DummyRequest(method=method, json=body))
    assert actual == status


def test_admin_recovery_returns_purchase(monkeypatch):
    from api.admin import order_recovery_api
    orders = []
    def recover(order_id):
        orders.append(order_id)
        return OrderCaptureResponseDTO(message='Recovered', purchase_id='p', payment_method='paypal')
    monkeypatch.setattr(order_recovery_api, 'recovery_service', SimpleNamespace(recover_order=recover))
    body, status = call_api(DummyRequest(method='POST', json={'order_id': 'o'}))
    assert status == 200 and body['purchase_id'] == 'p'
    assert orders == ['o']
