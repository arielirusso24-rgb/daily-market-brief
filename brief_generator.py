# brief_generator.py
"""Generate market brief with Claude API - FIXED VERSION."""

import os
from datetime import datetime


def generate_executive_summary(market_data):
    """Generate brief market opening summary."""
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
        
        return f"""
🎯 MARKET OPENING CONTEXT

Markets show {direction} sentiment from yesterday's close. Major indices averaging {avg_change:+.2f}% change.
{'All major indices closed lower' if indices_down == 4 else 'Most indices showed weakness' if indices_down >= 2 else 'Markets showed strength'}.
Data reflects changes versus previous trading day's close.
"""
    
    return "Processing market data..."


def get_sector_summary(market_data):
    """Get sector performance summary."""
    if '_all_stocks' not in market_data:
        return {}
    
    sector_performance = {}
    for stock in market_data['_all_stocks']:
        sector = stock.get('sector')
        if sector and sector != 'Unknown':
            if sector not in sector_performance:
                sector_performance[sector] = []
            sector_performance[sector].append(stock['change_percent'])
    
    return {
        sector: round(sum(changes) / len(changes), 2)
        for sector, changes in sector_performance.items()
        if changes
    }


def generate_brief(market_data, headlines):
    """Generate market brief using Claude - SIMPLE VERSION."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        return "ERROR: ANTHROPIC_API_KEY not found in environment"
    
    try:
        # Import here to avoid any initialization issues
        from anthropic import Anthropic
        from market_data import BIG_MOVE_THRESHOLD
        
        # Initialize client with ONLY api_key - nothing else
        client = Anthropic(api_key=api_key)
        
        # Format market data
        market_lines = []
        for name, data in market_data.items():
            if not name.startswith('_') and data.get('is_index'):
                sign = "+" if data['change_percent'] >= 0 else ""
                market_lines.append(f"{name}: ${data['latest_price']:.2f} ({sign}{data['change_percent']:.2f}%)")
        
        # Format gainers / losers with business context + per-ticker news
        def format_movers(stocks):
            blocks = []
            for stock in stocks[:5]:
                sign = "+" if stock['change_percent'] >= 0 else ""
                block = [
                    f"{stock['name']} ({stock['symbol']}): ${stock['latest_price']:.2f} ({sign}{stock['change_percent']:.2f}%) | {stock.get('sector', 'N/A')}"
                ]
                if stock.get('business'):
                    block.append(f"   What they do: {stock['business']}")
                if stock.get('news'):
                    block.append("   Recent news: " + " | ".join(stock['news'][:3]))
                blocks.append("\n".join(block))
            return blocks

        gainers = format_movers(market_data.get('_gainers', []))
        losers = format_movers(market_data.get('_losers', []))
        
        # Format sectors
        sector_summary = get_sector_summary(market_data)
        sectors = [f"{sector}: {change:+.2f}%" for sector, change in sorted(sector_summary.items(), key=lambda x: x[1], reverse=True)[:8]]
        
        # Format headlines
        headline_texts = []
        if headlines:
            for h in headlines[:6]:
                headline_texts.append(f"- {h['title']} ({h['source']})")
        
        universe_size = market_data.get('_universe_size', 'the S&P 500')

        # Build prompt
        prompt = f"""Create a concise, professional market brief for {datetime.now().strftime("%B %d, %Y")}.
The gainers/losers below are the best- and worst-performing names out of {universe_size} S&P 500 companies scanned today, so they rotate daily. Each comes with a short description of what the company does and recent news headlines.

INDICES (vs previous close):
{chr(10).join(market_lines)}

TOP GAINERS:
{chr(10).join(gainers)}

TOP DECLINERS:
{chr(10).join(losers)}

SECTOR AVERAGES:
{chr(10).join(sectors)}

MARKET HEADLINES:
{chr(10).join(headline_texts) if headline_texts else "Limited headlines today"}

Write a SHORT brief (keep it tight - quality over length) with:

**KEY MOVERS** (one bullet per top gainer and top decliner)
- For each: one line on what the company does, then the likely reason it moved, grounded in the news provided. If a name moved more than {BIG_MOVE_THRESHOLD:.0f}%, give a clearer cause (earnings, guidance, M&A, analyst action, sector news). If the reason isn't in the data, say so briefly instead of inventing one.

**SECTOR SPOTLIGHT** (only if warranted)
- If one segment clearly stands out today (e.g. biotech, semiconductors, energy, mobility/EV, financials), add 2-3 sentences digging into what's driving it. If nothing stands out, write "No single segment dominated today." and move on.

**WHAT MATTERS TODAY** (1-2 sentences)
- The key takeaway for investors and any levels to watch.

Be specific with numbers, professional but plain English. Do not pad."""

        # Call API with minimal parameters
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract text
        brief_text = response.content[0].text
        
        print("✅ Brief generated successfully")
        return brief_text
        
    except Exception as e:
        error_msg = f"Brief generation failed: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg