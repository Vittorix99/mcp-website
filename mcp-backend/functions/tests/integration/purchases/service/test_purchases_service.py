import pytest

from dto import PurchaseDTO
from services.service_errors import NotFoundError, ValidationError


@pytest.mark.integration
def test_purchases_service_crud(purchases_service, purchase_repository, purchase_dto):
    """Creates, fetches, lists, and deletes purchases via the service layer."""
    purchase_id = None
    try:
        created = purchases_service.create(purchase_dto)
        purchase_id = created.get("id")
        assert purchase_id

        fetched = purchases_service.get_by_id(purchase_id)
        assert fetched.get("id") == purchase_id
        assert fetched.get("payer_email") == purchase_dto.payer_email

        all_purchases = purchases_service.get_all()
        assert any(item.get("id") == purchase_id for item in all_purchases)
    finally:
        if purchase_id:
            purchases_service.delete(purchase_id)


@pytest.mark.integration
def test_purchases_service_missing_fields_rejected(purchases_service):
    """Rejects creation when required fields are missing."""
    with pytest.raises(ValidationError):
        purchases_service.create(PurchaseDTO.from_payload({}))


@pytest.mark.integration
def test_purchases_service_not_found(purchases_service):
    """Raises NotFoundError when purchase is missing."""
    with pytest.raises(NotFoundError):
        purchases_service.get_by_id("missing-id")
