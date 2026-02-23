# brief_generator.py
"""Generate comprehensive market brief with enhanced analysis."""

import os
from anthropic import Anthropic
from datetime import datetime
from market_data import get_sector_summary


def generate_executive_summary(market_data):
    """
    Generate a brief executive summary of market conditions.
    """
    # Get main indices
    indices_down = 0
    indices_total = 0
    avg_change = 0
    
    for name, data in market_data.items():
        if not name.startswith('_') and data.get('is_index'):
            indices_total += 1
            if data['change_percent'] < 0:
                indices_down += 1
            avg_change += data['change_percent']
    
    if indices_total > 0:
        avg_change = avg_change / indices_total
        
        direction = "negative" if indices_down >= 3 else "positive" if indices_down == 0 else "mixed"
        
        summary = f"""
🎯 MARKET OPENING CONTEXT

Markets reflect {direction} sentiment from yesterday's close. Major indices are averaging {avg_change:+.2f}% change. 
{'All major indices closed lower' if indices_down == 4 else 'Most indices showed weakness' if indices_down >= 2 else 'Markets showed relative strength'}, 
with the data showing movements relative to the previous trading day's close.

Key levels to watch: S&P 500 support at current levels, with {abs(avg_change):.1f}% moves indicating {'elevated volatility' if abs(avg_change) > 1 else 'normal trading conditions'}.
"""
        return summary
    
    return "Market data processing..."


def generate_brief(market_data, headlines):
    """
    Generate comprehensive market brief with geopolitical context.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "ERROR: ANTHROPIC_API_KEY not found in environment variables"
    
    try:
        client = Anthropic(api_key=api_key)
        
        # Get sector performance
        sector_summary = get_sector_summary(market_data)
        
        # Format market overview
        market_summary = []
        
        # Collect indices data
        for name, data in market_data.items():
            if not name.startswith('_') and data.get('is_index'):
                sign = "+" if data['change_percent'] >= 0 else ""
                market_summary.append(
                    f"{name}: ${data['latest_price']:.2f} ({sign}{data['change_percent']:.2f}%) vs previous close"
                )
        
        # Format gainers with prices
        gainers_text = ""
        if '_gainers' in market_data and market_data['_gainers']:
            gainers_text = "\n\nTOP GAINERS:\n" + "\n".join([
                f"- {stock['name']} ({stock['symbol']}): ${stock['latest_price']:.2f} (+{stock['change_percent']:.2f}%) | {stock.get('sector', 'N/A')}"
                for stock in market_data['_gainers']
            ])
        
        # Format losers with prices
        losers_text = ""
        if '_losers' in market_data and market_data['_losers']:
            losers_text = "\n\nTOP DECLINERS:\n" + "\n".join([
                f"- {stock['name']} ({stock['symbol']}): ${stock['latest_price']:.2f} ({stock['change_percent']:.2f}%) | {stock.get('sector', 'N/A')}"
                for stock in market_data['_losers']
            ])
        
        # Format sectors
        sector_text = ""
        if sector_summary:
            sorted_sectors = sorted(sector_summary.items(), key=lambda x: x[1], reverse=True)
            sector_text = "\n\nSECTOR PERFORMANCE:\n" + "\n".join([
                f"- {sector}: {change:+.2f}%"
                for sector, change in sorted_sectors[:10]
            ])
        
        # Format headlines with summaries
        headlines_text = ""
        if headlines:
            headlines_text = "\n\nKEY HEADLINES & SUMMARIES:\n" + "\n".join([
                f"{i+1}. {h['title']}\n   Source: {h['source']}\n   Summary: {h.get('description', 'Full article available at link')}"
                for i, h in enumerate(headlines[:8])
            ])
        else:
            headlines_text = "\n\nNOTE: Limited headline availability today."
        
        # Create enhanced prompt
        prompt = f"""You are a senior Wall Street analyst creating a morning market brief for {datetime.now().strftime("%B %d, %Y")}.

MARKET DATA (yesterday's close, showing change vs previous day):
{chr(10).join(market_summary)}
{gainers_text}
{losers_text}
{sector_text}
{headlines_text}

Create a professional market brief with these sections:

**1. KEY MARKET MOVERS** (5-7 bullets)
- Analyze top gainers/losers with SPECIFIC reasons
- Connect to broader themes (earnings, sector rotation, macro)
- Use exact numbers from the data

**2. GEOPOLITICAL & MACRO CONTEXT** (3-4 bullets)
- Identify international developments from headlines
- Central bank actions, economic data, policy changes
- If headlines limited, note "Markets focused on domestic factors..."

**3. SECTOR ANALYSIS** (3-4 bullets)
- Leading/lagging sectors with explanations
- Emerging trends and rotation patterns
- Defensive vs growth positioning

**4. WHAT MATTERS TODAY** (2-3 sentences)
- Key takeaway for investors
- Levels and catalysts to watch
- Risk/opportunity balance

Be SPECIFIC with data, explain causality, professional Bloomberg tone."""

        # Call Claude API (corrected - no proxies parameter)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text
        
    except Exception as e:
        error_msg = f"Brief generation error: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg
