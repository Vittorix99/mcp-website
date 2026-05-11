import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import public_endpoint
from dto.discount_code_dto import ValidateDiscountCodeRequestDTO
from errors.service_errors import NotFoundError
from repositories.event_repository import EventRepository
from services.payments.discount_code_service import DiscountCodeService
from utils.http_responses import handle_pydantic_error, handle_service_error


logger = logging.getLogger("DiscountCodePublicAPI")
discount_code_service = DiscountCodeService()
event_repository = EventRepository()


@public_endpoint(methods=("POST",))
def validate_discount_code(req):
    try:
        dto = ValidateDiscountCodeRequestDTO.model_validate(req.get_json(silent=True) or {})
        event = event_repository.get_model(dto.event_id)
        if not event:
            raise NotFoundError("Evento non trovato")
        payload = discount_code_service.validate_discount_code(
            event_id=dto.event_id,
            code=dto.code,
            participants_count=dto.participants_count,
            payer_email=dto.payer_email,
            payer_membership_id=dto.payer_membership_id,
            event_price=float(event.price or 0),
        )
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.exception("[validate_discount_code]")
        return handle_service_error(err)
