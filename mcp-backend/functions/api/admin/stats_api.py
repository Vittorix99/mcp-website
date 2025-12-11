import logging
from flask import jsonify
from firebase_functions import https_fn
from config.firebase_config import cors, region
from services.auth_service import require_admin
from services.stats_service import StatsService

logger = logging.getLogger("AdminStatsAPI")
stats_service = StatsService()

@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_get_general_stats(req):
    logger.info("admin_get_general_stats called")
    
    if req.method != "GET":
        return "Invalid method", 405

    try:
        response, status = stats_service.get_general_stats()
        return response, status
    except Exception as e:
        logger.exception("[admin_get_general_stats]")
        return jsonify({"error": str(e)}), 500
