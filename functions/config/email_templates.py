import os
from datetime import datetime


INSTAGRAM_URL = "https://www.instagram.com/musiconnectingpeople_"

LOGO_URL = os.getenv("LOGO_URL")

def get_newsletter_signup_template(email, logo_url, instagram_url):


    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to MCP Newsletter</title>
          <style>
    .logo {{
      max-width: 200px;
      margin-bottom: 30px;
    filter: invert(100%) brightness(0%);
    -webkit-filter: invert(100%);
    }}
  </style>
    </head>
    <body style="margin: 0; padding: 0; background-color: #000000;">
        <table role="presentation" width="100%" style="max-width: 600px; margin: 0 auto; background-color: #000000; color: #ffffff; font-family: Arial, sans-serif;">
            <tr>
                <td style="padding: 40px 20px; text-align: center;">
                    <!-- Logo -->
                    <img src="{LOGO_URL}" alt="MCP Logo" style="max-width: 200px; margin-bottom: 30px; " class="logo">
                    
                    <h1 style="color: #ff4500; margin-bottom: 20px;">Welcome to MCP Newsletter!</h1>
                    
                    <p style="color: #ffffff; font-size: 16px; line-height: 1.5; margin-bottom: 30px;">
                        Thank you for subscribing to our newsletter. Get ready to receive exclusive updates about our upcoming events and special announcements.
                    </p>
                    
                    <div style="margin: 40px 0; padding: 20px; border: 1px solid #ff4500; border-radius: 5px;">
                        <p style="color: #ff4500; font-size: 18px; margin: 0;">
                            Stay tuned for our next event!
                        </p>
                    </div>
                    
                    <p style="color: #999999; font-size: 14px;">
                        Follow us on social media:
                    </p>
                    
                    <!-- Social Links -->
                    <div style="margin: 20px 0;">
                        <a href="{instagram_url}" style="color: #ff4500; text-decoration: none; margin: 0 10px;">Instagram</a>
                    </div>
                    
                    <p style="color: #666666; font-size: 12px; margin-top: 40px;">
                        © {datetime.now().year} Music Connecting People. All rights reserved.<br>
                        You're receiving this email because you signed up for our newsletter.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

def get_newsletter_signup_text(email):
    return f"""
    Welcome to MCP Newsletter!

    Thank you for subscribing to our newsletter, {email}. Get ready to receive exclusive updates about our upcoming events and special announcements.

    Stay tuned for our next event!

    Follow us on social media:
    Instagram: https://instagram.com/mcp
    Facebook: https://facebook.com/mcp

    © {datetime.now().year} Music Connecting People. All rights reserved.
    You're receiving this email because you signed up for our newsletter.
    """


