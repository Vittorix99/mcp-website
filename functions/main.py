import firebase_admin
from firebase_admin import credentials, firestore, auth
from firebase_functions import https_fn
import base64
import os
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.oauth2 import service_account


# Initialize Firebase app
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
    'projectId': 'mcp-website-2a1ad',
})
db = firestore.client()

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
SERVICE_ACCOUNT_FILE = './service-account.json'


def gmail_send_email(to,subject,body, cc=None,):
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    try: 
        service = build('gmail', 'v1', credentials=creds)
        message = MIMEText(body)    
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = cc
        create_message = service.users().messages().send(userId='me', body={'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}).execute()
        print('Message Id: %s' % create_message['id'])
        return create_message
    except Exception as error:
        print(f'An error occurred: {error}')
        return None


@https_fn.on_call()
def contact_us(req):

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
        to_email = os.environ.get('CONTACT_EMAIL')
        subject = f'Contact Us Form Submission from {name}'
        body = f'Name: {name}\nEmail: {email}\n\n{message}'
        cc =  email if send_copy else None
        send_message = gmail_send_email(to_email, subject, body)
        if send_message:
            db = firestore.client()
            db.collection('contact_messages').add({
                'name': name,
                'email': email,
                'message': message, 
            })
            return 'Message sent successfully', 200
        else:
            return 'Failed to send message', 500
    except Exception as e:
        print(f'An error occurred: {e}')
        return 'An error occurred', 500

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