import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.analytics_api import EventAnalyticsQueryDTO, MembershipTrendQueryDTO
from dto.stats_api import EventSnapshotQueryDTO, RebuildAnalyticsRequestDTO
from services.core.analytics_service import AnalyticsService
from services.core.analytics_snapshot_service import AnalyticsSnapshotService
from services.core.stats_service import StatsService
from utils.http_responses import handle_pydantic_error, handle_service_error
from utils.safe_logging import redact_sensitive

logger = logging.getLogger("AdminStatsAPI")
stats_service = StatsService()
analytics_snapshot_service = AnalyticsSnapshotService()
analytics_service = AnalyticsService()


@admin_endpoint(methods=("GET",))
def admin_get_general_stats(req):
    try:
        payload = stats_service.get_general_stats()
        return jsonify(payload), 200
    except Exception as err:
        logger.error("[admin_get_general_stats] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_dashboard_snapshot(req):
    try:
        payload = analytics_snapshot_service.get_dashboard_snapshot()
        return jsonify(payload), 200
    except Exception as err:
        logger.error("[admin_get_dashboard_snapshot] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_analytics_event_snapshot(req):
    try:
        dto = EventSnapshotQueryDTO.model_validate(dict(req.args or {}))
        payload = analytics_snapshot_service.get_event_snapshot(dto.event_id)
        return jsonify(payload), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_get_analytics_event_snapshot] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_analytics_global_snapshot(req):
    try:
        payload = analytics_snapshot_service.get_global_snapshot()
        return jsonify(payload), 200
    except Exception as err:
        logger.error("[admin_get_analytics_global_snapshot] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_analytics_events_index(req):
    try:
        payload = analytics_snapshot_service.get_events_index()
        return jsonify(payload), 200
    except Exception as err:
        logger.error("[admin_get_analytics_events_index] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_entrance_flow(req):
    try:
        dto = EventAnalyticsQueryDTO.model_validate(dict(req.args or {}))
        result = analytics_service.get_entrance_flow(
            dto.event_id,
            start_time=dto.start_time,
            span_hours=dto.span_hours,
            bucket_minutes=dto.bucket_minutes,
        )
        return jsonify(result.model_dump(by_alias=True)), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_get_entrance_flow] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_sales_over_time(req):
    try:
        dto = EventAnalyticsQueryDTO.model_validate(dict(req.args or {}))
        result = analytics_service.get_sales_over_time(dto.event_id)
        return jsonify(result.model_dump(by_alias=True)), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_get_sales_over_time] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_audience_retention(req):
    try:
        dto = EventAnalyticsQueryDTO.model_validate(dict(req.args or {}))
        result = analytics_service.get_audience_retention(dto.event_id)
        return jsonify(result.model_dump(by_alias=True)), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_get_audience_retention] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_revenue_breakdown(req):
    try:
        dto = EventAnalyticsQueryDTO.model_validate(dict(req.args or {}))
        result = analytics_service.get_revenue_breakdown(dto.event_id)
        return jsonify(result.model_dump(by_alias=True)), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_get_revenue_breakdown] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_event_funnel(req):
    try:
        dto = EventAnalyticsQueryDTO.model_validate(dict(req.args or {}))
        result = analytics_service.get_event_funnel(dto.event_id)
        return jsonify(result.model_dump(by_alias=True)), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_get_event_funnel] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_gender_distribution(req):
    try:
        dto = EventAnalyticsQueryDTO.model_validate(dict(req.args or {}))
        result = analytics_service.get_gender_distribution(dto.event_id)
        return jsonify(result.model_dump(by_alias=True)), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_get_gender_distribution] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_membership_trend(req):
    try:
        dto = MembershipTrendQueryDTO.model_validate(dict(req.args or {}))
        result = analytics_service.get_membership_trend(dto.year)
        return jsonify(result.model_dump(by_alias=True)), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_get_membership_trend] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_dashboard_kpis(req):
    try:
        result = analytics_service.get_dashboard_kpis()
        return jsonify(result.model_dump(by_alias=True)), 200
    except Exception as err:
        logger.error("[admin_get_dashboard_kpis] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def admin_rebuild_analytics(req):
    try:
        dto = RebuildAnalyticsRequestDTO.model_validate(req.get_json(silent=True) or {})
        requested_by = (req.admin_token or {}).get("uid", "admin") if hasattr(req, "admin_token") else "admin"
        payload = analytics_snapshot_service.request_rebuild(
            scope=dto.scope,
            event_id=dto.event_id,
            requested_by=requested_by,
        )
        return jsonify(payload), 202
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_rebuild_analytics] %s", redact_sensitive(str(err)))
        return handle_service_error(err)
