import pytest

from dto import PurchaseDTO
from models import Purchase
from services.purchases_service import PurchasesService
from services.service_errors import NotFoundError, ValidationError


class _DummyPurchaseRepo:
    def __init__(self):
        self.models = []
        self.by_id = {}
        self.by_slug = {}
        self.deleted = []

    def stream_models(self):
        return iter(self.models)

    def get_model(self, purchase_id):
        return self.by_id.get(purchase_id)

    def get_model_by_slug(self, slug):
        return self.by_slug.get(slug)

    def create_from_model(self, purchase):
        self.by_id["pur-1"] = purchase
        return "pur-1"

    def delete(self, purchase_id):
        if purchase_id not in self.by_id:
            return False
        self.deleted.append(purchase_id)
        return True


def _make_service():
    service = PurchasesService()
    service.purchase_repository = _DummyPurchaseRepo()
    return service


def test_get_all_purchases():
    """Returns serialized purchases list."""
    service = _make_service()
    purchase = Purchase(payer_name="Mario", payer_surname="Rossi")
    purchase.id = "pur-1"
    service.purchase_repository.models = [purchase]
    payload = service.get_all()
    assert payload[0]["id"] == "pur-1"
    assert payload[0]["payer_name"] == "Mario"


def test_get_by_id_not_found():
    """Raises when purchase is missing."""
    service = _make_service()
    with pytest.raises(NotFoundError):
        service.get_by_id("pur-1")


def test_get_by_slug_success():
    """Fetches purchase by slug."""
    service = _make_service()
    purchase = Purchase(payer_name="Mario", payer_surname="Rossi")
    purchase.id = "pur-1"
    service.purchase_repository.by_slug["slug-1"] = purchase
    payload = service.get_by_id(None, slug="slug-1")
    assert payload["id"] == "pur-1"


def test_create_purchase_validation_error():
    """Rejects missing required fields."""
    service = _make_service()
    dto = PurchaseDTO(payer_name="Mario")
    with pytest.raises(ValidationError):
        service.create(dto)


def test_create_purchase_happy_path():
    """Creates purchase successfully."""
    service = _make_service()
    dto = PurchaseDTO(
        payer_name="Mario",
        payer_surname="Rossi",
        payer_email="mario@example.com",
        amount_total="10.00",
        currency="EUR",
        transaction_id="tx-1",
        order_id="order-1",
        timestamp="2026-02-13T10:00:00Z",
        type="event",
    )
    payload = service.create(dto)
    assert payload["id"] == "pur-1"


def test_delete_purchase_not_found():
    """Raises when delete target is missing."""
    service = _make_service()
    with pytest.raises(NotFoundError):
        service.delete("pur-1")


def test_delete_purchase_happy_path():
    """Deletes purchase successfully."""
    service = _make_service()
    service.purchase_repository.by_id["pur-1"] = Purchase(payer_name="Mario", payer_surname="Rossi")
    payload = service.delete("pur-1")
    assert payload["message"]
