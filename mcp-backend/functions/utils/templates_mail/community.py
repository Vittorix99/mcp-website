import os
from datetime import datetime


INSTAGRAM_URL = "https://www.instagram.com/musiconnectingpeople_"
LOGO_URL = os.getenv("LOGO_URL")


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
