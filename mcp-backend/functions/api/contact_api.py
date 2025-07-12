from firebase_functions import https_fn
from config.firebase_config import cors
from firebase_functions.https_fn import Request, Response
from firebase_admin import auth
import json
from config.firebase_config import region
from services.contact_service import contact_us_service
from google.auth.exceptions import GoogleAuthError



@https_fn.on_request(cors=cors, region=region)
def contact_us(req):
    """API to handle contact form submissions"""
    if req.method != 'POST':
        return 'Invalid request method', 405

    req_json = req.get_json()
    if not req_json:
        return 'Invalid request', 400

    return contact_us_service(req_json)