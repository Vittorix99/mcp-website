import os
import sys
import logging

# === Path setup (solo se necessario per import locali) ===
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# === Logging config ===
_log_level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, _log_level_name, logging.INFO))
logger = logging.getLogger("main")

# === Environment loading ===
from config import load_environment

load_environment()
_mcp_env = os.environ.get("MCP_ENV", "test")
logger.info("Environment loaded: mode=%s cloud_runtime=%s", _mcp_env, bool(os.environ.get("K_SERVICE")))

# === Mail Service init ===
from services.communications.mail_service import init_mail_service

init_mail_service()

# === Firebase Config ===
from firebase_admin import credentials, firestore, auth
from config.firebase_config import db, bucket, cors

# === API Pubbliche ===
from api.public.contact_api import contact_us
from api.public.newsletter_api import newsletter_signup
from api.public.settings_api import get_setting, get_membership_price_public
from api.public.sender_webhook_api import sender_webhook
from api.public.event_payment_api import create_order_event, capture_order_event
from api.public.events_api import get_event_by_id, get_next_event, get_all_events, get_event_guide
from api.public.events_tickets_api import check_participants
from api.public.radio_public_api import (
    get_published_radio_episodes,
    get_latest_radio_episode,
    get_radio_episode,
    get_radio_seasons,
)




from api.admin.newsletter_api import(
    admin_get_newsletter_signups,
    admin_delete_newsletter_signup,
    admin_update_newsletter_signup,
    admin_get_newsletter_consents,
)
from api.admin.messages_api import(
    get_messages,
    
    delete_message,
    reply_to_message
)

# === API Admin: Events ===
from api.admin.events_api import (
    admin_create_event,
    admin_update_event,
    admin_delete_event,
    admin_get_all_events,
    admin_get_event_by_id,
    admin_get_event_guide,
    admin_update_event_guide,
    admin_toggle_guide_published,
)

# === API Admin: Location ===
from api.admin.location_api import (
    admin_get_event_location,
    admin_update_event_location,
    admin_toggle_location_published,
)

# === API Admin: Member Auth Provisioning ===
from api.admin.members_auth_api import (
    provision_member_accounts,
    provision_single_member_account,
)

# === API Member ===
from api.member.member_api import (
    member_get_me,
    member_get_events,
    member_get_purchases,
    member_get_ticket,
    member_patch_preferences,
)
from api.member.location_api import member_get_event_location

# === API Admin: Participants ===
from api.admin.participants_api import (
    get_participants_by_event,
    get_participant,
    create_participant,
    update_participant,
    delete_participant,
    send_location,
    send_location_to_all,
    send_ticket,
    send_omaggio_emails,
)

# === API Admin: Memberships ===
from api.admin.members_api import (
    get_membership,
    get_memberships,
    create_membership,
    merge_memberships,
    update_membership,
    delete_membership,
    renew_membership,
    send_membership_card,
    get_membership_events,
    get_membership_purchases,
    get_membership_price,
    set_membership_price,
    get_memberships_report,
    get_wallet_model,
    set_wallet_model,
    create_wallet_pass,
    invalidate_wallet_pass,
)

# === API Admin: Purchases ===
from api.admin.purchases_api import (
    get_purchase,
    get_all_purchases,
    create_purchase,
    update_purchase_status,
    delete_purchase
)

# === Triggers ===
from triggers.registration_trigger import (
    on_participant_created,
    on_membership_created
)

from api.admin.stats_api import (
    admin_get_general_stats,
    admin_get_dashboard_snapshot,
    admin_get_analytics_event_snapshot,
    admin_get_analytics_global_snapshot,
    admin_get_analytics_events_index,
    admin_get_entrance_flow,
    admin_get_sales_over_time,
    admin_get_audience_retention,
    admin_get_revenue_breakdown,
    admin_get_event_funnel,
    admin_get_gender_distribution,
    admin_get_age_distribution,
    admin_get_membership_trend,
    admin_get_dashboard_kpis,
    admin_rebuild_analytics,
)
from api.admin.setting_api import get_settings, set_settings

# === API Admin: Radio ===
from api.admin.radio_seasons_api import (
    admin_get_radio_seasons,
    admin_create_radio_season,
    admin_get_radio_season,
    admin_update_radio_season,
    admin_delete_radio_season,
)
from api.admin.radio_episodes_api import (
    admin_get_radio_episodes,
    admin_create_radio_episode,
    admin_get_radio_episode,
    admin_update_radio_episode,
    admin_delete_radio_episode,
    admin_publish_radio_episode,
    admin_unpublish_radio_episode,
)
from triggers.jobs_trigger import process_send_location_job, process_analytics_rebuild_job
from triggers.new_year_trigger import invalidate_memberships_new_year
from triggers.cleanup_trigger import cleanup_stale_data
from triggers.analytics_trigger import (
    on_purchase_written,
    on_participant_written,
    on_entrance_scan_written,
    on_membership_written,
    rebuild_analytics_nightly,
)

# === API Entrance Scanner ===
from api.entrance.entrance_api import (
    entrance_generate_scan_token,
    entrance_verify_scan_token,
    entrance_deactivate_scan_token,
    entrance_manual_entry,
    entrance_validate,
)

# === API Admin: Sender ===
from api.admin.sender.subscribers_api import (
    admin_sender_subscribers,
    admin_sender_subscriber_groups,
    admin_sender_subscriber_events,
)
from api.admin.sender.groups_api import (
    admin_sender_groups,
    admin_sender_group_subscribers,
)
from api.admin.sender.campaigns_api import (
    admin_sender_campaigns,
    admin_sender_campaign_send,
    admin_sender_campaign_schedule,
    admin_sender_campaign_copy,
    admin_sender_campaign_stats,
)
from api.admin.sender.fields_api import admin_sender_fields
from api.admin.sender.segments_api import (
    admin_sender_segments,
    admin_sender_segment_subscribers,
)
from api.admin.sender.transactional_api import (
    admin_sender_transactional,
    admin_sender_transactional_send,
)
