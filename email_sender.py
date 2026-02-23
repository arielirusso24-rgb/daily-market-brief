# email_sender.py
"""Send market brief via email with properly formatted HTML."""

import os
import html
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def format_headlines_html(headlines):
    """Format headlines as HTML with clickable links."""
    html_content = ""
    for i, h in enumerate(headlines, 1):
        title = html.escape(h.get('title', ''))
        source = html.escape(h.get('source', ''))
        description = html.escape(h.get('description', ''))
        link = html.escape(h.get('link', '#'))
        
        html_content += f"""
        <div style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-left: 3px solid #1a73e8;">
            <div style="font-weight: bold; color: #333; margin-bottom: 5px;">{i}. {title}</div>
            <div style="color: #666; font-size: 13px; margin: 5px 0;">📌 {source}</div>
            <div style="color: #555; font-size: 13px; margin: 8px 0; line-height: 1.5;">{description}</div>
            <a href="{link}" style="color: #1a73e8; text-decoration: none; font-size: 13px;">🔗 Read full article →</a>
        </div>
        """
    return html_content


def send_email_brief(subject, market_formatted, headlines_list, brief, to_email=None):
    """Send market brief via Gmail SMTP with proper HTML formatting."""
    from_email = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not from_email or not password:
        print("❌ Email credentials not found")
        return False
    
    if not to_email:
        to_email = from_email
    
    try:
        # Format headlines as HTML
        headlines_html = format_headlines_html(headlines_list) if headlines_list else "<p>Limited headlines today</p>"
        
        # Escape HTML in plain-text content
        market_safe = html.escape(market_formatted)
        brief_safe = html.escape(brief)
        
        # Create HTML email
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; }}
                h2 {{ color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 10px; margin-top: 30px; }}
                h3 {{ color: #34a853; margin-top: 25px; }}
                .overview {{ background: #f8f9fa; padding: 20px; border-left: 5px solid #1a73e8; margin: 20px 0; white-space: pre-wrap; font-family: 'Courier New', monospace; font-size: 13px; }}
                .brief {{ background: #fff; padding: 20px; margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; white-space: pre-wrap; line-height: 1.8; }}
                .footer {{ margin-top: 40px; padding: 20px; border-top: 2px solid #ddd; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <h2>📊 Daily Market Brief - {datetime.now().strftime("%B %d, %Y")}</h2>
            
            <div class="overview">{market_safe}</div>
            
            <h3>📰 Market News & Headlines</h3>
            {headlines_html}
            
            <h3>📋 Professional Market Analysis</h3>
            <div class="brief">{brief_safe}</div>
            
            <div class="footer">
                <p><strong>Daily Market Brief System</strong></p>
                <p>Powered by yfinance · RSS feeds · Claude AI</p>
                <p>Automated analysis · Delivered daily at market open</p>
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
