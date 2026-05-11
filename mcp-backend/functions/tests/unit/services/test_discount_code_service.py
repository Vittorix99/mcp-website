import pytest

from errors.service_errors import ValidationError
from models import DiscountCode, DiscountType, Membership
from services.payments.discount_code_service import DiscountCodeService


class _DiscountCodeRepo:
    def __init__(self, model=None):
        self.model = model

    def get_by_code_and_event(self, code, event_id):
        if self.model and self.model.code == code and self.model.event_id == event_id:
            return self.model
        return None


class _MembershipRepo:
    def __init__(self, model=None):
        self.model = model

    def get(self, membership_id):
        if self.model and self.model.id == membership_id:
            return self.model
        return None


def _service(discount_code=None, membership=None):
    return DiscountCodeService(
        discount_code_repository=_DiscountCodeRepo(discount_code),
        membership_repository=_MembershipRepo(membership),
    )


def test_apply_discount_percentage():
    result = _service().apply_discount(20, "PERCENTAGE", 50)
    assert result == {"final_price": 10.0, "discount_amount": 10.0}


def test_apply_discount_fixed_rejects_negative_final_price():
    with pytest.raises(ValidationError):
        _service().apply_discount(20, "FIXED", 25)


def test_apply_discount_fixed_price_sets_final_price():
    result = _service().apply_discount(25, "FIXED_PRICE", 10)
    assert result == {"final_price": 10.0, "discount_amount": 15.0}


def test_apply_discount_fixed_price_rejects_price_above_original():
    with pytest.raises(ValidationError):
        _service().apply_discount(8, "FIXED_PRICE", 10)


def test_validate_discount_code_rejects_multi_participant_purchase():
    discount_code = DiscountCode(
        id="disc-1",
        event_id="evt-1",
        code="MCP50",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=50,
        max_uses=5,
        used_count=0,
        is_active=True,
    )
    result = _service(discount_code).validate_discount_code(
        event_id="evt-1",
        code="mcp50",
        participants_count=2,
        payer_email="user@example.com",
        event_price=20,
    )
    assert result.valid is False
    assert result.error_message == "Il codice sconto è valido solo per acquisti singoli"


def test_validate_membership_restriction_uses_membership_email():
    discount_code = DiscountCode(
        id="disc-1",
        event_id="evt-1",
        code="MEMBER",
        discount_type=DiscountType.FIXED_PRICE,
        discount_value=10,
        max_uses=5,
        used_count=0,
        is_active=True,
        restricted_membership_id="mem-1",
    )
    membership = Membership(id="mem-1", email="member@example.com")
    result = _service(discount_code, membership).validate_discount_code(
        event_id="evt-1",
        code="member",
        participants_count=1,
        payer_email="member@example.com",
        payer_membership_id="mem-1",
        event_price=25,
    )
    assert result.valid is True
    assert result.discount_amount == 15.0
