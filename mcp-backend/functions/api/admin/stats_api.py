import logging

from flask import jsonify

from api.decorators import admin_endpoint
from services.core.stats_service import StatsService
from utils.http_responses import handle_service_error

logger = logging.getLogger("AdminStatsAPI")
stats_service = StatsService()


@admin_endpoint(methods=("GET",))
def admin_get_general_stats(req):
    try:
        payload = stats_service.get_general_stats()
        return jsonify(payload), 200
    except Exception as err:
        logger.exception("[admin_get_general_stats]")
        return handle_service_error(err)
