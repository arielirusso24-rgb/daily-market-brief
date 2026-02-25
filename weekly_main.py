# weekly_main.py
"""Weekly Market Brief - Main Entry Point"""

import os
from datetime import datetime
from dotenv import load_dotenv
from weekly_brief_generator import generate_weekly_brief, get_weekly_performance
from email_sender import send_email_brief


def main():
    """Generate and send weekly market summary."""
    print("📅 Weekly Market Summary")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    load_dotenv()
    
    # Get weekly performance
    print("📊 Calculating weekly performance...")
    weekly_perf = get_weekly_performance()
    
    perf_text = "WEEKLY PERFORMANCE:\n" + "=" * 70 + "\n"
    for name, data in weekly_perf.items():
        sign = "+" if data['change'] >= 0 else ""
        perf_text += f"{name}: {sign}{data['change']:.2f}%\n"
    
    print(perf_text)
    
    # Generate weekly brief
    print("🤖 Generating weekly analysis...")
    brief = generate_weekly_brief()
    
    print("=" * 80)
    print("📋 WEEKLY MARKET BRIEF")
    print("=" * 80)
    print(brief)
    print("=" * 80)
    
    # Send email
    print("\n📧 Sending weekly summary...")
    week_start = datetime.now()
    email_subject = f"📅 Weekly Market Summary - Week of {week_start.strftime('%B %d, %Y')}"
    
    # Use simple format for weekly
    send_email_brief(email_subject, perf_text, [], brief)
    
    print("\n✨ Weekly summary sent!\n")


if __name__ == "__main__":
    main()
