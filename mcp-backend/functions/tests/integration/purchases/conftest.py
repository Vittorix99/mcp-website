from datetime import datetime, timezone
from uuid import uuid4

import pytest

from dto.purchase import CreatePurchaseRequestDTO
from repositories.purchase_repository import PurchaseRepository
from services.payments.purchases_service import PurchasesService


@pytest.fixture
def purchases_service():
    return PurchasesService()


@pytest.fixture
def purchase_repository():
    return PurchaseRepository()


@pytest.fixture
def purchase_payload():
    suffix = uuid4().hex[:8]
    return {
        "payer_name": "Mario",
        "payer_surname": "Rossi",
        "payer_email": f"mcpweb.testing+purchase_{suffix}@gmail.com",
        "amount_total": "10.00",
        "currency": "EUR",
        "transaction_id": f"txn-{suffix}",
        "order_id": f"order-{suffix}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "event",
        "ref_id": f"event-{suffix}",
        "payment_method": "website",
        "capture_status": "COMPLETED",
    }


@pytest.fixture
def purchase_dto(purchase_payload):
    return CreatePurchaseRequestDTO.model_validate(purchase_payload)
