# news_fetcher.py
"""Fetch news headlines with descriptions from RSS feeds."""

import re
import feedparser
from datetime import datetime


def get_news_headlines(max_headlines=10):
    """
    Fetch news headlines with descriptions from multiple sources.
    """
    feeds = {
        "Reuters": "http://feeds.reuters.com/reuters/businessNews",
        "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
        "Seeking Alpha": "https://seekingalpha.com/market_currents.xml",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "Investing.com": "https://www.investing.com/rss/news.rss",
    }
    
    all_headlines = []
    
    for source, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            if hasattr(feed, 'entries') and len(feed.entries) > 0:
                for entry in feed.entries[:3]:
                    # Get description/summary
                    description = ""
                    if hasattr(entry, 'summary'):
                        # Clean HTML tags from summary
                        description = re.sub('<[^<]+?>', '', entry.summary)
                        description = description[:200] + "..." if len(description) > 200 else description
                    elif hasattr(entry, 'description'):
                        description = re.sub('<[^<]+?>', '', entry.description)
                        description = description[:200] + "..." if len(description) > 200 else description
                    
                    headline = {
                        "title": entry.get('title', 'No title'),
                        "link": entry.get('link', ''),
                        "source": source,
                        "description": description or "Click link for full story",
                        "published": entry.get('published', '')
                    }
                    all_headlines.append(headline)
        except:
            continue
    
    return all_headlines[:max_headlines]


def format_headlines(headlines):
    """Format headlines with descriptions."""
    lines = ["\n📰 MARKET NEWS & HEADLINES", "=" * 70]
    
    if headlines:
        for i, headline in enumerate(headlines, 1):
            lines.append(f"\n{i}. {headline['title']}")
            lines.append(f"   📌 {headline['source']}")
            if headline.get('description'):
                lines.append(f"   📝 {headline['description']}")
            if headline.get('link'):
                lines.append(f"   🔗 {headline['link']}")
    else:
        lines.append("\n📊 Focusing on market data and sector trends today")
    
    return "\n".join(lines)


if __name__ == "__main__":
    headlines = get_news_headlines(max_headlines=10)
    print(format_headlines(headlines))
