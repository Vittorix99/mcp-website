from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from firebase_config import db, cors
from firebase_admin import auth
from firebase_functions import https_fn
from firebase_admin import firestore

import base64
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from mail import gmail_send_email, gmail_send_email_template
from email_templates import get_newsletter_signup_template, get_newsletter_signup_text




@https_fn.on_request(cors=cors) 
def newsletter_signup(req):
    if req.method != 'POST':
        return 'Invalid request method', 405

    req_json = req.get_json()
    if not req_json or 'email' not in req_json:
        return 'Missing required fields', 400

    email = req_json['email']
    try:
        # Salva l'email nel database
        db.collection('newsletter_signups').add({
            'email': email,
            'timestamp':firestore.SERVER_TIMESTAMP
        })

        # Prepara il contenuto dell'email
        logo_url = "https://musiconnectingpeople.com/logonew.png"   
        instagram_url = os.environ.get("INSTAGRAM_URL")
        
        html_content = get_newsletter_signup_template(email, logo_url, instagram_url)
        text_content = get_newsletter_signup_text(email)

        # Crea il messaggio email
        message = MIMEMultipart('alternative')
        message['to'] = email

        # Aggiungi sia versione testuale che HTML
        message.attach(MIMEText(text_content, 'plain'))
        message.attach(MIMEText(html_content, 'html'))

        # Converti il messaggio in formato raw
        subject = "Welcome to MCP Newsletter!"

        # Invia l'email
        gmail_send_email_template(email, subject, text_content, html_content)

        return 'Signed up for newsletter successfully', 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'error': str(e)}, 500