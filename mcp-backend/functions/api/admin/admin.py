# functions/admin/create_admin.py

from firebase_admin import auth, firestore
from firebase_functions import https_fn
from firebase_admin import initialize_app
from config.firebase_config import cors, db,bucket, region
from services.admin.auth_services import  verify_admin_service, require_admin



@https_fn.on_request(cors=cors, region=region)
@require_admin
def create_admin(req: https_fn.Request) -> https_fn.Response:
    if req.method != 'POST':
        return https_fn.Response('Invalid request method', status=405)

    try:
        req_json = req.get_json()
        if not req_json or 'email' not in req_json or 'password' not in req_json:
            return https_fn.Response('Missing required fields', status=400)

        email = req_json['email']
        password = req_json['password']
        display_name = req_json.get('displayName', '')

        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            email_verified=True
        )

        auth.set_custom_user_claims(user.uid, {'admin': True})

        db.collection('admin_users').document(user.uid).set({
            'email': email,
            'displayName': display_name,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'createdBy': req.admin_token['uid']
        })

        return https_fn.Response({
            'message': 'Admin user created successfully',
            'uid': user.uid
        }, status=201)

    except auth.EmailAlreadyExistsError:
        return https_fn.Response('Email already exists', status=400)
    except ValueError as e:
        return https_fn.Response(f'Invalid argument: {str(e)}', status=400)
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        return https_fn.Response('An error occurred while creating the admin user', status=500)
    
    

@https_fn.on_request(cors=cors)
@require_admin
def get_all_admins(req: https_fn.Request) -> https_fn.Response:
    if req.method != 'GET':
        return https_fn.Response('Invalid request method', status=405)

    try:
        admin_users = db.collection('admin_users').get()
        admins = []
        for admin in admin_users:
            admin_data = admin.to_dict()
            admin_data['uid'] = admin.id
            admins.append(admin_data)

        return https_fn.Response({'admins': admins}, status=200)
    except Exception as e:
        print(f"Error fetching admin users: {str(e)}")
        return https_fn.Response('An error occurred while fetching admin users', status=500)

@https_fn.on_request(cors=cors)
@require_admin
def get_admin_by_id(req: https_fn.Request) -> https_fn.Response:
    if req.method != 'GET':
        return https_fn.Response('Invalid request method', status=405)

    try:
        admin_id = req.args.get('id')
        if not admin_id:
            return https_fn.Response('Missing admin ID', status=400)

        admin_doc = db.collection('admin_users').document(admin_id).get()
        if not admin_doc.exists:
            return https_fn.Response('Admin user not found', status=404)

        admin_data = admin_doc.to_dict()
        admin_data['uid'] = admin_doc.id

        return https_fn.Response(admin_data, status=200)
    except Exception as e:
        print(f"Error fetching admin user: {str(e)}")
        return https_fn.Response('An error occurred while fetching the admin user', status=500)




@https_fn.on_request(cors=cors)
@require_admin
def update_admin(req: https_fn.Request) -> https_fn.Response:
    if req.method != 'PUT':
        return https_fn.Response('Invalid request method', status=405)

    try:
        req_json = req.get_json()
        if not req_json or 'uid' not in req_json:
            return https_fn.Response('Missing required fields', status=400)

        admin_id = req_json['uid']
        update_data = {}

        if 'displayName' in req_json:
            update_data['displayName'] = req_json['displayName']

        if 'email' in req_json:
            update_data['email'] = req_json['email']

        if update_data:
            # Update in Firebase Auth
            auth.update_user(admin_id, **update_data)

            # Update in Firestore
            db.collection('admin_users').document(admin_id).update(update_data)



        return https_fn.Response({'message': 'Admin user updated successfully'}, status=200)
    except auth.UserNotFoundError:
        return https_fn.Response('Admin user not found', status=404)
    except ValueError as e:
        return https_fn.Response(f'Invalid argument: {str(e)}', status=400)
    except Exception as e:
        print(f"Error updating admin user: {str(e)}")
        return https_fn.Response('An error occurred while updating the admin user', status=500)


@https_fn.on_request(cors=cors)
@require_admin
def delete_admin(req: https_fn.Request) -> https_fn.Response:
    if req.method != 'DELETE':
        return https_fn.Response('Invalid request method', status=405)

    try:
        admin_id = req.args.get('id')
        if not admin_id:
            return https_fn.Response('Missing admin ID', status=400)

        # Delete from Firebase Auth
        auth.delete_user(admin_id)

        # Delete from Firestore
        db.collection('admin_users').document(admin_id).delete()

        return https_fn.Response({'message': 'Admin user deleted successfully'}, status=200)
    except auth.UserNotFoundError:
        return https_fn.Response('Admin user not found', status=404)
    except Exception as e:
        print(f"Error deleting admin user: {str(e)}")
        return https_fn.Response('An error occurred while deleting the admin user', status=500)
    


@https_fn.on_call()
def verify_admin(req: https_fn.CallableRequest) -> dict:
    """API to verify if a user is an admin"""
    return verify_admin_service(req)