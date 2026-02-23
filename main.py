# main.py
"""Daily Market Brief - Main Entry Point"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from market_data import get_market_data, format_market_data
from news_fetcher import get_news_headlines, format_headlines
from brief_generator import generate_brief
from email_sender import send_email_brief


def setup_environment():
    """Load environment variables."""
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found")
        sys.exit(1)
    
    return api_key


def write_to_log(content, log_path="~/market_log.txt"):
    """Write to log file."""
    log_path = Path(log_path).expanduser()
    
    try:
        with open(log_path, 'a') as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n")
            f.write(content)
            f.write("\n")
        print(f"✅ Brief saved to {log_path}")
    except Exception as e:
        print(f"⚠️ Could not save to log: {e}")


def main():
    """Main execution - clean and professional."""
    print("🚀 Daily Market Brief")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    setup_environment()
    
    # Fetch market data
    print("📊 Loading market data...")
    market_data = get_market_data()
    market_formatted = format_market_data(market_data)
    print(market_formatted)
    
    # Fetch news
    print("\n📰 Checking news sources...")
    headlines = get_news_headlines(max_headlines=10)
    headlines_formatted = format_headlines(headlines)
    print(headlines_formatted)
    
    # Generate brief with Claude
    print("\n🤖 Generating market analysis...")
    try:
        brief = generate_brief(market_data, headlines)
        print("✅ Brief generated successfully\n")
        print("=" * 80)
        print("📋 DAILY MARKET BRIEF")
        print("=" * 80)
        print(brief)
        print("=" * 80)
    except Exception as e:
        print(f"❌ Error generating brief: {e}")
        brief = f"Brief generation failed: {str(e)}"
    
    # Save to log
    print("\n💾 Saving brief...")
    full_output = f"{market_formatted}\n\n{headlines_formatted}\n\n{'=' * 80}\n📋 DAILY MARKET BRIEF\n{'=' * 80}\n{brief}"
    write_to_log(full_output)
    
    # Send email
    print("📧 Sending email...")
    email_subject = f"Daily Market Brief - {datetime.now().strftime('%B %d, %Y')}"
    send_email_brief(email_subject, market_formatted, headlines_formatted, brief)
    
    print("\n✨ Done!\n")


if __name__ == "__main__":
    main()
