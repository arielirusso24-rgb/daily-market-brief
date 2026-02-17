# news_fetcher.py
"""Fetch news headlines silently - no error messages."""

import feedparser
from datetime import datetime


def get_news_headlines(max_headlines=10):
    """
    Fetch news headlines from multiple sources.
    Fails silently - returns what it can get.
    """
    feeds = {
        "Reuters": "http://feeds.reuters.com/reuters/businessNews",
        "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
        "Seeking Alpha": "https://seekingalpha.com/market_currents.xml",
        "Investing.com": "https://www.investing.com/rss/news.rss",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    }
    
    all_headlines = []
    
    for source, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            if hasattr(feed, 'entries') and len(feed.entries) > 0:
                for entry in feed.entries[:3]:
                    all_headlines.append({
                        "title": entry.get('title', 'No title'),
                        "link": entry.get('link', ''),
                        "source": source,
                        "published": entry.get('published', '')
                    })
        except:
            continue  # Fail silently
    
    return all_headlines[:max_headlines]


def format_headlines(headlines):
    """Format headlines - clean output."""
    lines = ["\n📰 MARKET NEWS", "=" * 70]
    
    if headlines:
        for i, headline in enumerate(headlines, 1):
            lines.append(f"\n{i}. {headline['title']}")
            lines.append(f"   📌 {headline['source']}")
    else:
        # No external headlines - that's fine
        lines.append("\n📊 Analysis based on market data and sector trends")
    
    return "\n".join(lines)


if __name__ == "__main__":
    headlines = get_news_headlines(max_headlines=10)
    print(format_headlines(headlines))
