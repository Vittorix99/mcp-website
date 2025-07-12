import logging
import base64
import uuid
from datetime import datetime
from typing import Dict, Any

from firebase_admin import firestore, storage, initialize_app, credentials
from flask import jsonify
from config.firebase_config import db, bucket

# Configura il logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('EventsService')



class EventsService:
    def __init__(self):
        self.db = db
        self.bucket = bucket
        self.collection_name = 'events'
        self.logger = logger

    def _validate_event_data(self, event_data: Dict[str, Any], is_update=False):
        self.logger.debug(f"_validate_event_data called. is_update={is_update}, data={event_data}")
        if not is_update:
            required = ['title', 'date', 'startTime', 'location']
            missing = [f for f in required if f not in event_data]
            if missing:
                raise ValueError(f"Missing required fields: {', '.join(missing)}")

        if 'date' in event_data:
            try:
                datetime.strptime(event_data['date'], '%d-%m-%Y')
            except ValueError:
                raise ValueError('Invalid date format. Use DD-MM-YYYY')

        if 'price' in event_data and event_data['price'] is not None:
            try:
                float(event_data['price'])
            except (ValueError, TypeError):
                raise ValueError('Invalid price format')

        if 'maxParticipants' in event_data and event_data['maxParticipants'] is not None:
            try:
                int(event_data['maxParticipants'])
            except (ValueError, TypeError):
                raise ValueError('Invalid maxParticipants format')

    def _upload_image_to_storage(self, image_data: str, title: str, image_type='main'):
        self.logger.debug(f"Uploading image for '{title}' [{image_type}]")
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]

        try:
            image_bytes = base64.b64decode(image_data)
        except Exception:
            self.logger.error("Invalid base64 image data")
            raise ValueError('Invalid base64 image data')

        unique_id = str(uuid.uuid4())[:8]
        if image_type == 'main':
            image_filename = f"{title}.jpg"
            image_path = f"events/{title}/{image_filename}"
        else:
            image_filename = f"{title}_{unique_id}.jpg"
            image_path = f"events/{title}/photos/{image_filename}"

        blob = self.bucket.blob(image_path)
        blob.upload_from_string(image_bytes, content_type='image/jpeg')
        blob.make_public()
        self.logger.info(f"Image uploaded to {image_path}")
        return image_filename, blob.public_url

    def _delete_image_from_storage(self, title, image_filename=None):
        path = f"events/{title}/{image_filename or title + '.jpg'}"
        blob = self.bucket.blob(path)
        if blob.exists():
            blob.delete()
            self.logger.info(f"Image deleted: {path}")
        else:
            self.logger.debug(f"No image to delete at: {path}")

    def _move_event_images(self, old_title, new_title):
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

    def create_event(self, event_data: Dict[str, Any], admin_uid: str):
        self.logger.debug(f"create_event by admin {admin_uid}")
        try:
            self._validate_event_data(event_data)
            title = event_data['title']

            # L'immagine arriva già pronta con il nome del file
            image_filename = event_data.get('image')  # None se mancante

            data = {
                'title': title,
                'description': event_data.get('description', ''),
                'date': event_data['date'],
                'startTime': event_data['startTime'],
                'endTime': event_data.get('endTime', ''),
                'location': event_data['location'],
                'price': float(event_data['price']) if event_data.get('price') else None,
                'fee':float(event_data['fee']) if event_data.get('fee') else None,
                'maxParticipants': int(event_data['maxParticipants']) if event_data.get('maxParticipants') else None,
                'active': event_data.get('active', True),
                'image': image_filename,
                'lineup': event_data.get('lineup', []),
                'note': event_data.get('note', ''),
                'participantsCount': 0,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'createdBy': admin_uid
            }

            doc_ref = self.db.collection(self.collection_name).add(data)
            event_id = doc_ref[1].id
            self.logger.info(f"Event created: {event_id}")

            return jsonify({'message': 'Event created', 'eventId': event_id}), 201

        except Exception as e:
            self.logger.error(f"[create_event] {str(e)}")
            return {'error': str(e)}, 400

    def update_event(self, event_id: str, event_data: Dict[str, Any], admin_uid: str):
        self.logger.debug(f"update_event {event_id} by {admin_uid}")
        try:
            self._validate_event_data(event_data, is_update=True)

            ref = self.db.collection(self.collection_name).document(event_id)
            doc = ref.get()
            if not doc.exists:
                return {'error': 'Event not found'}, 404

            current = doc.to_dict()
            old_title = current.get('title')
            new_title = event_data.get('title', old_title)

            if old_title != new_title and current.get('image'):
                moved = self._move_event_images(old_title, new_title)
                if moved:
                    event_data['image'] = moved

            image_url = None
            print("Event Data", event_data)
            if 'image' in event_data and event_data['image'].startswith('data:'):
                self._delete_image_from_storage(old_title, current['image'])
                image_filename, image_url = self._upload_image_to_storage(event_data['image'], new_title)
                event_data['image'] = image_filename

            if 'price' in event_data:
                event_data['price'] = float(event_data['price'])
            if 'fee' in event_data:
                event_data['fee'] = float(event_data['fee'])

            if 'maxParticipants' in event_data:
                event_data['maxParticipants'] = int(event_data['maxParticipants'])

            event_data['updatedAt'] = firestore.SERVER_TIMESTAMP
            event_data['updatedBy'] = admin_uid
            ref.update(event_data)

            self.logger.info(f"Event {event_id} updated")
            return jsonify({'message': 'Event updated', 'eventId': event_id, 'imageUrl': image_url}), 200
        except Exception as e:
            self.logger.error(f"[update_event] {str(e)}")
            return {'error': str(e)}, 400

    def delete_event(self, event_id: str, admin_uid: str):
        self.logger.debug(f"delete_event {event_id} by {admin_uid}")
        try:
            ref = self.db.collection(self.collection_name).document(event_id)
            doc = ref.get()
            if not doc.exists:
                return {'error': 'Event not found'}, 404

            data = doc.to_dict()
            title = data.get('title')

            if data.get('image'):
                self._delete_image_from_storage(title, data['image'])

            blobs = self.bucket.list_blobs(prefix=f"events/{title}/")
            for blob in blobs:
                blob.delete()

            ref.delete()
            self.logger.info(f"Event {event_id} deleted")
            return jsonify({'message': 'Event deleted', 'eventId': event_id}), 200
        except Exception as e:
            self.logger.error(f"[delete_event] {str(e)}")
            return {'error': str(e)}, 400

    def get_all_events(self):
            self.logger.debug("get_all_events")
            try:
                events = self.db.collection(self.collection_name).stream()
                events_list = []

                for e in events:
                    data = e.to_dict()
                    event_id = e.id
                    participants_count = self.get_event_participants_count(event_id)
                    data.update({
                        'id': event_id,
                        'participantsCount': participants_count
                    })
                    events_list.append(data)

                self.logger.info(f"Fetched {len(events_list)} events")
                return jsonify(events_list), 200

            except Exception as e:
                self.logger.error(f"[get_all_events] {str(e)}")
                return {'error': str(e)}, 500

    def get_event_by_id(self, event_id: str):
        self.logger.debug(f"get_event_by_id {event_id}")
        try:
            ref = self.db.collection(self.collection_name).document(event_id)
            doc = ref.get()
            if not doc.exists:
                return {'error': 'Event not found'}, 404

            data = doc.to_dict()
            data['id'] = doc.id
            if data.get('createdAt'):
                data['createdAt'] = data['createdAt'].isoformat()
            if data.get('updatedAt'):
                data['updatedAt'] = data['updatedAt'].isoformat()

            return jsonify({'event': data}), 200
        except Exception as e:
            self.logger.error(f"[get_event_by_id] {str(e)}")
            return {'error': str(e)}, 400

    def upload_event_photo(self, event_id: str, photo_data: str, admin_uid: str):
        self.logger.debug(f"upload_event_photo {event_id} by {admin_uid}")
        try:
            ref = self.db.collection(self.collection_name).document(event_id)
            doc = ref.get()
            if not doc.exists:
                return {'error': 'Event not found'}, 404

            data = doc.to_dict()
            title = data.get('title')
            filename, url = self._upload_image_to_storage(photo_data, title, 'additional')

            photos = data.get('additionalPhotos', [])
            photos.append({
                'filename': filename,
                'url': url,
                'uploadedAt': firestore.SERVER_TIMESTAMP,
                'uploadedBy': admin_uid
            })

            ref.update({
                'additionalPhotos': photos,
                'updatedAt': firestore.SERVER_TIMESTAMP,
                'updatedBy': admin_uid
            })

            self.logger.info(f"Photo uploaded for event {event_id}")
            return jsonify({'message': 'Photo uploaded', 'photoUrl': url, 'filename': filename}), 200
        except Exception as e:
            self.logger.error(f"[upload_event_photo] {str(e)}")
            return {'error': str(e)}, 400

    def get_event_participants_count(self, event_id: str) -> int:
        self.logger.debug(f"get_event_participants_count {event_id}")
        try:
            # Accesso alla sottocollezione participants_event sotto il documento participants/{eventId}
            participants_ref = self.db.collection("participants").document(event_id).collection("participants_event")
            participants = participants_ref.stream()
            count = sum(1 for _ in participants)  # Evita di materializzare tutta la lista
            self.logger.info(f"{count} participants found for event {event_id}")
            return count
        except Exception as e:
            self.logger.error(f"[get_event_participants_count] {str(e)}")
            return 0

    def update_participants_count(self, event_id: str):
        self.logger.debug(f"update_participants_count {event_id}")
        try:
            count = self.get_event_participants_count(event_id)
            self.db.collection(self.collection_name).document(event_id).update({
                'participantsCount': count
            })
            self.logger.info(f"Updated participant count: {count} for event {event_id}")
        except Exception as e:
            self.logger.error(f"[update_participants_count] {str(e)}")