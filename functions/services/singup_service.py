# functions/services/signup_service.py

from firebase_admin import firestore
from config.email_templates import get_signup_request_template, get_signup_request_text
import os
from services.mail_service import gmail_send_email_template
from config.firebase_config import db
import json


from firebase_admin import firestore

def create_signup_request(data):
    try:
        # Extract data from request
        first_name = data['firstName']
        last_name = data['lastName']
        email = data['email']
        instagram = data['instagram']

        # Check if a signup request with the same email already exists
        existing_requests = db.collection('signup_requests').where('email', '==', email).limit(1).get()
        
        if len(existing_requests) > 0:
            return {'message': 'A signup request with this email already exists'}, 409  # 409 Conflict

        # Save signup request to Firestore
        doc_ref = db.collection('signup_requests').add({
            'firstName': first_name,
            'lastName': last_name,
            'email': email,
            'instagram': instagram,
            'status': 'PENDING',
            'timestamp': firestore.SERVER_TIMESTAMP, 
            "email_sent": False
        })

        doc_id = doc_ref[1].id

        html_content = get_signup_request_template(first_name)
        text_content = get_signup_request_text(first_name)

        subject = "Thank you for your interest in MCP Community!"

        # Send email
        message_sent = gmail_send_email_template(email, subject, text_content, html_content)
        
        if message_sent:
            # Update the email_sent field in the document
            db.collection('signup_requests').document(doc_id).update({'email_sent': True})
            print(f"Message sent successfully")
        else:
            print(f"Failed to send message")
            
        return {'message': 'Signup request received successfully'}, 200

    except KeyError as e:
        print(f"Missing required field: {str(e)}")
        return {'message': 'Missing required field', 'error': str(e)}, 400  # 400 Bad Request

    except Exception as e:
        print(f"An error occurred: {e}")
        return {'message': 'An internal error occurred', 'error': str(e)}, 500  # 500 Internal Server Error
    
    

def get_signup_requests(request_id=None):
    try:
        if request_id:
            doc = db.collection('signup_requests').document(request_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return {'request': data}, 200
            else:
                return {'message': 'Signup request not found'}, 404
        else:
            docs = db.collection('signup_requests').order_by('timestamp', direction=firestore.Query.DESCENDING).get()
            requests = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                requests.append(data)
            return {'requests': requests}, 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'message': 'An internal error occurred', 'error': str(e)}, 500

def update_signup_request(request_id, data):
    try:
        doc_ref = db.collection('signup_requests').document(request_id)
        doc = doc_ref.get()
        if not doc.exists:
            return {'message': 'Signup request not found'}, 404

        # Only allow updating certain fields
        allowed_fields = ['status', 'notes']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        doc_ref.update(update_data)
        return {'message': 'Signup request updated successfully'}, 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'message': 'An internal error occurred', 'error': str(e)}, 500

def delete_signup_request(request_id):
    try:
        doc_ref = db.collection('signup_requests').document(request_id)
        doc = doc_ref.get()
        if not doc.exists:
            return {'message': 'Signup request not found'}, 404

        doc_ref.delete()
        return {'message': 'Signup request deleted successfully'}, 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'message': 'An internal error occurred', 'error': str(e)}, 500

def accept_signup_request(request_id):
    try:
        doc_ref = db.collection('signup_requests').document(request_id)
        doc = doc_ref.get()
        if not doc.exists:
            return {'message': 'Signup request not found'}, 404

        request_data = doc.to_dict()
        if request_data['status'] != 'PENDING':
            return {'message': 'Signup request is not in PENDING status'}, 400

        # Update signup request status
        doc_ref.update({
            'status': 'ACCEPTED'
        })

        # Create new user in user_community collection
        user_data = {
            'firstName': request_data['firstName'],
            'lastName': request_data['lastName'],
            'email': request_data['email'],
            'instagram': request_data['instagram'],
            'joinDate': firestore.SERVER_TIMESTAMP
        }
        db.collection('user_community').add(user_data)
        email = request_data['email']
        db.collection('newsletter_signups').add({
            'email': email,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        

        # Send acceptance email


        return {'message': 'Signup request accepted and user created successfully'}, 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'message': 'An internal error occurred', 'error': str(e)}, 500