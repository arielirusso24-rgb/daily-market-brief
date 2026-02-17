# email_sender.py
"""Send market brief via email."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def send_email_brief(subject, body, to_email=None):
    """
    Send market brief via Gmail SMTP.
    """
    # Get credentials from environment
    from_email = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not from_email or not password:
        print("❌ Email credentials not found in .env file")
        return False
    
    # Use sender's email as recipient if not specified
    if not to_email:
        to_email = from_email
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        print(f"✅ Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


if __name__ == "__main__":
    # Test
    from dotenv import load_dotenv
    load_dotenv()
    
    send_email_brief(
        subject="Test Email",
        body="This is a test email from your Daily Market Brief system."
    )
