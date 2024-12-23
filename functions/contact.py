from firebase_admin import auth
from firebase_functions import https_fn
from firebase_config import db, cors
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from mail import gmail_send_email

@https_fn.on_request(cors=cors)
def get_all_messages(req):
    if req.method != 'GET':
        return 'Invalid request method', 405
    
    try:

        messages = db.collection('contact_message').stream()
        messages_list = []
        for message in messages:
            print(f'{message.id} => {message.to_dict()}')
            messages_list.append(message.to_dict())
        return {'messages': messages_list}
    except Exception as e:
        print(f'An error occurred: {e}')
        return f'An error occurred ',

@https_fn.on_request(cors=cors)
def contact_us2(req):
    if req.method != 'POST':
        return 'Invalid request method', 405
    print("Request received")
    print("Current directory is: ", os.getcwd())

    req_json = req.get_json()
    if not req_json:
        return 'Invalid request', 400
    if 'name' not in req_json or 'email' not in req_json or 'message' not in req_json:
        return 'Missing required fields', 400
    
    name = req_json['name']
    email = req_json['email']
    message = req_json['message']
    send_copy = req_json['send_copy'] if 'send_copy' in req_json else None
    
    try:
        to_email =  os.environ.get("USER_EMAIL")
        print(f"Sending email to {to_email}")
        subject = f'Contact Us Form Submission from {name}'
        body = f'Name: {name}\nEmail: {email}\n\n{message}'
        cc =  email if send_copy else None
        send_message = gmail_send_email(to_email, subject, body)
        if send_message:
            print('Message sent successfully, trying to save to Firestore')
            db.collection('contact_message').add({
                'name': name,
                'email': email,
                'message': message, 
            })
            print('Message saved to Firestore')


            
            return 'Message sent successfully', 200
        else:
            return 'Failed to send message', 500
    except Exception as e:
        print(f'An error occurred: {e}')
        return f'ERROR IN SENDING MAIL: {e}', 500



