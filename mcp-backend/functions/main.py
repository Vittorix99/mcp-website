import os
import sys
import logging

# === Path setup (solo se necessario per import locali) ===
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# === Logging config ===
logging.basicConfig(level=logging.DEBUG)  # Usa INFO o WARNING in produzione

# === Firebase Config ===
from firebase_admin import credentials, firestore, auth
from config.firebase_config import db, bucket, cors

# === API Pubbliche ===
from api.contact_api import  contact_us
from api.newsletter_api import newsletter_signup
from api.singnup_api import signup_request
from api.payments_api import create_order, capture_order
from api.events_api import get_event_by_id, get_next_event, get_all_events
from api.events_tickets_api import check_participants




from api.admin.newsletter_api import(
    
    admin_get_newsletter_signups,
    admin_delete_newsletter_signup,
    admin_update_newsletter_signup 
    
)
from api.admin.messages_api import(
    get_messages,
    
    delete_message,
    reply_to_message
)

from api.questions_api import (
    get_all_questions,
    get_question_by_id,
    create_question,
    update_question,
    delete_question
)

# === API Admin: Events ===
from api.admin.events_api import (
    admin_create_event,
    admin_update_event,
    admin_delete_event,
    admin_get_all_events,
    admin_get_event_by_id,
    admin_upload_event_photo
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
    send_ticket
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
    set_membership_price
)

# === API Admin: Purchases ===
from api.admin.purchases_api import (
    get_purchase,
    get_all_purchases,
    create_purchase,
    delete_purchase
)

# === Triggers ===
from triggers.ticket_trigger import (
    on_participant_created,
    on_membership_created
)

from api.admin.stats_api import admin_get_general_stats

from api.admin.setting_api import get_settings, set_settings
from triggers.jobs_trigger import process_send_location_job