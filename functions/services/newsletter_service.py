from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.firebase_config import db
from firebase_admin import firestore
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from services.mail_service import gmail_send_email_template
from config.email_templates import get_newsletter_signup_template, get_newsletter_signup_text

def newsletter_signup_service(req_json):
    """Handles storing user email and sending confirmation email"""
    try:
        if 'email' not in req_json:
            return {'error': 'Missing required fields'}, 400

        email = req_json['email']
        existing_signup = db.collection('newsletter_signups').where('email', '==', email).limit(1).get()
        
        

        # Save email to Firestore
        if len(existing_signup) == 0:
            db.collection('newsletter_signups').add({
                'email': email,
                'timestamp': firestore.SERVER_TIMESTAMP
            })

        # Prepare email content
        logo_url = "https://musiconnectingpeople.com/logonew.png"
        instagram_url = os.environ.get("INSTAGRAM_URL")

        html_content = get_newsletter_signup_template(email, logo_url, instagram_url)
        text_content = get_newsletter_signup_text(email)

        subject = "Welcome to MCP Newsletter!"

        # Send email
        gmail_send_email_template(email, subject, text_content, html_content)

        return {'message': 'Signed up for newsletter successfully'}, 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return {'error': str(e)}, 500
    
    


def get_newsletter_signups(signup_id=None):
    """Retrieve all newsletter signups or a specific one"""
    try:
        if signup_id:
            doc = db.collection('newsletter_signups').document(signup_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return {'signup': data}, 200
            else:
                return {'error': 'Newsletter signup not found'}, 404
        else:
            docs = db.collection('newsletter_signups').order_by('timestamp', direction=firestore.Query.DESCENDING).get()
            signups = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                signups.append(data)
            return {'signups': signups}, 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'error': 'An internal error occurred'}, 500

def update_newsletter_signup(signup_id, data):
    """Update a newsletter signup"""
    try:
        doc_ref = db.collection('newsletter_signups').document(signup_id)
        doc = doc_ref.get()
        if not doc.exists:
            return {'error': 'Newsletter signup not found'}, 404

        # Only allow updating 'active' field
        if 'active' in data:
            doc_ref.update({'active': data['active']})
            return {'message': 'Newsletter signup updated successfully'}, 200
        else:
            return {'error': 'No valid fields to update'}, 400
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'error': 'An internal error occurred'}, 500

def delete_newsletter_signup(signup_id):
    """Delete a newsletter signup"""
    try:
        doc_ref = db.collection('newsletter_signups').document(signup_id)
        doc = doc_ref.get()
        if not doc.exists:
            return {'error': 'Newsletter signup not found'}, 404

        doc_ref.delete()
        return {'message': 'Newsletter signup deleted successfully'}, 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'error': 'An internal error occurred'}, 500