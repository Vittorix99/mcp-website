from firebase_functions import https_fn
from firebase_admin import initialize_app
from config.firebase_config import cors
from services.signup_service import create_signup_request, get_signup_requests, update_signup_request, delete_signup_request, accept_signup_request
from services.admin.auth_service import require_admin
import json
from config.firebase_config import region

@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_get_signup_requests(req: https_fn.Request) -> https_fn.Response:
    """Get all signup requests or a specific one"""
    if req.method != 'GET':
        return https_fn.Response('Invalid request method', status=405)

    request_id = req.args.get('id')
    result, status_code = get_signup_requests(request_id)
    
    return https_fn.Response(json.dumps(result), status=status_code, content_type='application/json')

@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_update_signup_request(req: https_fn.Request) -> https_fn.Response:
    """Update a signup request"""
    if req.method != 'PUT':
        return https_fn.Response('Invalid request method', status=405)

    try:
        req_json = req.get_json()
    except ValueError:
        return https_fn.Response('Invalid JSON', status=400)

    if not req_json or 'id' not in req_json:
        return https_fn.Response('Missing request body or ID', status=400)

    request_id = req_json.pop('id')
    result, status_code = update_signup_request(request_id, req_json)
    
    return https_fn.Response(json.dumps(result), status=status_code, content_type='application/json')

@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_delete_signup_request(req: https_fn.Request) -> https_fn.Response:
    """Delete a signup request"""
    if req.method != 'DELETE':
        return https_fn.Response('Invalid request method', status=405)

    request_id = req.args.get('id')
    if not request_id:
        return https_fn.Response('Missing request ID', status=400)

    result, status_code = delete_signup_request(request_id)
    
    return https_fn.Response(json.dumps(result), status=status_code, content_type='application/json')

@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_accept_signup_request(req: https_fn.Request) -> https_fn.Response:
    """Accept a signup request"""
    if req.method != 'POST':
        return https_fn.Response('Invalid request method', status=405)

    try:
        req_json = req.get_json()
    except ValueError:
        return https_fn.Response('Invalid JSON', status=400)

    if not req_json or 'id' not in req_json:
        return https_fn.Response('Missing request body or ID', status=400)

    request_id = req_json['id']
    result, status_code = accept_signup_request(request_id)
    
    return https_fn.Response(json.dumps(result), status=status_code, content_type='application/json')