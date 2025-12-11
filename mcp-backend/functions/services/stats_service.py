from flask import jsonify
from google.cloud import firestore
from services.events_service import EventsService
from datetime import datetime, timedelta
from config.firebase_config import db
from datetime import timezone
datetime.now(timezone.utc)


class StatsService:
    def __init__(self):
        self.db = db

    def get_general_stats(self):
        try:
            # 🔢 Totali
            members_query = self.db.collection("memberships").where("subscription_valid", "==", True).stream()
            total_active_members = sum(1 for _ in members_query)

            purchases_query = self.db.collection("purchases").stream()
            purchases = [p.to_dict() for p in purchases_query]
            total_purchases = len(purchases)
            total_gross_amount = sum(float(p.get("amount_total", 0)) for p in purchases)
            total_net_amount = sum(float(p.get("net_amount", 0)) for p in purchases)

            events_query = self.db.collection("events").stream()
            total_events = sum(1 for _ in events_query)

            # 📅 Evento imminente
            events_service = EventsService()
            upcoming_resp, status_code = events_service.list_upcoming_events(limit=1)
            upcoming_event_data = None
            if status_code == 200:
                payload = upcoming_resp.get_json()
                if isinstance(payload, list) and payload:
                    upcoming_event_data = payload[0]

            upcoming_event_participants = 0
            upcoming_event_total_paid = 0.0

            if upcoming_event_data and upcoming_event_data.get("id"):
                upcoming_event_id = upcoming_event_data["id"]
                participants_query = self.db.collection("participants") \
                    .document(upcoming_event_id) \
                    .collection("participants_event").stream()

                for doc in participants_query:
                    data = doc.to_dict()
                    upcoming_event_participants += 1
                    try:
                        upcoming_event_total_paid += float(data.get("price", 0))
                    except (ValueError, TypeError):
                        continue
            now = datetime.now(timezone.utc)
            time_limit = now - timedelta(hours=24)

            messages_query = self.db.collection("contact_message") \
                .where("answered", "==", False) \
                .where("timestamp", ">=", time_limit) \
                .stream()

            last_24h_unanswered = sum(1 for _ in messages_query)

            last_message = (
                self.db.collection("contact_message")
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(1)
                .get()
)

            def doc_to_safe_dict(snapshot):
                return {**snapshot.to_dict(), "id": snapshot.id} if snapshot else None

            last_membership = (
                self.db.collection("memberships")
                .order_by("start_date", direction=firestore.Query.DESCENDING)
                .limit(1)
                .get()
            )

            last_purchase = (
                self.db.collection("purchases")
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(1)
                .get()
            )

            last_participant = (
                self.db.collection_group("participants_event")
                .order_by("createdAt", direction=firestore.Query.DESCENDING)
                .limit(1)
                .get()
            )

            response = {
                "total_active_members": total_active_members,
                "total_purchases": total_purchases,
                "total_events": total_events,
                "upcoming_event_participants": upcoming_event_participants,
                "upcoming_event_total_paid": f"{upcoming_event_total_paid:.2f}",
                "total_gross_amount": f"{total_gross_amount:.2f}",
                "total_net_amount": f"{total_net_amount:.2f}",
                "last_membership": doc_to_safe_dict(last_membership[0]) if last_membership else None,
                "last_purchase": doc_to_safe_dict(last_purchase[0]) if last_purchase else None,
                "last_participant": doc_to_safe_dict(last_participant[0]) if last_participant else None,
                "last_24h_unanswered_messages": last_24h_unanswered,
                "last_message": doc_to_safe_dict(last_message[0]) if last_message else None,
            }

            return jsonify(response), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
