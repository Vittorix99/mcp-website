from config.firebase_config import db, bucket
from flask import jsonify
from datetime import datetime
import base64
from firebase_admin import firestore, storage



def get_all_events_service():
    """Fetch all events from Firestore"""
    try:
        events = db.collection('events').stream()
        events_list = [{**event.to_dict(), 'id': event.id} for event in events]
        return jsonify(events_list), 200
    except Exception as e:
        return {'error': str(e)}, 500

def update_event_service(req_json):
    """Update an event"""
    try:
        event_id = req_json['id']
        updated_data = req_json['updatedData']

        db.collection('events').document(event_id).update(updated_data)
        return {'message': 'Event updated successfully'}, 200
    except Exception as e:
        return {'error': str(e)}, 500

def delete_event_service(event_id):
    """Delete an event"""
    try:
        db.collection('events').document(event_id).delete()
        return {'message': 'Event deleted successfully'}, 200
    except Exception as e:
        return {'error': str(e)}, 500


def get_next_event_service():
    """Get the next upcoming event"""
    try:
        # Get today's date as a datetime object
        today = datetime.now().date()

        # Query for all active events
        events = db.collection('events').stream()

        # Convert to list and add id to each event
        all_events = [{**event.to_dict(), 'id': event.id} for event in events]

        # Sort events by date, converting string dates to datetime objects
        sorted_events = sorted(all_events, key=lambda x: datetime.strptime(x['date'], '%d-%m-%Y').date())

        # Find the first event that's in the future
        next_event = next((event for event in sorted_events if datetime.strptime(event['date'], '%d-%m-%Y').date() >= today), None)

        print("Next event:", next_event)

        if next_event:
            return jsonify(next_event), 200
        else:
            return {'message': 'No upcoming events found'}, 404
    except Exception as e:
        return {'error': str(e)}, 500


def get_event_by_id_service(event_id):
    """Get details of a specific event by ID"""
    try:
        event_ref = db.collection('events').document(event_id)
        event = event_ref.get()

        if not event.exists:
            return {'error': f"Event with ID {event_id} not found"}, 404
        
        return jsonify({
            'id': event.id,
            **event.to_dict()
        }), 200
    except Exception as e:
        return {'error': str(e)}, 500
    
    
# Admin API functions

def create_event_service(event_data, admin_uid):
    required_fields = ['title', 'date', 'startTime', 'endTime', 'location', 'price', 'image']
    if not all(field in event_data for field in required_fields):
        raise ValueError('Missing required fields')

    try:
        datetime.strptime(event_data['date'], '%d-%m-%Y')
    except ValueError:
        raise ValueError('Invalid date format. Use DD-MM-YYYY')

    title = event_data['title']
    image_data = event_data['image']

    if 'base64,' in image_data:
        image_data = image_data.split('base64,')[1]

    image_bytes = base64.b64decode(image_data)

    image_filename = f"{title}.jpg"
    folder_path = f"events/{title}"
    image_path = f"{folder_path}/{image_filename}"

    blob = bucket.blob(image_path)
    blob.upload_from_string(image_bytes, content_type='image/jpeg')
    blob.make_public()

    event_doc = {
        'title': title,
        'date': event_data['date'],
        'startTime': event_data['startTime'],
        'endTime': event_data['endTime'],
        'location': event_data['location'],
        'price': float(event_data['price']),
        'active': event_data.get('active', True),
        'image': image_filename,
        'lineup': event_data.get('lineup', []),
        'note': event_data.get('note', ''),
        'createdAt': firestore.SERVER_TIMESTAMP,
        'createdBy': admin_uid
    }

    event_ref = db.collection('events').add(event_doc)

    return {
        'message': 'Event created successfully',
        'eventId': event_ref[1].id,
        'imageUrl': blob.public_url
    }
    
def update_event_service(event_data, admin_uid):
    event_id = event_data.pop('id')
    event_ref = db.collection('events').document(event_id)
    
    event_doc = event_ref.get()
    if not event_doc.exists:
        raise ValueError('Event not found')

    if 'title' in event_data and event_doc.get('image'):
        old_title = event_doc.get('title')
        new_title = event_data['title']
        
        if old_title != new_title:
            old_path = f"events/{old_title}/{old_title}.jpg"
            new_path = f"events/{new_title}/{new_title}.jpg"
            
            old_blob = bucket.blob(old_path)
            new_blob = bucket.blob(new_path)
            
            if old_blob.exists():
                new_blob.rewrite(old_blob)
                old_blob.delete()
                event_data['image'] = f"{new_title}.jpg"

    if 'image' in event_data and event_data['image'].startswith('data:'):
        image_data = event_data['image']
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]

        image_bytes = base64.b64decode(image_data)

        title = event_data.get('title', event_doc.get('title'))
        
        image_filename = f"{title}.jpg"
        folder_path = f"events/{title}"
        image_path = f"{folder_path}/{image_filename}"

        blob = bucket.blob(image_path)
        blob.upload_from_string(image_bytes, content_type='image/jpeg')
        blob.make_public()

        event_data['image'] = image_filename

    if 'date' in event_data:
        try:
            datetime.strptime(event_data['date'], '%d-%m-%Y')
        except ValueError:
            raise ValueError('Invalid date format. Use DD-MM-YYYY')

    if 'price' in event_data:
        event_data['price'] = float(event_data['price'])

    event_data['updatedAt'] = firestore.SERVER_TIMESTAMP
    event_data['updatedBy'] = admin_uid

    event_ref.update(event_data)

    return {
        'message': 'Event updated successfully',
        'eventId': event_id
    }

def delete_event_service(event_id):
    event_ref = db.collection('events').document(event_id)
    event_doc = event_ref.get()
    
    if not event_doc.exists:
        raise ValueError('Event not found')

    event_data = event_doc.to_dict()
    if event_data.get('image'):
        title = event_data.get('title')
        image_path = f"events/{title}/{title}.jpg"
        blob = bucket.blob(image_path)
        if blob.exists():
            blob.delete()