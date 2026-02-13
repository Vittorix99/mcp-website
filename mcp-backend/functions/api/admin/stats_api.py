import logging
from flask import jsonify
from firebase_functions import https_fn
from config.firebase_config import cors, region
from services.auth_service import require_admin
from services.stats_service import StatsService
from services.service_errors import ExternalServiceError, NotFoundError, ServiceError, ValidationError

logger = logging.getLogger("AdminStatsAPI")
stats_service = StatsService()

@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_get_general_stats(req):
    logger.info("admin_get_general_stats called")
    
    if req.method != "GET":
        return "Invalid method", 405

    try:
        payload = stats_service.get_general_stats()
        return jsonify(payload), 200
    except Exception as err:
        logger.exception("[admin_get_general_stats]")
        return _handle_service_error(err)


def _handle_service_error(err: Exception):
    if isinstance(err, ValidationError):
        return jsonify({"error": str(err)}), 400
    if isinstance(err, NotFoundError):
        return jsonify({"error": str(err)}), 404
    if isinstance(err, ExternalServiceError):
        return jsonify({"error": str(err)}), 502
    if isinstance(err, ServiceError):
        return jsonify({"error": str(err)}), 500
    return jsonify({"error": "Internal server error"}), 500
