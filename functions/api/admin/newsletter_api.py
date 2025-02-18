
# functions/api/newsletter_api.py

from firebase_functions import https_fn
from firebase_admin import initialize_app
from config.firebase_config import cors
from services.newsletter_service import newsletter_signup_service, get_newsletter_signups, update_newsletter_signup, delete_newsletter_signup
from services.admin.auth_service import require_admin
import json



@https_fn.on_request(cors=cors)
def newsletter_signup(req: https_fn.Request) -> https_fn.Response:
    """Public API to handle newsletter signups"""
    if req.method != 'POST':
        return https_fn.Response('Invalid request method', status=405)

    try:
        req_json = req.get_json()
    except ValueError:
        return https_fn.Response('Invalid JSON', status=400)

    if not req_json:
        return https_fn.Response('Missing request body', status=400)

    result, status_code = newsletter_signup_service(req_json)
    
    return https_fn.Response(json.dumps(result), status=status_code, content_type='application/json')

@https_fn.on_request(cors=cors)
@require_admin
def admin_get_newsletter_signups(req: https_fn.Request) -> https_fn.Response:
    """Admin API to get all newsletter signups or a specific one"""
    if req.method != 'GET':
        return https_fn.Response('Invalid request method', status=405)

    signup_id = req.args.get('id')
    result, status_code = get_newsletter_signups(signup_id)
    
    return https_fn.Response(json.dumps(result), status=status_code, content_type='application/json')

@https_fn.on_request(cors=cors)
@require_admin
def admin_update_newsletter_signup(req: https_fn.Request) -> https_fn.Response:
    """Admin API to update a newsletter signup"""
    if req.method != 'PUT':
        return https_fn.Response('Invalid request method', status=405)

    try:
        req_json = req.get_json()
    except ValueError:
        return https_fn.Response('Invalid JSON', status=400)

    if not req_json or 'id' not in req_json:
        return https_fn.Response('Missing request body or ID', status=400)

    signup_id = req_json.pop('id')
    result, status_code = update_newsletter_signup(signup_id, req_json)
    
    return https_fn.Response(json.dumps(result), status=status_code, content_type='application/json')

@https_fn.on_request(cors=cors)
@require_admin
def admin_delete_newsletter_signup(req: https_fn.Request) -> https_fn.Response:
    """Admin API to delete a newsletter signup"""
    if req.method != 'DELETE':
        return https_fn.Response('Invalid request method', status=405)

    signup_id = req.args.get('id')
    if not signup_id:
        return https_fn.Response('Missing signup ID', status=400)

    result, status_code = delete_newsletter_signup(signup_id)
    
    return https_fn.Response(json.dumps(result), status=status_code, content_type='application/json')