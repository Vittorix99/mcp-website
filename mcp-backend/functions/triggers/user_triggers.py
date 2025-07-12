from firebase_functions import firestore_fn
from firebase_admin import initialize_app, firestore
from config.email_templates import get_welcome_email_text, get_welcome_email_template
from services.mail_service import gmail_send_email_template
from config.firebase_config import db, cors, bucket


@firestore_fn.on_document_created(document="user_community/{userId}")
def on_new_user_created(event: firestore_fn.Event[firestore_fn.DocumentSnapshot]) -> None:
    """Triggered when a new user is added to the user_community collection"""
    new_user = event.data.to_dict()
    
    if new_user is None:
        print("Error: New user data is None")
        return

    try:
        # Prepare and send welcome email
        html_content = get_welcome_email_template(new_user['firstName'])
        text_content = get_welcome_email_text(new_user['firstName'])
        subject = "Welcome to MCP Community!"
        
        email_sent = gmail_send_email_template(new_user['email'], subject, text_content, html_content)
        
        if email_sent:
            print(f"Welcome email sent to {new_user['email']}")
            # Update the document to indicate that the email was sent
            event.data.reference.update({
                'welcomeEmailSent': True,
                'welcomeEmailSentAt': firestore.SERVER_TIMESTAMP
            })
        else:
            print(f"Failed to send welcome email to {new_user['email']}")
            # You might want to add some error handling or retry logic here
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")