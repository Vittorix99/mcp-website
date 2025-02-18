from firebase_admin import firestore, storage
from firebase_functions import https_fn
from firebase_admin import initialize_app
from config.firebase_config import cors
from services.admin.auth_service import require_admin
from datetime import datetime
import base64
from config.firebase_config import db, bucket



# functions/admin/events_admin.py



initialize_app()
db = firestore.client()
bucket = storage.bucket()

@https_fn.on_request(cors=cors)
@require_admin
def create_event(req: https_fn.Request) -> https_fn.Response:
    """Create a new event"""
    if req.method != 'POST':
        return https_fn.Response('Invalid request method', status=405)

    try:
        req_json = req.get_json()
        if not req_json:
            return https_fn.Response('Missing request body', status=400)

        required_fields = ['title', 'date', 'startTime', 'endTime', 'location', 'price', 'image']
        if not all(field in req_json for field in required_fields):
            return https_fn.Response('Missing required fields', status=400)

        # Validate date format
        try:
            datetime.strptime(req_json['date'], '%d-%m-%Y')
        except ValueError:
            return https_fn.Response('Invalid date format. Use DD-MM-YYYY', status=400)

        title = req_json['title']
        image_data = req_json['image']  # This should be base64 encoded image data

        # Remove header from base64 if present
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]

        # Decode base64 image
        image_bytes = base64.b64decode(image_data)

        # Create the image path in storage
        image_filename = f"{title}.jpg"
        folder_path = f"events/{title}"
        image_path = f"{folder_path}/{image_filename}"

        # Upload image to Firebase Storage
        blob = bucket.blob(image_path)
        blob.upload_from_string(image_bytes, content_type='image/jpeg')

        # Make the image publicly accessible
        blob.make_public()

        event_data = {
            'title': title,
            'date': req_json['date'],
            'startTime': req_json['startTime'],
            'endTime': req_json['endTime'],
            'location': req_json['location'],
            'price': float(req_json['price']),
            'active': req_json.get('active', True),
            'image': image_filename,  # Store only the filename
            'lineup': req_json.get('lineup', []),
            'note': req_json.get('note', ''),
            'createdAt': firestore.SERVER_TIMESTAMP,
            'createdBy': req.admin_token['uid']
        }

        # Add event to Firestore
        event_ref = db.collection('events').add(event_data)

        return https_fn.Response({
            'message': 'Event created successfully',
            'eventId': event_ref[1].id,
            'imageUrl': blob.public_url
        }, status=201)

    except Exception as e:
        print(f"Error creating event: {str(e)}")
        return https_fn.Response({'error': str(e)}, status=500)

@https_fn.on_request(cors=cors)
@require_admin
def update_event(req: https_fn.Request) -> https_fn.Response:
    """Update an existing event"""
    if req.method != 'PUT':
        return https_fn.Response('Invalid request method', status=405)

    try:
        req_json = req.get_json()
        if not req_json or 'id' not in req_json:
            return https_fn.Response('Missing event ID', status=400)

        event_id = req_json.pop('id')
        event_ref = db.collection('events').document(event_id)
        
        event_doc = event_ref.get()
        if not event_doc.exists:
            return https_fn.Response('Event not found', status=404)

        # If title is being updated and there's an image, we need to move the image
        if 'title' in req_json and event_doc.get('image'):
            old_title = event_doc.get('title')
            new_title = req_json['title']
            
            # Move image to new folder if title changed
            if old_title != new_title:
                old_path = f"events/{old_title}/{old_title}.jpg"
                new_path = f"events/{new_title}/{new_title}.jpg"
                
                # Copy the old image to new location
                old_blob = bucket.blob(old_path)
                new_blob = bucket.blob(new_path)
                
                if old_blob.exists():
                    new_blob.rewrite(old_blob)
                    # Delete the old image
                    old_blob.delete()
                    
                    # Update the image field in the document
                    req_json['image'] = f"{new_title}.jpg"

        # If a new image is being uploaded
        if 'image' in req_json and req_json['image'].startswith('data:'):
            image_data = req_json['image']
            if 'base64,' in image_data:
                image_data = image_data.split('base64,')[1]

            # Decode base64 image
            image_bytes = base64.b64decode(image_data)

            # Get the title (either new or existing)
            title = req_json.get('title', event_doc.get('title'))
            
            # Create the image path in storage
            image_filename = f"{title}.jpg"
            folder_path = f"events/{title}"
            image_path = f"{folder_path}/{image_filename}"

            # Upload new image
            blob = bucket.blob(image_path)
            blob.upload_from_string(image_bytes, content_type='image/jpeg')
            blob.make_public()

            # Update the image field to store only the filename
            req_json['image'] = image_filename

        # If date is being updated, validate its format
        if 'date' in req_json:
            try:
                datetime.strptime(req_json['date'], '%d-%m-%Y')
            except ValueError:
                return https_fn.Response('Invalid date format. Use DD-MM-YYYY', status=400)

        # Convert price to float if present
        if 'price' in req_json:
            req_json['price'] = float(req_json['price'])

        # Add update metadata
        req_json['updatedAt'] = firestore.SERVER_TIMESTAMP
        req_json['updatedBy'] = req.admin_token['uid']

        # Update the event
        event_ref.update(req_json)

        return https_fn.Response({
            'message': 'Event updated successfully',
            'eventId': event_id
        }, status=200)

    except Exception as e:
        print(f"Error updating event: {str(e)}")
        return https_fn.Response({'error': str(e)}, status=500)

@https_fn.on_request(cors=cors)
@require_admin
def delete_event(req: https_fn.Request) -> https_fn.Response:
    """Delete an event"""
    if req.method != 'DELETE':
        return https_fn.Response('Invalid request method', status=405)

    try:
        event_id = req.args.get('id')
        if not event_id:
            return https_fn.Response('Missing event ID', status=400)

        event_ref = db.collection('events').document(event_id)
        event_doc = event_ref.get()
        
        if not event_doc.exists:
            return https_fn.Response('Event not found', status=404)

        # Delete the image from storage if it exists
        event_data = event_doc.to_dict()
        if event_data.get('image'):
            title = event_data.get('title')
            image_path = f"events/{title}/{title}.jpg"
            blob = bucket.blob(image_path)
            if blob.exists():
                blob.delete()

        # Delete the event document
        event_ref.delete()

        return https_fn.Response({
            'message': 'Event deleted successfully',
            'eventId': event_id
        }, status=200)

    except Exception as e:
        print(f"Error deleting event: {str(e)}")
        return https_fn.Response({'error': str(e)}, status=500)

