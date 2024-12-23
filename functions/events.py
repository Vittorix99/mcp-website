

from firebase_admin import auth
from firebase_functions import https_fn
from firebase_functions import params

from flask import jsonify
from firebase_functions import https_fn
from firebase_config import db, bucket, cors
from datetime import datetime
import base64

@https_fn.on_request(cors=cors)
def create_event(req):
    """
    Crea un evento con immagine caricata su Firebase Storage.
    """
    if req.method != 'POST':
        return 'Invalid request method', 405

    try:
        # Ricezione dei dati JSON
        req_json = req.get_json()
        if not req_json or 'eventData' not in req_json or 'imageBase64' not in req_json or 'imageName' not in req_json:
            return {'error': 'Missing required fields'}, 400

        # Estrarre i dati JSON
        event_data = req_json['eventData']
        image_name = req_json['imageName']
        image_base64 = req_json['imageBase64']

        # Caricamento immagine su Firebase Storage
        blob = bucket.blob(f"events/{image_name}")  # Salva in una cartella chiamata "events"
        blob.upload_from_string(base64.b64decode(image_base64), content_type='image/jpeg')

        # Ottieni l'URL pubblico
        image_url = blob.public_url

        # Aggiunta dell'immagine ai dati evento
        event_data['image'] = image_url

        # Salva i dati su Firestore
        doc_ref = db.collection('events').add(event_data)

        return jsonify({
            'message': 'Event created successfully',
            'event_id': doc_ref[1].id,
            'image_url': image_url
        }), 201

    except Exception as e:
        print(f"Error: {e}")
        return {'error': str(e)}, 500

@https_fn.on_request(cors=cors)
def get_all_events(req):
    if req.method != 'GET':
        return 'Invalid request method', 405

    try:
        events = db.collection('events')
        events = events.stream()
        
        events_list = [{**event.to_dict(), 'id': event.id} for event in events]
        print(events_list)
        return jsonify(events_list), 200
    except Exception as e:
        return {'error': str(e)}, 500



@https_fn.on_request(cors=cors)
def update_event(req):
    if req.method != 'PUT':
        return 'Invalid request method', 405

    try:
        req_json = req.get_json()
        if not req_json or 'id' not in req_json or 'updatedData' not in req_json:
            return {'error': 'Missing required fields'}, 400

        event_id = req_json['id']
        updated_data = req_json['updatedData']

        # Aggiorna documento in Firestore
        db.collection('events').document(event_id).update(updated_data)
        return {'message': 'Event updated successfully'}, 200
    except Exception as e:
        return {'error': str(e)}, 500


@https_fn.on_request(cors=cors)
def delete_event(req):
    if req.method != 'DELETE':
        return 'Invalid request method', 405

    try:
        event_id = req.args.get('id')
        if not event_id:
            return {'error': 'Missing event ID'}, 400

        # Elimina il documento Firestore
        db.collection('events').document(event_id).delete()
        return {'message': 'Event deleted successfully'}, 200
    except Exception as e:
        return {'error': str(e)}, 500


@https_fn.on_request(cors=cors)
def get_next_event(req):
    if req.method != 'GET':
        return 'Invalid request method', 405

    try:
        today = datetime.now().strftime('%Y-%m-%d')

        # Query per trovare l'evento con la data più vicina
        events = db.collection('events') \
            .where('date', '>=', today) \
            .order_by('date') \
            .limit(1) \
            .stream()

        # Include the document ID in the returned event object
        next_event = [{
            **event.to_dict(),  # Merge document data
            'id': event.id      # Add document ID
        } for event in events]

        print(next_event)
        if next_event:
            return jsonify(next_event[0]), 200
        else:
            return {'message': 'No upcoming events found'}, 404
    except Exception as e:
        return {'error': str(e)}, 500

@https_fn.on_request(cors=cors)
def get_event_by_Id(req):
    try:
        # Verifica se l'utente è autenticato

        
        # Recupera l'ID dell'evento
        event_id = req.args.get('id')
        if not event_id:
            raise ValueError("Event ID is required")
        
        # Ottieni i dettagli dell'evento da Firestore
        event_ref = db.collection('events').document(event_id)
        event = event_ref.get()

        # Verifica se l'evento esiste
        if not event.exists:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.NOT_FOUND,
                message=f"Event with ID {event_id} not found"
            )
        
        # Restituisci i dati dell'evento
        return {
            'id': event.id,
            **event.to_dict()
        }
        
    except ValueError as ve:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message=str(ve)
        )
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error getting event: {str(e)}"
        )
@https_fn.on_request(cors=cors)
def get_all_events(req):
    if req.method != 'GET':
        return 'Invalid request method', 405

    try:
        events = db.collection('events')
        events = events.stream()
        
        events_list = [{**event.to_dict(), 'id': event.id} for event in events]
        print(events_list)
        return jsonify(events_list), 200
    except Exception as e:
        return {'error': str(e)}, 500