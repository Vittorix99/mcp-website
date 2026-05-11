import pytest
from pydantic import ValidationError as PydanticValidationError

from dto.purchase import CreatePurchaseRequestDTO, UpdatePurchaseStatusRequestDTO
from errors.service_errors import NotFoundError
from models import PurchaseStatus


@pytest.mark.integration
def test_purchases_service_crud(purchases_service, purchase_repository, purchase_dto):
    """Creates, fetches, lists, and deletes purchases via the service layer."""
    purchase_id = None
    try:
        created = purchases_service.create(purchase_dto)
        purchase_id = created.id
        assert purchase_id

        fetched = purchases_service.get_by_id(purchase_id)
        assert fetched.id == purchase_id
        assert fetched.payer_email == purchase_dto.payer_email

        all_purchases = purchases_service.get_all()
        assert any(item.id == purchase_id for item in all_purchases)
    finally:
        if purchase_id:
            purchases_service.delete(purchase_id)


@pytest.mark.integration
def test_purchases_service_missing_fields_rejected(purchases_service):
    """Rejects creation when required fields are missing."""
    with pytest.raises(PydanticValidationError):
        purchases_service.create(CreatePurchaseRequestDTO.model_validate({}))


@pytest.mark.integration
def test_purchases_service_not_found(purchases_service):
    """Raises NotFoundError when purchase is missing."""
    with pytest.raises(NotFoundError):
        purchases_service.get_by_id("missing-id")


@pytest.mark.integration
def test_purchases_service_update_status(purchases_service, purchase_repository, purchase_dto):
    """Updates purchase status through the service layer."""
    purchase_id = None
    try:
        created = purchases_service.create(purchase_dto)
        purchase_id = created.id
        assert purchase_id

        result = purchases_service.update_status(
            UpdatePurchaseStatusRequestDTO(
                purchase_id=purchase_id,
                status=PurchaseStatus.CANCELLED,
            )
        )
        assert result.id == purchase_id
        assert result.message == "Status updated"

        updated = purchase_repository.get_model(purchase_id)
        assert updated is not None
        assert updated.status == PurchaseStatus.CANCELLED.value
    finally:
        if purchase_id:
            purchases_service.delete(purchase_id)


@pytest.mark.integration
def test_purchases_service_update_status_not_found(purchases_service):
    """Raises NotFoundError when updating a missing purchase status."""
    with pytest.raises(NotFoundError):
        purchases_service.update_status(
            UpdatePurchaseStatusRequestDTO(
                purchase_id="missing-id",
                status=PurchaseStatus.REFUNDED,
            )
        )
