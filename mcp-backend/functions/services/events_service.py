import base64
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from firebase_admin import firestore
from flask import jsonify

from config.firebase_config import bucket, db
from models import Event
from utils.events_utils import map_purchase_mode

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("EventsService")


class EventsService:
    def __init__(self):
        self.db = db
        self.bucket = bucket
        self.collection_name = "events"
        self.logger = logger
        self.public_field_profiles = {
            "card": ["title", "date", "startTime", "endTime", "locationHint", "image", "photoPath", "description"],
            "gallery": ["title", "date", "description", "photoPath", "image"],
            "ids": ["title"],  # Firestore richiede almeno un campo in select()
        }

    # ----------------------- Date helpers -----------------------
    def _normalize_date_string(self, date_str: str) -> str:
        """
        Accepts DD-MM-YYYY, DD/MM/YYYY, or YYYY-MM-DD and returns a normalized DD-MM-YYYY string.
        """
        if not date_str:
            raise ValueError("Invalid date format. Use DD-MM-YYYY")

        value = str(date_str).strip()
        candidates = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"]
        for fmt in candidates:
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed.strftime("%d-%m-%Y")
            except ValueError:
                continue

        raise ValueError("Invalid date format. Use DD-MM-YYYY")

    def _safe_parse_date(self, date_str: str):
        """
        Try to parse a stored date (accepting both '-' and '/' just in case of legacy data).
        Returns a date object or None.
        """
        if not date_str:
            return None
        value = str(date_str).strip()
        for fmt in ["%d-%m-%Y", "%d/%m/%Y"]:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    # ----------------------- Model helpers -----------------------
    def _event_from_snapshot(self, snapshot) -> Event:
        data = snapshot.to_dict() or {}
        event = Event.from_firestore(data, snapshot.id)
        legacy_type = data.get("type")
        event.purchase_mode = map_purchase_mode(legacy_type or event.purchase_mode.value)
        return event

    def _event_to_dict(self, event: Event, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = event.to_firestore(include_none=True)
        payload["id"] = event.id
        payload["purchaseMode"] = event.purchase_mode.value

        if extra:
            for key, value in extra.items():
                if key not in payload:
                    payload[key] = value
        return payload

    def _shape_public_event(self, raw: Dict[str, Any], view: Optional[str]):
        if view == "card":
            return {
                "id": raw.get("id"),
                "title": raw.get("title"),
                "date": raw.get("date"),
                "startTime": raw.get("startTime"),
                "endTime": raw.get("endTime"),
                "locationHint": raw.get("locationHint"),
                "image": raw.get("image"),
                "photoPath": raw.get("photoPath"),
                "description": raw.get("description"),
            }
        if view == "gallery":
            return {
                "id": raw.get("id"),
                "title": raw.get("title"),
                "date": raw.get("date"),
                "description": raw.get("description"),
                "photoPath": raw.get("photoPath"),
                "image": raw.get("image"),
            }
        if view == "ids":
            return {"id": raw.get("id")}

        event = Event.from_firestore(raw, raw.get("id"))
        return self._event_to_dict(event, raw)

    def _apply_payload_to_event(self, event: Event, payload: Dict[str, Any]):
        field_map = {
            "title": "title",
            "date": "date",
            "startTime": "start_time",
            "start_time": "start_time",
            "endTime": "end_time",
            "end_time": "end_time",
            "location": "location",
            "locationHint": "location_hint",
            "location_hint": "location_hint",
            "price": "price",
            "fee": "fee",
            "membershipFee": "membership_fee",
            "maxParticipants": "max_participants",
            "max_participants": "max_participants",
            "active": "active",
            "image": "image",
            "lineup": "lineup",
            "note": "note",
            "allowDuplicates": "allow_duplicates",
            "allow_duplicates": "allow_duplicates",
            "over21Only": "over21_only",
            "over21_only": "over21_only",
            "onlyFemales": "only_females",
            "only_females": "only_females",
            "externalLink": "external_link",
            "external_link": "external_link",
        }

        for key, attr in field_map.items():
            if key not in payload:
                continue
            value = payload[key]
            if attr in {"price", "fee"} and value is not None:
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    raise ValueError(f"Invalid value for {key}")
            if attr == "max_participants" and value is not None:
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    raise ValueError(f"Invalid value for {key}")
            setattr(event, attr, value)

        purchase_value = payload.get("purchaseMode")
        if purchase_value is None and "type" in payload:
            purchase_value = payload["type"]
        if purchase_value is not None:
            event.purchase_mode = map_purchase_mode(purchase_value)

    # ----------------------- Admin helpers -----------------------
    def _validate_event_data(self, event_data: Dict[str, Any], is_update=False):
        self.logger.debug(f"_validate_event_data called. is_update={is_update}, data={event_data}")

        # Per gli update, rimuoviamo i campi stringa vuoti per evitare di validare valori non modificati.
        if is_update:
            keys_to_remove = []
            for key, value in event_data.items():
                if isinstance(value, str) and value.strip() == "":
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                event_data.pop(key, None)

        if not is_update:
            required = ["title", "date", "startTime", "location", "locationHint"]
            missing = [f for f in required if f not in event_data]
            if missing:
                raise ValueError(f"Missing required fields: {', '.join(missing)}")

        if "date" in event_data:
            event_data["date"] = self._normalize_date_string(event_data["date"])

        if "price" in event_data and event_data["price"] is not None:
            try:
                float(event_data["price"])
            except (ValueError, TypeError):
                raise ValueError("Invalid price format")

        if "maxParticipants" in event_data and event_data["maxParticipants"] is not None:
            try:
                int(event_data["maxParticipants"])
            except (ValueError, TypeError):
                raise ValueError("Invalid maxParticipants format")

    def _upload_image_to_storage(self, image_data: str, title: str, image_type="main"):
        self.logger.debug(f"Uploading image for '{title}' [{image_type}]")
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]

        image_bytes = base64.b64decode(image_data)

        unique_id = str(uuid.uuid4())[:8]
        if image_type == "main":
            image_filename = f"{title}.jpg"
            image_path = f"events/{title}/{image_filename}"
        else:
            image_filename = f"{title}_{unique_id}.jpg"
            image_path = f"events/{title}/photos/{image_filename}"

        blob = self.bucket.blob(image_path)
        blob.upload_from_string(image_bytes, content_type="image/jpeg")
        blob.make_public()
        self.logger.info(f"Image uploaded to {image_path}")
        return image_filename, blob.public_url

    def _delete_image_from_storage(self, title: str, image_filename: Optional[str] = None):
        path = f"events/{title}/{image_filename or title + '.jpg'}"
        blob = self.bucket.blob(path)
        if blob.exists():
            blob.delete()
            self.logger.info(f"Image deleted: {path}")
        else:
            self.logger.debug(f"No image to delete at: {path}")

    def _move_event_images(self, old_title: str, new_title: str):
        old_path = f"events/{old_title}/{old_title}.jpg"
        new_path = f"events/{new_title}/{new_title}.jpg"
        old_blob = self.bucket.blob(old_path)
        if old_blob.exists():
            new_blob = self.bucket.blob(new_path)
            new_blob.rewrite(old_blob)
            old_blob.delete()
            self.logger.info(f"Image moved to: {new_path}")
            return f"{new_title}.jpg"
        return None

    # ----------------------- Admin actions -----------------------
    def create_event(self, event_data: Dict[str, Any], admin_uid: str):
        self.logger.debug(f"create_event by admin {admin_uid}")
        try:
            self._validate_event_data(event_data)

            event = Event(
                participants_count=0,
                created_at=firestore.SERVER_TIMESTAMP,
                created_by=admin_uid,
            )
            self._apply_payload_to_event(event, event_data)

            doc_ref = self.db.collection(self.collection_name).add(event.to_firestore(include_none=True))
            event_id = doc_ref[1].id
            self.logger.info(f"Event created: {event_id}")

            return jsonify({"message": "Event created", "eventId": event_id}), 201

        except Exception as e:
            self.logger.error(f"[create_event] {str(e)}")
            return {"error": str(e)}, 400

    def update_event(self, event_id: str, event_data: Dict[str, Any], admin_uid: str):
        self.logger.debug(f"update_event {event_id} by {admin_uid}")
        try:
            self._validate_event_data(event_data, is_update=True)

            ref = self.db.collection(self.collection_name).document(event_id)
            doc = ref.get()
            if not doc.exists:
                return {"error": "Event not found"}, 404

            event = self._event_from_snapshot(doc)
            current = doc.to_dict() or {}
            old_title = event.title
            new_title = event_data.get("title", old_title)

            if old_title != new_title and event.image:
                moved = self._move_event_images(old_title, new_title)
                if moved:
                    event_data["image"] = moved

            image_url = None
            if "image" in event_data and isinstance(event_data["image"], str) and event_data["image"].startswith("data:"):
                self._delete_image_from_storage(old_title, current.get("image"))
                image_filename, image_url = self._upload_image_to_storage(event_data["image"], new_title)
                event_data["image"] = image_filename

            self._apply_payload_to_event(event, event_data)
            event.updated_at = firestore.SERVER_TIMESTAMP
            event.updated_by = admin_uid

            ref.update(event.to_firestore(include_none=True))

            self.logger.info(f"Event {event_id} updated")
            return jsonify({"message": "Event updated", "eventId": event_id, "imageUrl": image_url}), 200
        except Exception as e:
            self.logger.error(f"[update_event] {str(e)}")
            return {"error": str(e)}, 400

    def delete_event(self, event_id: str, admin_uid: str):
        self.logger.debug(f"delete_event {event_id} by {admin_uid}")
        try:
            ref = self.db.collection(self.collection_name).document(event_id)
            doc = ref.get()
            if not doc.exists:
                return {"error": "Event not found"}, 404

            data = doc.to_dict()
            title = data.get("title")

            if data.get("image"):
                self._delete_image_from_storage(title, data["image"])

            blobs = self.bucket.list_blobs(prefix=f"events/{title}/")
            for blob in blobs:
                blob.delete()

            ref.delete()
            self.logger.info(f"Event {event_id} deleted")
            return jsonify({"message": "Event deleted", "eventId": event_id}), 200
        except Exception as e:
            self.logger.error(f"[delete_event] {str(e)}")
            return {"error": str(e)}, 400

    def get_all_events(self):
        self.logger.debug("get_all_events")
        try:
            events = self.db.collection(self.collection_name).stream()
            events_list: List[Dict[str, Any]] = []

            for snapshot in events:
                raw = snapshot.to_dict() or {}
                event = self._event_from_snapshot(snapshot)
                event.participants_count = self.get_event_participants_count(event.id)
                event_dict = self._event_to_dict(event, raw)
                events_list.append(event_dict)

            self.logger.info(f"Fetched {len(events_list)} events")
            return jsonify(events_list), 200
        except Exception as e:
            self.logger.error(f"[get_all_events] {str(e)}")
            return {"error": str(e)}, 500

    def get_event_by_id(self, event_id: str):
        self.logger.debug(f"get_event_by_id {event_id}")
        try:
            event_ref = self.db.collection(self.collection_name).document(event_id)
            event = event_ref.get()

            if not event.exists:
                return {"error": f"Event with ID {event_id} not found"}, 404

            model = self._event_from_snapshot(event)
            event_payload = self._event_to_dict(model, event.to_dict())
            return jsonify({"event": event_payload}), 200
        except Exception as e:
            self.logger.error(f"[get_event_by_id] {str(e)}")
            return {"error": str(e)}, 500

    def get_event_participants_count(self, event_id: str) -> int:
        try:
            participants_ref = (
                self.db.collection("participants").document(event_id).collection("participants_event")
            )
            participants = participants_ref.stream()
            count = sum(1 for _ in participants)
            return count
        except Exception as e:
            self.logger.error(f"[get_event_participants_count] {str(e)}")
            return 0

    def upload_event_photo(self, event_id: str, photo_data: str, admin_uid: str):
        self.logger.debug(f"upload_event_photo {event_id} by {admin_uid}")
        try:
            ref = self.db.collection(self.collection_name).document(event_id)
            doc = ref.get()
            if not doc.exists:
                return {"error": "Event not found"}, 404

            data = doc.to_dict() or {}
            title = data.get("title")
            filename, url = self._upload_image_to_storage(photo_data, title, "additional")

            photos = data.get("additionalPhotos", [])
            photos.append(
                {
                    "filename": filename,
                    "url": url,
                    "uploadedAt": firestore.SERVER_TIMESTAMP,
                    "uploadedBy": admin_uid,
                }
            )

            ref.update(
                {
                    "additionalPhotos": photos,
                    "updatedAt": firestore.SERVER_TIMESTAMP,
                    "updatedBy": admin_uid,
                }
            )

            return jsonify({"message": "Photo uploaded", "photoUrl": url, "filename": filename}), 200
        except Exception as e:
            self.logger.error(f"[upload_event_photo] {str(e)}")
            return {"error": str(e)}, 400

    # ----------------------- Public endpoints -----------------------
    def list_public_events(self, view: Optional[str] = None):
        """Fetch all events for the public site."""
        try:
            base_query = self.db.collection(self.collection_name)
            selected_fields = self.public_field_profiles.get(view)
            events = (
                base_query.select(selected_fields).stream()
                if selected_fields
                else base_query.stream()
            )
            events_list = []
            for snapshot in events:
                raw = snapshot.to_dict() or {}
                raw["id"] = snapshot.id
                events_list.append(self._shape_public_event(raw, view))
            return jsonify(events_list), 200
        except Exception as e:
            return {"error": str(e)}, 500

    def list_upcoming_events(self, limit: int = 5):
        """Return upcoming events ordered by date (public data)."""
        try:
            snapshots = list(self.db.collection(self.collection_name).stream())
            events = []
            for snapshot in snapshots:
                model = self._event_from_snapshot(snapshot)
                if not model.date:
                    continue
                event_date = self._safe_parse_date(model.date)
                if not event_date:
                    continue
                if event_date >= datetime.now().date():
                    events.append((event_date, model, snapshot.to_dict() or {}))

            events.sort(key=lambda item: item[0])
            limited = events[:limit] if limit else events
            payload = [self._event_to_dict(model, raw) for _, model, raw in limited]
            return jsonify(payload), 200
        except Exception as e:
            return {"error": str(e)}, 500

    def get_next_public_event(self):
        try:
            today = datetime.now().date()
            snapshots = list(self.db.collection(self.collection_name).stream())
            events = [(self._event_from_snapshot(snapshot), snapshot.to_dict() or {}) for snapshot in snapshots]

            def parse_date(event: Event):
                return self._safe_parse_date(event.date)

            future_events = [(evt, raw) for evt, raw in events if evt.date]
            sorted_events = sorted(future_events, key=lambda pair: parse_date(pair[0]))
            upcoming_events = [self._event_to_dict(model, raw) for model, raw in sorted_events if parse_date(model) and parse_date(model) >= today]

            return jsonify(upcoming_events), 200
        except Exception as e:
            return {"error": str(e)}, 500

    def get_public_event_by_id(self, event_id: str):
        try:
            event_ref = self.db.collection(self.collection_name).document(event_id)
            event = event_ref.get()

            if not event.exists:
                return {"error": f"Event with ID {event_id} not found"}, 404

            model = self._event_from_snapshot(event)
            payload = self._event_to_dict(model, event.to_dict())
            return jsonify(payload), 200
        except Exception as e:
            return {"error": str(e)}, 500
