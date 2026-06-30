# market_data.py
"""Fetch comprehensive market data.

Universe is the full S&P 500 (SPY constituents), pulled live so the
gainers/losers rotate every day instead of being a fixed hand-picked list.
Top movers are enriched with a short business description and recent
per-ticker news so the brief can explain *what* the company does and *why*
it moved.
"""

import io
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone


# Fallback universe used only if the live S&P 500 list can't be fetched.
# Kept small on purpose - just enough to produce a brief if Wikipedia/yahoo fail.
_FALLBACK_UNIVERSE = {
    "AAPL": ("Apple", "Information Technology"),
    "MSFT": ("Microsoft", "Information Technology"),
    "NVDA": ("Nvidia", "Information Technology"),
    "AMZN": ("Amazon", "Consumer Discretionary"),
    "GOOGL": ("Alphabet", "Communication Services"),
    "META": ("Meta Platforms", "Communication Services"),
    "TSLA": ("Tesla", "Consumer Discretionary"),
    "BRK-B": ("Berkshire Hathaway", "Financials"),
    "JPM": ("JPMorgan Chase", "Financials"),
    "V": ("Visa", "Financials"),
    "UNH": ("UnitedHealth", "Health Care"),
    "LLY": ("Eli Lilly", "Health Care"),
    "JNJ": ("Johnson & Johnson", "Health Care"),
    "WMT": ("Walmart", "Consumer Staples"),
    "COST": ("Costco", "Consumer Staples"),
    "KO": ("Coca-Cola", "Consumer Staples"),
    "XOM": ("Exxon Mobil", "Energy"),
    "CVX": ("Chevron", "Energy"),
    "AVGO": ("Broadcom", "Information Technology"),
    "AMD": ("AMD", "Information Technology"),
    "CRM": ("Salesforce", "Information Technology"),
    "ADBE": ("Adobe", "Information Technology"),
    "NOW": ("ServiceNow", "Information Technology"),
    "PLTR": ("Palantir", "Information Technology"),
}

# How many names to show on each side, and the move threshold (in %) above
# which we ask the brief to dig into the reason behind the move.
TOP_N = 5
BIG_MOVE_THRESHOLD = 4.0


def get_sp500_universe():
    """Return {yahoo_symbol: (company_name, sector)} for current S&P 500.

    Pulled from Wikipedia; falls back to a curated mega-cap list on failure.
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        import requests
        import certifi

        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            verify=certifi.where(),
            timeout=20,
        )
        resp.raise_for_status()
        df = pd.read_html(io.StringIO(resp.text))[0]

        universe = {}
        for _, row in df.iterrows():
            # Yahoo uses '-' where Wikipedia uses '.' (e.g. BRK.B -> BRK-B)
            symbol = str(row["Symbol"]).strip().replace(".", "-")
            name = str(row["Security"]).strip()
            sector = str(row["GICS Sector"]).strip()
            if symbol and symbol.lower() != "nan":
                universe[symbol] = (name, sector)

        if len(universe) >= 100:
            return universe
    except Exception as e:
        print(f"WARNING: could not fetch live S&P 500 list ({e}); using fallback")

    return dict(_FALLBACK_UNIVERSE)


def _pct_change_from_closes(closes):
    """Last close vs previous close, in percent. None if not computable."""
    closes = closes.dropna()
    if len(closes) < 2:
        return None, None
    latest = float(closes.iloc[-1])
    prev = float(closes.iloc[-2])
    if prev == 0:
        return None, None
    return latest, round((latest - prev) / prev * 100, 2)


def get_market_data():
    """Fetch index data + rotating S&P 500 gainers/losers (enriched)."""
    indices = {
        "S&P 500 (SPY)": "SPY",
        "Nasdaq 100 (QQQ)": "QQQ",
        "Dow Jones (DIA)": "DIA",
        "Russell 2000 (IWM)": "IWM",
    }

    all_data = {}

    # --- Indices (only 4, fetch individually) ---
    for name, symbol in indices.items():
        data = _fetch_ticker_data(name, symbol, is_index=True)
        if data:
            all_data[name] = data

    # --- Full S&P 500 universe, batched in one download ---
    universe = get_sp500_universe()
    symbols = list(universe.keys())

    stock_data = []
    try:
        batch = yf.download(
            symbols,
            period="5d",
            group_by="ticker",
            progress=False,
            threads=True,
        )
        for symbol in symbols:
            name, sector = universe[symbol]
            try:
                closes = batch[symbol]["Close"]
            except (KeyError, TypeError):
                continue
            latest, pct = _pct_change_from_closes(closes)
            if latest is None:
                continue
            stock_data.append({
                "name": name,
                "symbol": symbol,
                "latest_price": round(latest, 2),
                "change_percent": pct,
                "sector": sector,
                "is_index": False,
            })
    except Exception as e:
        print(f"WARNING: batch download failed ({e})")

    # Sort by the day's performance and slice the rotating ends
    stock_data.sort(key=lambda x: x["change_percent"], reverse=True)

    gainers = stock_data[:TOP_N]
    losers = list(reversed(stock_data[-TOP_N:])) if len(stock_data) >= TOP_N else []

    # Enrich only the names we will actually talk about (~10 tickers)
    for stock in gainers + losers:
        _enrich_mover(stock)

    all_data["_gainers"] = gainers
    all_data["_losers"] = losers
    all_data["_all_stocks"] = stock_data
    all_data["_universe_size"] = len(stock_data)

    return all_data


def _enrich_mover(stock):
    """Add a short business description + recent news to a single mover."""
    try:
        ticker = yf.Ticker(stock["symbol"])

        # Business description (trim to keep the prompt lean)
        try:
            summary = ticker.info.get("longBusinessSummary") or ""
            if summary:
                stock["business"] = summary[:320].rsplit(" ", 1)[0] + "..."
        except Exception:
            pass

        # Recent headlines specific to this ticker (the "why")
        headlines = []
        try:
            for item in (ticker.news or [])[:3]:
                content = item.get("content", item)
                title = content.get("title") or item.get("title")
                if title:
                    headlines.append(title.strip())
        except Exception:
            pass
        if headlines:
            stock["news"] = headlines
    except Exception:
        pass


def _fetch_ticker_data(name, symbol, is_index=False):
    """Fetch data for a single ticker (used for indices)."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")

        if len(hist) < 1:
            return None

        latest, change_pct = _pct_change_from_closes(hist["Close"])
        if latest is None:
            latest = float(hist["Close"].iloc[-1])
            change_pct = 0.0
        latest_date = hist.index[-1].strftime("%Y-%m-%d")

        return {
            "name": name,
            "symbol": symbol,
            "latest_price": round(latest, 2),
            "change": round(latest - (latest / (1 + change_pct / 100) if change_pct else latest), 2),
            "change_percent": change_pct,
            "latest_date": latest_date,
            "is_live": (datetime.now().date() == hist.index[-1].date()),
            "sector": None,
            "is_index": is_index,
        }
    except Exception:
        return None


