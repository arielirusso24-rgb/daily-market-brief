# brief_generator.py
"""Generate comprehensive market brief with enhanced analysis."""

import os
from anthropic import Anthropic
from datetime import datetime
from market_data import get_sector_summary


def generate_brief(market_data, headlines):
    """
    Generate comprehensive market brief with geopolitical context.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found")
    
    try:
        client = Anthropic(api_key=api_key)
        
        # Get sector performance
        sector_summary = get_sector_summary(market_data)
        
        # Format market overview
        market_summary = []
        indices_data = {}
        
        # Collect indices data
        for name, data in market_data.items():
            if not name.startswith('_') and data.get('is_index'):
                sign = "+" if data['change_percent'] >= 0 else ""
                indices_data[name] = {
                    'price': data['latest_price'],
                    'change': data['change_percent'],
                    'date': data.get('latest_date')
                }
                market_summary.append(
                    f"{name}: ${data['latest_price']:.2f} ({sign}{data['change_percent']:.2f}%)"
                )
        
        # Format gainers
        gainers_text = ""
        if '_gainers' in market_data and market_data['_gainers']:
            gainers_text = "\n\nTOP GAINERS:\n" + "\n".join([
                f"- {stock['name']} ({stock['symbol']}): +{stock['change_percent']:.2f}% | {stock.get('sector', 'N/A')}"
                for stock in market_data['_gainers']
            ])
        
        # Format losers
        losers_text = ""
        if '_losers' in market_data and market_data['_losers']:
            losers_text = "\n\nTOP DECLINERS:\n" + "\n".join([
                f"- {stock['name']} ({stock['symbol']}): {stock['change_percent']:.2f}% | {stock.get('sector', 'N/A')}"
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
        
        # Format headlines with better context
        headlines_text = ""
        if headlines:
            headlines_text = "\n\nKEY HEADLINES TODAY:\n" + "\n".join([
                f"- [{h['source']}] {h['title']}\n  Link: {h['link']}"
                for h in headlines[:10]
            ])
        else:
            headlines_text = "\n\nNOTE: Limited news availability. Focusing on market data analysis."
        
        # Create enhanced prompt
        prompt = f"""You are a senior Wall Street analyst creating a morning market brief for {datetime.now().strftime("%B %d, %Y")}.

MARKET DATA (as of previous close):
{chr(10).join(market_summary)}
{gainers_text}
{losers_text}
{sector_text}
{headlines_text}

Your task: Create a comprehensive, professional market brief with the following sections:

**1. MARKET OVERVIEW & OPENING CONTEXT** (3-4 sentences)
- Describe how markets opened today based on the data shown (which reflects the previous close)
- Explain the PRIMARY DRIVERS behind index movements (be specific - mention actual catalysts)
- Note if this is a continuation of a trend or a reversal
- Reference the actual percentage changes you see in the data

**2. KEY MARKET MOVERS** (5-7 bullets)
- Analyze top gainers and losers with SPECIFIC EXPLANATIONS
- Connect stock movements to broader themes (earnings, sector rotation, macro events)
- Identify sector patterns (e.g., "Technology weakness led by...")
- Mention specific percentage moves and why they matter

**3. GEOPOLITICAL & MACRO CONTEXT** (3-4 bullets)
- Based on the headlines provided, identify any:
  • International developments affecting markets (trade, conflicts, policy)
  • Central bank actions or monetary policy shifts
  • Economic data releases or policy announcements
  • Regulatory or political developments
- If headlines don't cover geopolitics, note "Limited geopolitical headlines today - focus remains on..."

**4. SECTOR ANALYSIS** (3-4 bullets)
- Which sectors are leading/lagging and WHY
- Emerging trends in bullish sectors
- Contrarian opportunities in oversold areas
- Rotation patterns (defensive vs growth, etc.)

**5. WHAT MATTERS TODAY** (2-3 sentences)
- Bottom line: What should investors focus on?
- Key levels or catalysts to watch
- Risk/opportunity assessment

CRITICAL INSTRUCTIONS:
- Be SPECIFIC with numbers (mention actual %changes, price levels)
- EXPLAIN causality - don't just state movements, say WHY
- Connect macro events to market action
- Professional Bloomberg/Barron's tone
- If data is from previous close, frame it as "Yesterday's close showed..."
- Base geopolitical analysis on actual headlines provided
- If brief on headlines, acknowledge it and focus on technical/sector analysis

Generate the brief NOW:"""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2500,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text
        
    except Exception as e:
        print(f"Error generating brief with Claude: {e}")
        return f"Brief generation encountered an error: {str(e)}\n\nPlease check the logs for details."
