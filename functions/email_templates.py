import os
from datetime import datetime


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
                    <img src="{logo_url}" alt="MCP Logo" style="max-width: 200px; margin-bottom: 30px; " class="logo">
                    
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