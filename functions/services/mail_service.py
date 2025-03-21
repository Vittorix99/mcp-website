import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from firebase_functions import params
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


# Recupera le variabili dall'ambiente Firebase
import os

def get_mail_info():
    """
    Recupera le variabili di ambiente di Firebase.
    """
    return {
        "SCOPES": os.environ.get("SCOPES", "").split(","),
        "SERVICE_ACCOUNT_FILE": os.environ.get("SERVICE_MAIL_FILE"),
        "USER_EMAIL": os.environ.get("USER_EMAIL"),
        "ACCESS_TOKEN": os.environ.get("ACCESS_TOKEN"),
        "REFRESH_TOKEN": os.environ.get("REFRESH_TOKEN"),
        "CLIENT_ID": os.environ.get("CLIENT_ID"),
        "CLIENT_SECRET": os.environ.get("CLIENT_SECRET"),
    }

# Test delle variabili
if __name__ == "__main__":
    mail_info = get_mail_info()



def gmail_send_email(to_email, subject, body):
    try:
        mail_info = get_mail_info()

        # Estrai le credenziali
        CLIENT_ID = mail_info["CLIENT_ID"]
        CLIENT_SECRET = mail_info["CLIENT_SECRET"]
        REFRESH_TOKEN = mail_info["REFRESH_TOKEN"]
        SCOPES = mail_info["SCOPES"]
        USER_EMAIL = mail_info["USER_EMAIL"]

        creds = Credentials(
            None,
            refresh_token=REFRESH_TOKEN,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES,
        )

        if creds.expired or not creds.valid:
            creds.refresh(Request())

        # Connettiti all'API Gmail
        service = build("gmail", "v1", credentials=creds)

        # Crea il messaggio email
        message = MIMEText(body)
        message["to"] = to_email
        message["from"] = USER_EMAIL
        message["subject"] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Invia il messaggio
        sent_message = service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        print(f"Message sent successfully: {sent_message}")
        return sent_message
    except Exception as e:
        print(f"An error occurred: {e}")
        raise e


def gmail_send_email_template(to_email, subject, text_content, html_content, attachment=None, attachment_name=None):
    try:
        mail_info = get_mail_info()

        # Extract credentials
        CLIENT_ID = mail_info["CLIENT_ID"]
        CLIENT_SECRET = mail_info["CLIENT_SECRET"]
        REFRESH_TOKEN = mail_info["REFRESH_TOKEN"]
        SCOPES = mail_info["SCOPES"]
        USER_EMAIL = mail_info["USER_EMAIL"]

        creds = Credentials(
            None,
            refresh_token=REFRESH_TOKEN,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES,
        )

        if creds.expired or not creds.valid:
            creds.refresh(Request())

        # Connect to Gmail API
        service = build("gmail", "v1", credentials=creds)

        # Create the root message
        message = MIMEMultipart('mixed')
        message['to'] = to_email
        message['from'] = USER_EMAIL
        message['subject'] = subject

        # Create the multipart/alternative child container
        msg_alternative = MIMEMultipart('alternative')
        message.attach(msg_alternative)

        # Attach the plain text and HTML versions to the multipart/alternative
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg_alternative.attach(part1)
        msg_alternative.attach(part2)

        # Attach PDF file if provided
        if attachment is not None and attachment_name is not None:
            part_pdf = MIMEApplication(attachment.getvalue(), Name=attachment_name)
            part_pdf['Content-Disposition'] = f'attachment; filename="{attachment_name}"'
            message.attach(part_pdf)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send email
        sent_message = service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        
        print(f"✅ Email sent successfully: {sent_message}")
        return sent_message  # ✅ Indicate success

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False  # ❌ Indicate failure