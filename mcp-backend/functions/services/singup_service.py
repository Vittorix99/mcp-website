from firebase_admin import firestore
from utils.email_templates import get_signup_request_template, get_signup_request_text
import os
from services.mail_service import gmail_send_email_template
from config.firebase_config import db, bucket
import json
from datetime import datetime
import re
from utils.email_templates import get_membership_email_template, get_membership_email_text
from utils.pdf_template import generate_membership_pdf


def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


def is_adult(birthdate_str):
    try:
        birth_date = datetime.strptime(birthdate_str, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age >= 18
    except ValueError:
        return False


def create_signup_request(data):
    try:
        print("Received data:", data)   
        # Extract data from request
        first_name = data['firstName']
        last_name = data['lastName']
        email = data['email']
        dateBirth = data['dateBirth']
        questions = data['questions']  # Expecting a list of { question, answer }

        # Validate email format
        if not is_valid_email(email):
            return {'message': 'Invalid email format'}, 400

        # Validate birth date format and age
        #if not is_adult(dateBirth):
         #   return {'message': 'User must be at least 18 years old and provide a valid date in YYYY-MM-DD format'}, 400

        # Check if a signup request with the same email already exists
        existing_requests = db.collection('signup_requests').where('email', '==', email).limit(1).get()

        if len(existing_requests) > 0:
            return {'message': 'A signup request with this email already exists'}, 409  # 409 Conflict

        # Save signup request to Firestore
        doc_ref = db.collection('signup_requests').add({
            'firstName': first_name,
            'lastName': last_name,
            'email': email,
            'dateBirth': dateBirth,
            'questions': questions,
            'status': 'PENDING',
            'timestamp': firestore.SERVER_TIMESTAMP,
            "email_sent": False
        })

        doc_id = doc_ref[1].id

        html_content = get_signup_request_template(first_name)
        text_content = get_signup_request_text(first_name)

        subject = "Thank you for your interest in MCP Community!"

        # Send email
        message_sent = gmail_send_email_template(email, subject, text_content, html_content)

        if message_sent:
            # Update the email_sent field in the document
            db.collection('signup_requests').document(doc_id).update({'email_sent': True})
            print(f"Message sent successfully")
        else:
            print(f"Failed to send message")

        return {'message': 'Signup request received successfully'}, 200

    except KeyError as e:
        print(f"Missing required field: {str(e)}")
        return {'message': 'Missing required field', 'error': str(e)}, 400  # 400 Bad Request

    except Exception as e:
        print(f"An error occurred: {e}")
        return {'message': 'An internal error occurred', 'error': str(e)}, 500  # 500 Internal Server Error


def get_signup_requests(request_id=None):
    try:
        if request_id:
            doc = db.collection('signup_requests').document(request_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return {'request': data}, 200
            else:
                return {'message': 'Signup request not found'}, 404
        else:
            docs = db.collection('signup_requests').order_by('timestamp', direction=firestore.Query.DESCENDING).get()
            requests = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                requests.append(data)
            return {'requests': requests}, 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'message': 'An internal error occurred', 'error': str(e)}, 500


def update_signup_request(request_id, data):
    try:
        doc_ref = db.collection('signup_requests').document(request_id)
        doc = doc_ref.get()
        if not doc.exists:
            return {'message': 'Signup request not found'}, 404

        # Only allow updating certain fields
        allowed_fields = ['status', 'notes']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        doc_ref.update(update_data)
        return {'message': 'Signup request updated successfully'}, 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'message': 'An internal error occurred', 'error': str(e)}, 500


def delete_signup_request(request_id):
    try:
        doc_ref = db.collection('signup_requests').document(request_id)
        doc = doc_ref.get()
        if not doc.exists:
            return {'message': 'Signup request not found'}, 404

        doc_ref.delete()
        return {'message': 'Signup request deleted successfully'}, 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'message': 'An internal error occurred', 'error': str(e)}, 500


