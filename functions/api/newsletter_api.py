from firebase_functions import https_fn
from config.firebase_config import cors
from services.newsletter_service import newsletter_signup_service

@https_fn.on_request(cors=cors)
def newsletter_signup(req):
    """API to handle newsletter signups"""
    if req.method != 'POST':
        return 'Invalid request method', 405

    req_json = req.get_json()
    if not req_json:
        return 'Missing request body', 400

    return newsletter_signup_service(req_json)