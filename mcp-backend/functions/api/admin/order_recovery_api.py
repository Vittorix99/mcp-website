from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.preorder import OrderCaptureDTO
from services.payments.event_order_recovery_service import EventOrderRecoveryService
from utils.http_responses import handle_pydantic_error, handle_service_error


recovery_service = EventOrderRecoveryService()


@admin_endpoint(methods=('POST',))
def recover_order_event(req):
    try:
        dto = OrderCaptureDTO.model_validate(req.get_json(silent=True) or {})
        result = recovery_service.recover_order(dto.order_id)
        return jsonify(result.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
