# email_sender.py
"""Send market brief via email with HTML formatting."""

import os
import html
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def send_email_brief(subject, market_formatted, headlines_formatted, brief, to_email=None):
    """
    Send market brief via Gmail SMTP with HTML formatting.
    """
    from_email = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not from_email or not password:
        print("❌ Email credentials not found")
        return False
    
    if not to_email:
        to_email = from_email
    
    try:
        # Escape HTML in dynamic content
        market_safe = html.escape(market_formatted)
        headlines_safe = html.escape(headlines_formatted)
        brief_safe = html.escape(brief)
        
        # Create HTML email
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h2 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 5px; }}
                h3 {{ color: #34a853; margin-top: 20px; }}
                .index {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #1a73e8; margin: 10px 0; }}
                .gainer {{ color: #34a853; font-weight: bold; }}
                .loser {{ color: #ea4335; font-weight: bold; }}
                .news-item {{ margin: 10px 0; padding: 10px; background: #f8f9fa; }}
                .news-link {{ color: #1a73e8; text-decoration: none; }}
                .brief {{ background: #fff; padding: 20px; border: 1px solid #ddd; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <h2>📊 Daily Market Brief - {datetime.now().strftime("%B %d, %Y")}</h2>
            
            <div class="index">
                <pre>{market_safe}</pre>
            </div>
            
            <h3>📰 Market News & Headlines</h3>
            <div class="news-section">
                <pre>{headlines_safe}</pre>
            </div>
            
            <h3>📋 Professional Market Analysis</h3>
            <div class="brief">
                <pre style="white-space: pre-wrap; font-family: Arial, sans-serif;">{brief_safe}</pre>
            </div>
            
            <div class="footer">
                <p>Generated automatically by Daily Market Brief System</p>
                <p>Powered by yfinance, RSS feeds, and Claude AI</p>
            </div>
        </body>
        </html>
        """
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach HTML
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False
