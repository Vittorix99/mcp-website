from firebase_functions import https_fn
from config.firebase_config import cors
from services.contact_service import get_all_messages_service, contact_us_service

@https_fn.on_request(cors=cors)
def get_all_messages(req):
    """API to fetch all contact messages"""
    if req.method != 'GET':
        return 'Invalid request method', 405

    return get_all_messages_service()

@https_fn.on_request(cors=cors)
def contact_us2(req):
    """API to handle contact form submissions"""
    if req.method != 'POST':
        return 'Invalid request method', 405

    req_json = req.get_json()
    if not req_json:
        return 'Invalid request', 400

    return contact_us_service(req_json)