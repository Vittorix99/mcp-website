from firebase_functions import https_fn
from config.firebase_config import cors
from firebase_functions.https_fn import Request, Response
from firebase_admin import auth
import json
from config.firebase_config import region
from services.messages_service import MessagesService
from google.auth.exceptions import GoogleAuthError


messages_service = MessagesService()


@https_fn.on_request(cors=cors, region=region)
def contact_us(req):
    """API to handle contact form submissions"""
    if req.method != 'POST':
        return 'Invalid request method', 405

    req_json = req.get_json()
    if not req_json:
        return 'Invalid request', 400

    return messages_service.submit_contact_message(req_json)
