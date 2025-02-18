from firebase_functions import https_fn
from firebase_admin import initialize_app, firestore
from config.firebase_config import cors, db, bucket
from services.admin.auth_services import require_admin
from services.ticket_service import (
    create_ticket_service,
    get_tickets_service,
    update_ticket_service,
    delete_ticket_service,
    send_pdf_ticket_service,
    download_pdf_ticket_service, 
    create_new_pdf_ticket_service,
    delete_existing_pdf_ticket_service
)
from flask import send_file
import io
import logging





@https_fn.on_request(cors=cors)
@require_admin
def create_ticket(req: https_fn.Request) -> https_fn.Response:
    """Create a new ticket"""
    if req.method != 'POST':
        return https_fn.Response('Invalid request method', status=405)

    try:
        req_json = req.get_json()
        if not req_json:
            return https_fn.Response('Missing request body', status=400)

        result = create_ticket_service(req_json, req.admin_token['uid'])
        return https_fn.Response(result, status=201)

    except ValueError as e:
        return https_fn.Response({'error': str(e)}, status=400)
    except Exception as e:
        logging.exception("Error creating ticket")
        return https_fn.Response({'error': 'An unexpected error occurred'}, status=500)

@https_fn.on_request(cors=cors)
@require_admin
def get_tickets(req: https_fn.Request) -> https_fn.Response:
    """Get all tickets or a specific ticket"""
    if req.method != 'GET':
        return https_fn.Response('Invalid request method', status=405)

    try:
        ticket_id = req.args.get('id')
        event_id = req.args.get('event_id')
        result = get_tickets_service(ticket_id, event_id)
        return https_fn.Response(result, status=200)

    except ValueError as e:
        return https_fn.Response({'error': str(e)}, status=404)
    except Exception as e:
        logging.exception("Error fetching tickets")
        return https_fn.Response({'error': 'An unexpected error occurred'}, status=500)

@https_fn.on_request(cors=cors)
@require_admin
def update_ticket(req: https_fn.Request) -> https_fn.Response:
    """Update an existing ticket"""
    if req.method != 'PUT':
        return https_fn.Response('Invalid request method', status=405)

    try:
        req_json = req.get_json()
        if not req_json or 'id' not in req_json:
            return https_fn.Response('Missing ticket ID', status=400)

        result = update_ticket_service(req_json, req.admin_token['uid'])
        return https_fn.Response(result, status=200)

    except ValueError as e:
        return https_fn.Response({'error': str(e)}, status=400)
    except Exception as e:
        logging.exception("Error updating ticket")
        return https_fn.Response({'error': 'An unexpected error occurred'}, status=500)

@https_fn.on_request(cors=cors)
@require_admin
def delete_ticket(req: https_fn.Request) -> https_fn.Response:
    """Delete a ticket"""
    if req.method != 'DELETE':
        return https_fn.Response('Invalid request method', status=405)

    try:
        ticket_id = req.args.get('id')
        if not ticket_id:
            return https_fn.Response('Missing ticket ID', status=400)

        result = delete_ticket_service(ticket_id)
        return https_fn.Response(result, status=200)

    except ValueError as e:
        return https_fn.Response({'error': str(e)}, status=404)
    except Exception as e:
        logging.exception("Error deleting ticket")
        return https_fn.Response({'error': 'An unexpected error occurred'}, status=500)
    
    
    

@https_fn.on_request(cors=cors)
@require_admin
def send_pdf_ticket(req: https_fn.Request) -> https_fn.Response:
    """Send the PDF ticket to the user's email"""
    if req.method != 'POST':
        return https_fn.Response('Invalid request method', status=405)

    try:
        req_json = req.get_json()
        if not req_json or 'ticket_id' not in req_json:
            return https_fn.Response('Missing ticket ID', status=400)

        ticket_id = req_json['ticket_id']
        result = send_pdf_ticket_service(ticket_id)

        if result['success']:
            return https_fn.Response(result, status=200)
        else:
            return https_fn.Response({'error': result['error']}, status=400)

    except Exception as e:
        logging.exception("Error sending PDF ticket")
        return https_fn.Response({'error': 'An unexpected error occurred'}, status=500)

@https_fn.on_request(cors=cors)
def download_pdf_ticket(req: https_fn.Request) -> https_fn.Response:
    """Download the PDF ticket"""
    if req.method != 'GET':
        return https_fn.Response('Invalid request method', status=405)

    try:
        ticket_id = req.args.get('ticket_id')
        if not ticket_id:
            return https_fn.Response('Missing ticket ID', status=400)

        pdf_content, error = download_pdf_ticket_service(ticket_id)

        if pdf_content:
            return send_file(
                io.BytesIO(pdf_content),
                mimetype='application/pdf',
                as_attachment=True,
                attachment_filename=f'ticket_{ticket_id}.pdf'
            )
        else:
            return https_fn.Response({'error': error}, status=400)

    except Exception as e:
        logging.exception("Error downloading PDF ticket")
        return https_fn.Response({'error': 'An unexpected error occurred'}, status=500)




@https_fn.on_request(cors=cors)
@require_admin
def create_new_pdf_ticket(req: https_fn.Request) -> https_fn.Response:
    """Create a new PDF ticket if it doesn't already exist"""
    if req.method != 'POST':
        return https_fn.Response('Invalid request method', status=405)

    try:
        req_json = req.get_json()
        if not req_json or 'ticket_id' not in req_json:
            return https_fn.Response('Missing ticket ID', status=400)

        ticket_id = req_json['ticket_id']
        result = create_new_pdf_ticket_service(ticket_id, req.admin_token['uid'])

        if result['success']:
            return https_fn.Response(result, status=201)
        else:
            return https_fn.Response({'error': result['error']}, status=400)

    except Exception as e:
        logging.exception("Error creating new PDF ticket")
        return https_fn.Response({'error': 'An unexpected error occurred'}, status=500)

@https_fn.on_request(cors=cors)
@require_admin
def delete_existing_pdf_ticket(req: https_fn.Request) -> https_fn.Response:
    """Delete an existing PDF ticket from storage"""
    if req.method != 'DELETE':
        return https_fn.Response('Invalid request method', status=405)

    try:
        ticket_id = req.args.get('ticket_id')
        if not ticket_id:
            return https_fn.Response('Missing ticket ID', status=400)

        result = delete_existing_pdf_ticket_service(ticket_id, req.admin_token['uid'])

        if result['success']:
            return https_fn.Response(result, status=200)
        else:
            return https_fn.Response({'error': result['error']}, status=400)

    except Exception as e:
        logging.exception("Error deleting existing PDF ticket")
        return https_fn.Response({'error': 'An unexpected error occurred'}, status=500)