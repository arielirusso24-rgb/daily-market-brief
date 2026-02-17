# brief_generator.py
"""Generate comprehensive market brief - always provides value."""

import os
from anthropic import Anthropic
from datetime import datetime
from market_data import get_sector_summary


def generate_brief(market_data, headlines):
    """
    Generate comprehensive market brief.
    ALWAYS generates useful insights even without external news.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    
    client = Anthropic(api_key=api_key)
    
    # Get sector performance
    sector_summary = get_sector_summary(market_data)
    
    # Format market overview
    market_summary = []
    
    # Add indices
    for name, data in market_data.items():
        if not name.startswith('_') and data.get('is_index'):
            sign = "+" if data['change_percent'] >= 0 else ""
            status = "" if data.get('is_live') else f" (as of {data.get('latest_date')})"
            market_summary.append(f"{name}: ${data['latest_price']:,.2f} ({sign}{data['change_percent']:.2f}%){status}")
    
    # Add top gainers
    gainers_text = ""
    if '_gainers' in market_data and market_data['_gainers']:
        gainers_text = "\n\nTOP GAINERS:\n" + "\n".join([
            f"- {stock['name']} ({stock['symbol']}): +{stock['change_percent']:.2f}% | Sector: {stock.get('sector', 'N/A')}"
            for stock in market_data['_gainers']
        ])
    
    # Add top losers
    losers_text = ""
    if '_losers' in market_data and market_data['_losers']:
        losers_text = "\n\nTOP DECLINERS:\n" + "\n".join([
            f"- {stock['name']} ({stock['symbol']}): {stock['change_percent']:.2f}% | Sector: {stock.get('sector', 'N/A')}"
            for stock in market_data['_losers']
        ])
    
    # Add sector performance
    sector_text = ""
    if sector_summary:
        sorted_sectors = sorted(sector_summary.items(), key=lambda x: x[1], reverse=True)
        sector_text = "\n\nSECTOR PERFORMANCE:\n" + "\n".join([
            f"- {sector}: {change:+.2f}%"
            for sector, change in sorted_sectors[:10]
        ])
    
    # Format headlines (or note their absence)
    has_headlines = len(headlines) > 0
    if has_headlines:
        headlines_text = "\n\nRECENT HEADLINES:\n" + "\n".join([
            f"- {h['title']} ({h['source']})" 
            for h in headlines[:10]
        ])
    else:
        headlines_text = "\n\nNOTE: External news feeds temporarily unavailable. Analysis focuses on market data and sector trends."
    
    # Create comprehensive prompt
    prompt = f"""You are a senior Wall Street analyst creating a morning market brief for {datetime.now().strftime("%B %d, %Y")}.

MARKET DATA:
{chr(10).join(market_summary) if market_summary else "Market indices data processing..."}
{gainers_text}
{losers_text}
{sector_text}
{headlines_text}

Your task: Create a comprehensive, actionable market brief that provides real value to investors.

Structure your brief as follows:

**EXECUTIVE SUMMARY** (2-3 sentences)
- Overall market sentiment and direction
- Key drivers from the data available

**MARKET MOVERS & NOTABLE STOCKS** (5-7 bullets)
- Analyze the top gainers and losers
- Identify WHY certain stocks/sectors are moving
- Highlight companies showing interesting patterns
- Point out stocks in bullish sectors worth watching

**SECTOR ANALYSIS** (4-5 bullets)
- Which sectors are leading/lagging
- Emerging trends visible in sector performance
- Industries showing momentum
- Contrarian opportunities in oversold sectors

**INVESTMENT THEMES & OPPORTUNITIES** (4-5 bullets)
- Key themes emerging from market data
- Stocks positioned well in trending sectors
- Risk factors visible in the data
- Forward-looking catalysts to watch

**WHAT MATTERS TODAY** (1 paragraph)
- Synthesize the key takeaways
- Actionable insights for today's trading
- What investors should monitor

CRITICAL INSTRUCTIONS:
- Even without external news, provide deep analysis of stock movements and sector trends
- Be specific: mention actual stock symbols, percentages, and sector names
- Identify patterns: "Tech stocks showing strength with NVDA +X%, MSFT +Y%"
- Always provide actionable insights
- Connect market moves to broader themes (AI adoption, rate sensitivity, etc.)
- Professional, data-driven tone - Bloomberg/Barron's quality

Generate the brief NOW based on available data."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text