def format_market_data(market_data):
    """Format market data with executive summary and stock prices."""
    from brief_generator import generate_executive_summary

    lines = ["📊 MARKET OVERVIEW", "=" * 70]

    if not market_data:
        lines.append("\nMarket data loading...")
        return "\n".join(lines)

    summary = generate_executive_summary(market_data)
    lines.append(summary)

    universe_size = market_data.get("_universe_size")
    if universe_size:
        lines.append(f"(Scanned {universe_size} S&P 500 names for today's movers)")

    # Indices
    lines.append("\n🏛️ MAJOR INDICES (vs previous close):")
    for name, data in market_data.items():
        if not name.startswith("_") and data.get("is_index"):
            change_symbol = "📈" if data["change_percent"] >= 0 else "📉"
            sign = "+" if data["change_percent"] >= 0 else ""
            lines.append(f"  {name}: ${data['latest_price']:.2f} ({sign}{data['change_percent']:.2f}%) {change_symbol} [{data.get('latest_date')}]")

    # Top gainers
    if market_data.get("_gainers"):
        lines.append("\n🚀 TOP GAINERS (S&P 500):")
        for data in market_data["_gainers"]:
            sector_info = f" | {data['sector']}" if data.get("sector") else ""
            lines.append(f"  {data['name']} ({data['symbol']}): ${data['latest_price']:.2f} (+{data['change_percent']:.2f}%){sector_info}")

    # Top losers
    if market_data.get("_losers"):
        lines.append("\n📉 TOP DECLINERS (S&P 500):")
        for data in market_data["_losers"]:
            sector_info = f" | {data['sector']}" if data.get("sector") else ""
            lines.append(f"  {data['name']} ({data['symbol']}): ${data['latest_price']:.2f} ({data['change_percent']:.2f}%){sector_info}")

    return "\n".join(lines)


def get_sector_summary(market_data):
    """Average performance per GICS sector across the scanned universe."""
    if "_all_stocks" not in market_data:
        return {}

    sector_performance = {}
    for stock in market_data["_all_stocks"]:
        sector = stock.get("sector")
        if sector and sector != "Unknown":
            sector_performance.setdefault(sector, []).append(stock["change_percent"])

    return {
        sector: round(sum(changes) / len(changes), 2)
        for sector, changes in sector_performance.items()
        if changes
    }


if __name__ == "__main__":
    data = get_market_data()
    print(format_market_data(data))
