# functions/api/signup_api.py

from firebase_functions import https_fn
from firebase_admin import initialize_app
from config.firebase_config import cors
from services.singup_service import create_signup_request
import json


@https_fn.on_request(cors=cors)
def signup_request(req: https_fn.Request) -> https_fn.Response:
    """API to handle community signup requests"""
    if req.method != 'POST':
        return https_fn.Response('Invalid request method', status=405)

    try:
        req_json = req.get_json()
    except ValueError:
        return https_fn.Response('Invalid JSON', status=400)

    if not req_json:
        return https_fn.Response('Missing request body', status=400)

    required_fields = ['firstName', 'lastName', 'email', 'instagram']
    if not all(field in req_json for field in required_fields):
        return https_fn.Response('Missing required fields', status=400)

    result, status_code = create_signup_request(req_json)
    
    # Convert the result to a JSON string
    result_json = json.dumps(result)
    
    # Create the response with the appropriate status code and JSON content
    response = https_fn.Response(result_json)
    response.status = status_code
    response.headers['Content-Type'] = 'application/json'
    
    return response