def get_ticket_email_template(ticket_data, event_data, pdf_url=None):
    """Generates an HTML email for the ticket purchase confirmation, including a PDF link if available."""

    pdf_download_html = f"""
        <p>📌 Click below to download your ticket:</p>
        <a class="button" href="{pdf_url}" target="_blank">Download Ticket</a>
    """ if pdf_url else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #000000;
                font-family: Arial, sans-serif;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 40px 20px;
                background-color: #000000;
                color: #ffffff;
                text-align: center;
            }}
            .logo {{
                max-width: 200px;
                margin-bottom: 30px;
            }}
            .header {{
                font-size: 24px;
                font-weight: bold;
                color: #ff4500;
                margin-bottom: 20px;
            }}
            .details {{
                margin: 30px 0;
                padding: 20px;
                border: 1px solid #ff4500;
                border-radius: 5px;
                text-align: left;
            }}
            .button {{
                display: inline-block;
                margin-top: 20px;
                padding: 12px 24px;
                color: #000000;
                background-color: #ff4500;
                border-radius: 5px;
                text-decoration: none;
                font-weight: bold;
            }}
            .footer {{
                margin-top: 40px;
                font-size: 12px;
                color: #666666;
            }}
            .social-links {{
                margin: 20px 0;
            }}
            .social-links a {{
                color: #ff4500;
                text-decoration: none;
                margin: 0 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Logo -->
            <img src="{LOGO_URL}" alt="MCP Logo" class="logo">
            
            <div class="header">🎟️ Your Ticket for {event_data.get("title")}</div>
            <p>Thank you for your purchase, {ticket_data.get("first_name")}!</p>
            
            <div class="details">
                <strong style="color: #ff4500;">Event Details:</strong><br>
                📅 Date: {event_data.get("date")}<br>
                ⏰ Time: {event_data.get("startTime")} - {event_data.get("endTime")}<br>
                📍 Location: {event_data.get("location")}<br>
                🎤 Lineup: {", ".join(event_data.get("lineup", []))}<br>
                <br>
                <strong style="color: #ff4500;">Your Ticket:</strong><br>
                👤 Name: {ticket_data.get("first_name")} {ticket_data.get("last_name")}<br>
                🆔 Ticket ID: {ticket_data.get("transaction_id")}<br>
                💳 Paid: {event_data.get("price")} EUR
            </div>

            {pdf_download_html}

            <div class="social-links">
                <p style="color: #999999;">Follow us on social media:</p>
                <a href="{os.getenv('INSTAGRAM_URL', '#')}">Instagram</a>
            </div>

            <div class="footer">
                <p>See you at the event! 🎶</p>
                <p>© {datetime.now().year} Music Connecting People. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    
def get_signup_request_template(first_name):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Thank You for Your Interest in MCP Community</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #000000;
                font-family: Arial, sans-serif;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 40px 20px;
                background-color: #000000;
                color: #ffffff;
            }}
            .logo {{
                max-width: 200px;
                margin-bottom: 30px;
            }}
            h1 {{
                color: #ff4500;
                margin-bottom: 20px;
            }}
            .content {{
                font-size: 16px;
                line-height: 1.5;
                margin-bottom: 30px;
            }}
            .footer {{
                margin-top: 40px;
                font-size: 12px;
                color: #666666;
            }}
            .social-link {{
                color: #ff4500;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <img src="{LOGO_URL}" alt="MCP Logo" class="logo">
            
            <h1>Hello {first_name}!</h1>
            
            <div class="content">
                <p>Thank you for your interest in joining the Music Connecting People community.</p>
                <p>We have received your application and our team is currently reviewing it.</p>
                <p>You will receive another email once your application has been processed.</p>
            </div>
            
            <p>Best regards,<br>The MCP Team</p>
            
            <div class="footer">
                <p>Follow us on social media:</p>
                <a href="{INSTAGRAM_URL}" class="social-link">Instagram</a>
                
                <p>© {datetime.now().year} Music Connecting People. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_welcome_email_template(first_name):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to MCP Community</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #000000;
                font-family: Arial, sans-serif;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 40px 20px;
                background-color: #000000;
                color: #ffffff;
            }}
            .logo {{
                max-width: 200px;
                margin-bottom: 30px;
            }}
            h1 {{
                color: #ff4500;
                margin-bottom: 20px;
            }}
            .content {{
                font-size: 16px;
                line-height: 1.5;
                margin-bottom: 30px;
            }}
            .footer {{
                margin-top: 40px;
                font-size: 12px;
                color: #666666;
            }}
            .social-link {{
                color: #ff4500;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <img src="{LOGO_URL}" alt="MCP Logo" class="logo">
            
            <h1>Welcome to MCP Community, {first_name}!</h1>
            
            <div class="content">
                <p>We're thrilled to have you join our community of music enthusiasts.</p>
                <p>As a member, you now have access to exclusive events, networking opportunities, and more.</p>
                <p>Stay tuned for upcoming events and announcements!</p>
            </div>
            
            <p>Best regards,<br>The MCP Team</p>
            
            <div class="footer">
                <p>Follow us on social media:</p>
                <a href="{INSTAGRAM_URL}" class="social-link">Instagram</a>
                
                <p>© {datetime.now().year} Music Connecting People. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

# Text versions of the emails
def get_signup_request_text(first_name):
    return f"""
    Hello {first_name}!

    Thank you for your interest in joining the Music Connecting People community.

    We have received your application and our team is currently reviewing it.
    You will receive another email once your application has been processed.

    Best regards,
    The MCP Team

    © {datetime.now().year} Music Connecting People. All rights reserved.
    """

def get_welcome_email_text(first_name):
    return f"""
    Welcome to MCP Community, {first_name}!

    We're thrilled to have you join our community of music enthusiasts.
    As a member, you now have access to exclusive events, networking opportunities, and more.
    Stay tuned for upcoming events and announcements!

    Best regards,
    The MCP Team

    © {datetime.now().year} Music Connecting People. All rights reserved.
    """