def accept_signup_request(request_id):
    try:
        doc_ref = db.collection('signup_requests').document(request_id)
        doc = doc_ref.get()
        if not doc.exists:
            return {'message': 'Signup request not found'}, 404

        request_data = doc.to_dict()
        if request_data['status'] != 'PENDING':
            return {'message': 'Signup request is not in PENDING status'}, 400

        # Update signup request status
        doc_ref.update({
            'status': 'ACCEPTED'
        })

        # Create new user in user_community collection
        user_data = {
            'firstName': request_data['firstName'],
            'lastName': request_data['lastName'],
            'email': request_data['email'],
            'age': request_data['age'],
            'questions': request_data['questions'],
            'joinDate': firestore.SERVER_TIMESTAMP
        }
        db.collection('user_community').add(user_data)
        email = request_data['email']
        db.collection('newsletter_signups').add({
            'email': email,
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        # Send acceptance email (optional)

        return {'message': 'Signup request accepted and user created successfully'}, 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'message': 'An internal error occurred', 'error': str(e)}, 500


def process_new_membership(membership_id, membership_data, sent_on_create=False):
    try:
        print(f"🚀 Processing membership {membership_id}")
        membership_data["membership_id"] = membership_id

        if not membership_data.get("subscription_valid"):
            return {"success": False, "error": "Subscription not valid"}

        # Se il PDF esiste già, esci
        if membership_data.get("card_url"):
            return {"success": False, "error": "Card already generated"}

        # 📄 Genera PDF tessera
        logo_path = "logos/logo_white.png"
        pattern_path = "patterns/FINAL MCP PATTERN - ORANGE.png"
        pdf_buffer = generate_membership_pdf(membership_data, logo_path, pattern_path)

        if not pdf_buffer:
            return {"success": False, "error": "PDF generation failed"}

        # Definisci i nomi del file
        name = membership_data.get("name", "user")
        surname = membership_data.get("surname", "")
        name_surname = f"{name}_{surname}_{membership_id}"

        # ☁️ Salva su Firebase Storage
        pdf_path = f"memberships/cards/{membership_id}.pdf"
        blob = bucket.blob(pdf_path)
        blob.upload_from_string(pdf_buffer.getvalue(), content_type="application/pdf")
        pdf_url = blob.public_url
        print(f"✅ PDF tessera salvato: {pdf_url}")

        # Si procede solo se sent_on_create è True
        if sent_on_create:
            subject = f"Tessera Associativa MCP"
            html_content = get_membership_email_template(membership_data, pdf_url)
            text_content = get_membership_email_text(membership_data)

            sent = gmail_send_email_template(
                membership_data["email"],
                subject,
                text_content,
                html_content,
                pdf_buffer,
                f"{name_surname}_tessera.pdf"
            )

            if not sent:
                print("❌ Email non inviata")
                return {"success": False, "error": "Email send failed"}

            # ✅ Se l’email è stata inviata, aggiorna il DB
            db.collection("memberships").document(membership_id).update({
                "membership_sent": True,
                "card_url": pdf_url,
                "card_storage_path": pdf_path
            })
            print(f"✅ Tessera inviata a {membership_data['email']}")

        else:
            # 🟡 Se non si invia, salvo solo il PDF e aggiorno il DB
            db.collection("memberships").document(membership_id).update({
                "membership_sent": False,
                "card_url": pdf_url,
                "card_storage_path": pdf_path
            })
            print("⚠️ Tessera generata ma non inviata (sent_on_create=False)")

        return {"success": True, "pdf_url": pdf_url, "storage_path": pdf_path}

    except Exception as e:
        print(f"❌ Errore in process_new_membership: {str(e)}")
        return {"success": False, "error": str(e)}



def update_membership_card(membership_id, updated_data):
    try:
        print(f"🔄 Rigenerazione tessera per {membership_id}")

        # 🔎 Verifica che il membro esista
        doc_ref = db.collection("memberships").document(membership_id)
        doc = doc_ref.get()

        if not doc.exists:
            return {"success": False, "error": "Membership non trovata"}

        current_data = doc.to_dict()
        merged_data = current_data.copy()
        merged_data.update(updated_data)
        merged_data["membership_id"] = membership_id

        if not merged_data.get("subscription_valid"):
            return {"success": False, "error": "Subscription non valida"}

        # 📄 Genera nuova tessera PDF
        logo_path = "logos/logo_white.png"
        pattern_path = "patterns/FINAL MCP PATTERN - ORANGE.png"
        pdf_buffer = generate_membership_pdf(merged_data, logo_path, pattern_path)

        if not pdf_buffer:
            return {"success": False, "error": "Generazione PDF fallita"}

        name = merged_data.get("name", "user")
        surname = merged_data.get("surname", "")
        name_surname = f"{name}_{surname}_{membership_id}"

        # 📦 Path storage
        pdf_path = f"memberships/cards/{membership_id}.pdf"
        blob = bucket.blob(pdf_path)
        blob.upload_from_string(pdf_buffer.getvalue(), content_type="application/pdf")
        pdf_url = blob.public_url
        print(f"✅ Tessera aggiornata salvata: {pdf_url}")

        # 🔁 Aggiorna Firestore
        doc_ref.update({
            "card_url": pdf_url,
            "card_storage_path": pdf_path,
            "membership_sent": False
        })

        return {"success": True, "pdf_url": pdf_url, "storage_path": pdf_path}

    except Exception as e:
        print(f"❌ Errore in update_membership_card: {str(e)}")
        return {"success": False, "error": str(e)}