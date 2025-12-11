from config.firebase_config import db, bucket
from services.mail_service import gmail_send_email_template
from utils.email_templates import get_membership_email_template, get_membership_email_text
from utils.pdf_template import generate_membership_pdf


def process_new_membership(membership_id, membership_data, sent_on_create=False):
    """
    Generate a membership card PDF, optionally send it via email, and update Firestore.
    """
    try:
        print(f"🚀 Processing membership {membership_id}")
        membership_data["membership_id"] = membership_id

        if not membership_data.get("subscription_valid"):
            return {"success": False, "error": "Subscription not valid"}

        if membership_data.get("card_url"):
            return {"success": False, "error": "Card already generated"}

        logo_path = "logos/logo_white.png"
        pattern_path = "patterns/FINAL MCP PATTERN - ORANGE.png"
        pdf_buffer = generate_membership_pdf(membership_data, logo_path, pattern_path)

        if not pdf_buffer:
            return {"success": False, "error": "PDF generation failed"}

        name = membership_data.get("name", "user")
        surname = membership_data.get("surname", "")
        name_surname = f"{name}_{surname}_{membership_id}"

        pdf_path = f"memberships/cards/{membership_id}.pdf"
        blob = bucket.blob(pdf_path)
        blob.upload_from_string(pdf_buffer.getvalue(), content_type="application/pdf")
        pdf_url = blob.public_url
        print(f"✅ PDF tessera salvato: {pdf_url}")

        if sent_on_create:
            subject = "Tessera Associativa MCP"
            html_content = get_membership_email_template(membership_data, pdf_url)
            text_content = get_membership_email_text(membership_data)

            sent = gmail_send_email_template(
                membership_data["email"],
                subject,
                text_content,
                html_content,
                pdf_buffer,
                f"{name_surname}_tessera.pdf",
            )

            if not sent:
                print("❌ Email non inviata")
                return {"success": False, "error": "Email send failed"}

            db.collection("memberships").document(membership_id).update(
                {
                    "membership_sent": True,
                    "card_url": pdf_url,
                    "card_storage_path": pdf_path,
                }
            )
            print(f"✅ Tessera inviata a {membership_data['email']}")
        else:
            db.collection("memberships").document(membership_id).update(
                {
                    "membership_sent": False,
                    "card_url": pdf_url,
                    "card_storage_path": pdf_path,
                }
            )
            print("⚠️ Tessera generata ma non inviata (sent_on_create=False)")

        return {"success": True, "pdf_url": pdf_url, "storage_path": pdf_path}

    except Exception as e:
        print(f"❌ Errore in process_new_membership: {str(e)}")
        return {"success": False, "error": str(e)}


def update_membership_card(membership_id, updated_data):
    """
    Regenerate a membership card PDF and update Firestore.
    """
    try:
        print(f"🔄 Rigenerazione tessera per {membership_id}")

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

        logo_path = "logos/logo_white.png"
        pattern_path = "patterns/FINAL MCP PATTERN - ORANGE.png"
        pdf_buffer = generate_membership_pdf(merged_data, logo_path, pattern_path)

        if not pdf_buffer:
            return {"success": False, "error": "Generazione PDF fallita"}

        name = merged_data.get("name", "user")
        surname = merged_data.get("surname", "")
        name_surname = f"{name}_{surname}_{membership_id}"

        pdf_path = f"memberships/cards/{membership_id}.pdf"
        blob = bucket.blob(pdf_path)
        blob.upload_from_string(pdf_buffer.getvalue(), content_type="application/pdf")
        pdf_url = blob.public_url
        print(f"✅ Tessera aggiornata salvata: {pdf_url}")

        doc_ref.update(
            {
                "card_url": pdf_url,
                "card_storage_path": pdf_path,
                "membership_sent": False,
            }
        )

        return {"success": True, "pdf_url": pdf_url, "storage_path": pdf_path}

    except Exception as e:
        print(f"❌ Errore in update_membership_card: {str(e)}")
        return {"success": False, "error": str(e)}
