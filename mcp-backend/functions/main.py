import os
import sys
import logging

# === Path setup (solo se necessario per import locali) ===
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# === Environment loading ===
from config import load_environment

_env_path = load_environment()
_mcp_env = os.environ.get("MCP_ENV", "test")
print(f"Environment: {_mcp_env} (env_file={_env_path})")

# === Logging config ===
logging.basicConfig(level=logging.DEBUG)  # Usa INFO o WARNING in produzione

# === Mail Service init ===
from services.communications.mail_service import init_mail_service

init_mail_service()

# === Firebase Config ===
from firebase_admin import credentials, firestore, auth
from config.firebase_config import db, bucket, cors

# === API Pubbliche ===
from api.public.contact_api import contact_us
from api.public.newsletter_api import newsletter_signup
from api.public.sender_webhook_api import sender_webhook
from api.public.event_payment_api import create_order_event, capture_order_event
from api.public.events_api import get_event_by_id, get_next_event, get_all_events
from api.public.events_tickets_api import check_participants




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
    admin_get_event_by_id
)

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
    update_membership,
    delete_membership,
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
    delete_purchase
)

# === Triggers ===
from triggers.registration_trigger import (
    on_participant_created,
    on_membership_created
)

from api.admin.stats_api import admin_get_general_stats
from api.admin.error_logs_api import admin_error_logs

from api.admin.setting_api import get_settings, set_settings
from triggers.jobs_trigger import process_send_location_job
from triggers.new_year_trigger import invalidate_memberships_new_year

# === API Entrance Scanner ===
from api.entrance import (
    entrance_generate_scan_token,
    entrance_verify_scan_token,
    entrance_deactivate_scan_token,
    entrance_manual_entry,
    entrance_validate,
    entrance_deactivate_scan_token,
)

# === API Admin: MailerLite ===
from api.admin.mailer_lite.groups_api import (
    admin_mailerlite_groups,
    admin_mailerlite_group_subscribers,
    admin_mailerlite_group_assign_subscriber,
    admin_mailerlite_group_unassign_subscriber,
)
from api.admin.mailer_lite.subscribers_api import (
    admin_mailerlite_subscribers,
    admin_mailerlite_subscriber_forget,
)
from api.admin.mailer_lite.campaigns_api import (
    admin_mailerlite_campaigns,
    admin_mailerlite_campaign_schedule,
    admin_mailerlite_campaign_cancel_ready,
)
from api.admin.mailer_lite.fields_api import admin_mailerlite_fields
from api.admin.mailer_lite.automations_api import (
    admin_mailerlite_automations,
    admin_mailerlite_automation_activity,
)
from api.admin.mailer_lite.segments_api import (
    admin_mailerlite_segments,
    admin_mailerlite_segment_subscribers,
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
