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


        if next_event:
            return jsonify(next_event), 200
        else:
            return {'message': 'No upcoming events found'}, 400
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
    
    
