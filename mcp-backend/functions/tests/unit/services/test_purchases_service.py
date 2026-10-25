import pytest
from pydantic import ValidationError as PydanticValidationError

from dto.purchase import CreatePurchaseRequestDTO
from models import Purchase
from services.payments.purchases_service import PurchasesService
from errors.service_errors import NotFoundError


class _DummyPurchaseRepo:
    def __init__(self):
        self.models = []
        self.by_id = {}
        self.by_slug = {}
        self.deleted = []
        self.created = []

    def stream_models(self):
        return iter(self.models)

    def get_model(self, purchase_id):
        return self.by_id.get(purchase_id)

    def get_model_by_slug(self, slug):
        return self.by_slug.get(slug)

    def create_from_model(self, purchase):
        self.created.append(purchase)
        self.by_id["pur-1"] = purchase
        return "pur-1"

    def delete(self, purchase_id):
        if purchase_id not in self.by_id:
            return False
        self.deleted.append(purchase_id)
        return True


def _make_service():
    repository = _DummyPurchaseRepo()
    return PurchasesService(purchase_repository=repository)


def _create_request(**overrides):
    values = {
        "payer_name": "Mario",
        "payer_surname": "Rossi",
        "payer_email": "mario@example.com",
        "amount_total": "10.00",
        "currency": "EUR",
        "transaction_id": "tx-1",
        "order_id": "order-1",
        "timestamp": "2026-02-13T10:00:00Z",
    }
    values.update(overrides)
    return CreatePurchaseRequestDTO.model_validate(values)


def test_get_all_purchases():
    """Returns typed purchase response objects."""
    service = _make_service()
    purchase = Purchase(payer_name="Mario", payer_surname="Rossi")
    purchase.id = "pur-1"
    service.purchase_repository.models = [purchase]
    payload = service.get_all()
    assert payload[0].id == "pur-1"
    assert payload[0].payer_name == "Mario"


def test_get_by_id_not_found():
    with pytest.raises(NotFoundError):
        _make_service().get_by_id("pur-1")


def test_get_by_id_success():
    service = _make_service()
    purchase = Purchase(payer_name="Mario", payer_surname="Rossi")
    purchase.id = "pur-1"
    service.purchase_repository.by_id["pur-1"] = purchase
    assert service.get_by_id("pur-1").id == "pur-1"


def test_get_by_slug_success():
    service = _make_service()
    purchase = Purchase(payer_name="Mario", payer_surname="Rossi")
    purchase.id = "pur-1"
    service.purchase_repository.by_slug["slug-1"] = purchase
    assert service.get_by_id(None, slug="slug-1").id == "pur-1"


def test_create_purchase_validation_error():
    """Rejects a create request missing required schema fields."""
    with pytest.raises(PydanticValidationError):
        CreatePurchaseRequestDTO.model_validate({"payer_name": "Mario"})


def test_create_purchase_happy_path_persists_model():
    service = _make_service()
    response = service.create(_create_request(purchase_type="membership"))
    assert response.to_payload() == {"message": "Purchase created", "id": "pur-1"}
    created = service.purchase_repository.created[0]
    assert created.purchase_type.value == "membership"
    assert created.payer_email == "mario@example.com"
    assert service.purchase_repository.by_id["pur-1"] is created


def test_create_purchase_defaults_type_from_schema():
    service = _make_service()
    service.create(_create_request())
    assert service.purchase_repository.created[0].purchase_type.value == "event"


def test_create_purchase_rejects_invalid_type_in_schema():
    with pytest.raises(PydanticValidationError):
        _create_request(purchase_type="invalid-type")


def test_delete_purchase_not_found():
    with pytest.raises(NotFoundError):
        _make_service().delete("pur-1")


def test_delete_purchase_happy_path():
    service = _make_service()
    service.purchase_repository.by_id["pur-1"] = Purchase(payer_name="Mario", payer_surname="Rossi")
    response = service.delete("pur-1")
    assert response.to_payload() == {"message": "Purchase deleted", "id": "pur-1"}
    assert service.purchase_repository.deleted == ["pur-1"]
