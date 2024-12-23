from firebase_admin import auth
from firebase_functions import https_fn
from firebase_config import db, cors
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