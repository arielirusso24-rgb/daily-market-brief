# weekly_brief_generator.py
"""Generate comprehensive weekly market summary."""

import os
from anthropic import Anthropic
from datetime import datetime, timedelta
import yfinance as yf


def get_weekly_performance():
    """Get weekly performance for major indices and stocks."""
    tickers = {
        "S&P 500": "SPY",
        "Nasdaq 100": "QQQ",
        "Dow Jones": "DIA",
        "Russell 2000": "IWM",
    }
    
    performance = {}
    
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            # Get 2 weeks of data to ensure we have full week
            hist = ticker.history(period="2wk")
            
            if len(hist) >= 6:  # Need 6+ days for week-over-week comparison
                week_start = hist['Close'].iloc[-6]  # 5 trading days ago
                week_end = hist['Close'].iloc[-1]
                change = ((week_end - week_start) / week_start) * 100
                
                performance[name] = {
                    'start': week_start,
                    'end': week_end,
                    'change': round(change, 2)
                }
        except Exception as e:
            print(f"Error getting {name}: {e}")
    
    return performance


def generate_weekly_brief():
    """Generate comprehensive weekly market summary."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        return "ERROR: ANTHROPIC_API_KEY not found"
    
    try:
        client = Anthropic(api_key=api_key)
        
        # Get weekly performance
        weekly_perf = get_weekly_performance()
        
        # Format weekly data
        weekly_summary = []
        for name, data in weekly_perf.items():
            sign = "+" if data['change'] >= 0 else ""
            weekly_summary.append(f"{name}: {sign}{data['change']:.2f}% this week")
        
        # Get current week dates
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = today
        
        prompt = f"""Create a comprehensive WEEKLY market summary for the week of {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}.

WEEKLY PERFORMANCE:
{chr(10).join(weekly_summary)}

Create a professional weekly brief with:

**📊 WEEK IN REVIEW** (3-4 sentences)
- Overall market direction this week
- Key themes that dominated trading
- Major sector rotations

**📈 WINNERS OF THE WEEK** (4-5 bullets)
- Sectors and stocks that outperformed
- Reasons for strength
- Notable earnings or catalysts

**📉 LOSERS OF THE WEEK** (3-4 bullets)
- Underperforming areas
- What weighed on these names
- Risk factors identified

**🌍 MACRO & GEOPOLITICAL HIGHLIGHTS** (3-4 bullets)
- Key economic data releases
- Fed/central bank actions or comments
- International developments
- Policy changes

**📅 WEEK AHEAD PREVIEW** (3-4 bullets)
- Upcoming earnings to watch
- Economic calendar highlights
- Potential market catalysts
- Technical levels to monitor

**💡 KEY TAKEAWAYS** (2-3 sentences)
- Main investment themes
- Positioning recommendations
- Risk/opportunity balance

Use professional Bloomberg/Barron's tone. Be specific with percentages and concrete examples."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
        
    except Exception as e:
        return f"Weekly brief generation failed: {str(e)}"


if __name__ == "__main__":
    print("Generating weekly brief...")
    brief = generate_weekly_brief()
    print(brief)
