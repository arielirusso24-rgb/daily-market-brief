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
        
        # Format headlines (title + short description for richer context)
        headline_texts = []
        if headlines:
            for h in headlines[:8]:
                line = f"- {h['title']} ({h['source']})"
                desc = h.get('description')
                if desc and desc != "Click link for full story":
                    line += f"\n    {desc}"
                headline_texts.append(line)
        
        universe_size = market_data.get('_universe_size', 'the S&P 500')

        # Voice/persona - keeps the brief sharp and human instead of robotic
        system_prompt = (
            "You write a daily markets newsletter that people actually enjoy reading - "
            "think the wit and clarity of Morning Brew or Matt Levine, with the credibility "
            "of a buy-side analyst. Your voice is conversational, sharp, and occasionally "
            "wry, but never goofy and never at the expense of accuracy. You explain WHY "
            "things happened in plain English, connect dots between stories, and respect the "
            "reader's intelligence and time. Hard rules: every number you cite must come from "
            "the data provided; never invent a catalyst - if the reason for a move isn't in "
            "the data, say so plainly; no hype, no filler, no generic 'investors are watching "
            "closely' clichés. Make it engaging through insight and clean writing, not "
            "exclamation marks."
        )

        # Build prompt
        prompt = f"""Here's today's market data for {datetime.now().strftime("%A, %B %d, %Y")}. The gainers and losers are the best and worst performers out of {universe_size} S&P 500 names scanned today (they rotate daily), each with a note on what the company does and recent headlines.

INDICES (vs previous close):
{chr(10).join(market_lines)}

TOP GAINERS:
{chr(10).join(gainers)}

TOP DECLINERS:
{chr(10).join(losers)}

SECTOR AVERAGES:
{chr(10).join(sectors)}

MARKET HEADLINES (from multiple outlets):
{chr(10).join(headline_texts) if headline_texts else "Limited headlines today"}

Write a substantial but readable brief (a full one-page read, not a tweet). Use these sections, with markdown headings exactly as written:

## The open
A punchy 3-4 sentence lede that captures the day's mood. Lead with the most interesting thing that happened, not a recap of index levels. Hook the reader, then set up what follows.

## What moved & why
Cover EVERY top gainer and decliner listed above - one tight bullet each. For each: who the company is in a few words, then the real reason it moved, grounded in the headlines provided. For moves above {BIG_MOVE_THRESHOLD:.0f}%, pin down the catalyst (earnings, guidance, M&A, analyst calls, sector news). If the data doesn't explain it, say so honestly - "no obvious catalyst; looks like momentum" beats a made-up reason.

## Sector spotlight
If a theme is clearly driving the day - biotech, semiconductors, energy, mobility/EV, financials, AI - spend 3-4 sentences on what's behind it, which names it's hitting, and why it matters. If nothing stands out, say so briefly and instead unpack the most interesting sector rotation in the data.

## The macro backdrop
3-4 sentences connecting today's market headlines to the bigger picture - rates, the economy, geopolitics, earnings season, whatever the news points to. Synthesize across the different outlets; don't just relist headlines.

## The bottom line
2-3 sentences: the takeaway worth remembering, plus specific things to watch next (levels, events, catalysts). Make it land."""

        # Call API
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            system=system_prompt,
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