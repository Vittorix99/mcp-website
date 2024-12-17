import firebase_admin
from firebase_admin import credentials, firestore, auth
from firebase_functions import https_fn
from google.oauth2.credentials import Credentials
from firebase_functions import params


import base64
import os
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from google.oauth2 import service_account
from email.mime.text import MIMEText
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from mail import gmail_send_email
from firebase_functions import options








# Initialize Firebase app
cred = credentials.ApplicationDefault()

cred = credentials.Certificate("service-account.json")  # Path al tuo file JSON
firebase_admin.initialize_app(cred)


db = firestore.client()
cors = options.CorsOptions(
        cors_origins="*",
        cors_methods=["get", "post", "options"],)



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
        return 'An error occurred', 500

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

@https_fn.on_call()
def set_user_role(req: https_fn.CallableRequest) -> dict:
    # Check if the caller is an admin
    if not req.auth or not req.auth.token.get('admin', False):
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            message='Only admins can modify user roles.'
        )
    
    try:
        uid = req.data.get('uid')
        role = req.data.get('role')
        
        if not uid or not role:
            raise ValueError("Both uid and role are required")
            
        # Update user document in Firestore
        db.collection('users').document(uid).set({
            'role': role
        }, merge=True)
        return {'message': f'Successfully set role {role} for user {uid}'}
        
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f'Error setting user role: {str(e)}'
        )

@https_fn.on_call()
def create_admin(req: https_fn.CallableRequest) -> dict:
    if not req.auth or not req.auth.token.get('admin', False):
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            message='Only admins can create other admins.'
        )
    
    try:
        email = req.data.get('email')
        if not email:
            raise ValueError("Email is required")
            
        # Get user by email
        user = auth.get_user_by_email(email)
        
        # Update user document in Firestore
        db.collection('users').document(user.uid).set({
            'role': 'admin',
            'isAdmin': True
        }, merge=True)
        
        return {'message': f'Successfully made {email} an admin'}
        
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f'Error creating admin: {str(e)}'
        )

@https_fn.on_call()
def verify_admin(req: https_fn.CallableRequest) -> dict:
    if not req.auth:
        return {'isAdmin': False}
        
    try:
        user_ref = db.collection('users').document(req.auth.uid)
        user_data = user_ref.get().to_dict()
        
        return {
            'isAdmin': user_data.get('isAdmin', False),
            'role': user_data.get('role', 'user')
        }
        
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f'Error verifying admin status: {str(e)}'
        )