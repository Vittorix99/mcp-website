import firebase_admin
from firebase_admin import credentials, firestore, auth
from firebase_functions import https_fn

# Initialize Firebase app
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
    'projectId': 'mcp-website-2a1ad',
})
db = firestore.client()

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