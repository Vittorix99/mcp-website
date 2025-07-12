from config.firebase_config import db
from google.cloud import firestore
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from services.mail_service import gmail_send_email

def contact_us_service(req_json):
    """Handles sending an email and saving contact message to Firestore"""

    try:
        if 'name' not in req_json or 'email' not in req_json or 'message' not in req_json:
            return {'error': 'Missing required fields'}, 400

        name = req_json['name']
        email = req_json['email']
        message = req_json['message']
        send_copy = req_json.get('send_copy', None)

        to_email = os.environ.get("USER_EMAIL")
        print(f"Sending email to {to_email}")

        subject = f'Contact Us Form Submission from {name}'
        body = f'Name: {name}\nEmail: {email}\n\n{message}'
        cc = email if send_copy else None

        send_message = gmail_send_email(to_email, subject, body)

        if send_message:
            print('Message sent successfully, saving to Firestore...')
            db.collection('contact_message').add({
                'name': name,
                'email': email,
                'message': message,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'answered':False
            })
            print('Message saved to Firestore')

            return {'message': 'Message sent successfully'}, 200
        else:
            return {'error': 'Failed to send message'}, 500

    except Exception as e:
        print(f'An error occurred: {e}')
        return {'error': f'ERROR IN SENDING MAIL: {str(e)}'}, 500