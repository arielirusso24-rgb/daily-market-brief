# news_fetcher.py
"""Fetch news headlines from a diverse set of RSS feeds.

Pulls from many outlets (not just one), spreads the picks across sources so no
single feed dominates, and de-duplicates near-identical stories. Feeds are
fetched with a real User-Agent via requests, because several outlets block the
default feedparser client and return nothing otherwise.
"""

import re
import requests
import feedparser

try:
    import certifi
    _CA = certifi.where()
except Exception:
    _CA = True

# Diverse, currently-live feeds. Mix of markets-focused and general business so
# the brief isn't one outlet's worldview. (Reuters/AP public RSS were dropped -
# they no longer serve open feeds.)
FEEDS = {
    "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "CNBC Markets": "https://www.cnbc.com/id/20910258/device/rss/rss.html",
    "Investing.com": "https://www.investing.com/rss/news.rss",
    "BBC Business": "http://feeds.bbci.co.uk/news/business/rss.xml",
    "The Guardian": "https://www.theguardian.com/uk/business/rss",
    "NPR Business": "https://feeds.npr.org/1006/rss.xml",
    "Nasdaq": "https://www.nasdaq.com/feed/rssoutbound?category=Markets",
    "Fortune": "https://fortune.com/feed/",
    "Seeking Alpha": "https://seekingalpha.com/market_currents.xml",
}

_UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


def _clean(text, limit=220):
    """Strip HTML and trim a description."""
    if not text:
        return ""
    text = re.sub(r"<[^<]+?>", "", text).strip()
    return (text[:limit] + "...") if len(text) > limit else text


def _dedupe_key(title):
    """Normalized key to catch the same story syndicated across outlets."""
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()[:60]


def get_news_headlines(max_headlines=12, per_source=3):
    """Fetch headlines spread across sources, de-duplicated.

    Round-robins across feeds so the final list reflects many outlets instead of
    whichever feed happens to list the most items.
    """
    per_source_lists = {}

    for source, url in FEEDS.items():
        try:
            resp = requests.get(url, headers=_UA, timeout=15, verify=_CA)
            feed = feedparser.parse(resp.content)
            entries = getattr(feed, "entries", []) or []
            picked = []
            for entry in entries[: per_source + 2]:
                title = entry.get("title", "").strip()
                if not title:
                    continue
                description = _clean(entry.get("summary") or entry.get("description"))
                picked.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "source": source,
                    "description": description or "Click link for full story",
                    "published": entry.get("published", ""),
                })
                if len(picked) >= per_source:
                    break
            if picked:
                per_source_lists[source] = picked
        except Exception:
            continue

    # Round-robin across sources for diversity, de-duping syndicated stories.
    headlines, seen = [], set()
    for depth in range(per_source):
        for source in per_source_lists:
            if depth < len(per_source_lists[source]):
                item = per_source_lists[source][depth]
                key = _dedupe_key(item["title"])
                if key and key not in seen:
                    seen.add(key)
                    headlines.append(item)
                    if len(headlines) >= max_headlines:
                        return headlines

    return headlines[:max_headlines]


def format_headlines(headlines):
    """Format headlines with descriptions."""
    lines = ["\n📰 MARKET NEWS & HEADLINES", "=" * 70]

    if headlines:
        for i, headline in enumerate(headlines, 1):
            lines.append(f"\n{i}. {headline['title']}")
            lines.append(f"   📌 {headline['source']}")
            if headline.get("description"):
                lines.append(f"   📝 {headline['description']}")
            if headline.get("link"):
                lines.append(f"   🔗 {headline['link']}")
    else:
        lines.append("\n📊 Focusing on market data and sector trends today")

    return "\n".join(lines)


if __name__ == "__main__":
    headlines = get_news_headlines()
    print(f"Fetched {len(headlines)} headlines from "
          f"{len(set(h['source'] for h in headlines))} sources\n")
    print(format_headlines(headlines))
