# market_data.py
"""Fetch comprehensive market data - clean execution."""

import yfinance as yf
from datetime import datetime


TOP_STOCKS = {
    # Mega Cap Tech
    "Apple": "AAPL", "Microsoft": "MSFT", "Nvidia": "NVDA",
    "Amazon": "AMZN", "Alphabet": "GOOGL", "Meta": "META", "Tesla": "TSLA",
    
    # Finance
    "Berkshire": "BRK-B", "JPMorgan": "JPM", "Visa": "V",
    
    # Healthcare  
    "UnitedHealth": "UNH", "Eli Lilly": "LLY", "J&J": "JNJ",
    
    # Consumer
    "Walmart": "WMT", "Costco": "COST", "Coca-Cola": "KO",
    
    # Energy
    "Exxon": "XOM", "Chevron": "CVX",
    
    # Semiconductors
    "TSMC": "TSM", "Broadcom": "AVGO", "AMD": "AMD",
    
    # Cloud/Software
    "Salesforce": "CRM", "Adobe": "ADBE", "ServiceNow": "NOW",
    
    # AI/Emerging
    "Palantir": "PLTR", "Snowflake": "SNOW",
}


def get_market_data():
    """Fetch market data - clean, minimal output."""
    indices = {
        "S&P 500 (SPY)": "SPY",
        "Nasdaq 100 (QQQ)": "QQQ",
        "Dow Jones (DIA)": "DIA",
        "Russell 2000 (IWM)": "IWM",
    }
    
    all_data = {}
    
    # Get index data (silent)
    for name, symbol in indices.items():
        data = _fetch_ticker_data(name, symbol, is_index=True)
        if data:
            all_data[name] = data
    
    # Get stock data (silent)
    stock_data = []
    for name, symbol in TOP_STOCKS.items():
        data = _fetch_ticker_data(name, symbol, is_index=False)
        if data:
            stock_data.append(data)
    
    # Sort and categorize
    stock_data.sort(key=lambda x: x.get('change_percent', 0), reverse=True)
    
    all_data['_gainers'] = stock_data[:5]
    all_data['_losers'] = stock_data[-5:]
    all_data['_all_stocks'] = stock_data
    
    return all_data


def _fetch_ticker_data(name, symbol, is_index=False):
    """Fetch data for single ticker - no output."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")
        
        if len(hist) < 1:
            return None
        
        latest_close = hist['Close'].iloc[-1]
        latest_date = hist.index[-1].strftime('%Y-%m-%d')
        
        prev_close = hist['Close'].iloc[-2] if len(hist) >= 2 else latest_close
        change = latest_close - prev_close
        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
        
        sector = None
        if not is_index:
            try:
                sector = ticker.info.get('sector', 'Unknown')
            except:
                pass
        
        return {
            "name": name,
            "symbol": symbol,
            "latest_price": round(latest_close, 2),
            "change": round(change, 2),
            "change_percent": round(change_pct, 2),
            "latest_date": latest_date,
            "is_live": (datetime.now().date() == hist.index[-1].date()),
            "sector": sector,
            "is_index": is_index
        }
    except:
        return None


def format_market_data(market_data):
    """Format market data - clean professional output."""
    lines = ["📊 MARKET OVERVIEW", "=" * 70]
    
    if not market_data:
        lines.append("\nMarket data loading...")
        return "\n".join(lines)
    
    # Indices
    lines.append("\n🏛️ MAJOR INDICES:")
    for name, data in market_data.items():
        if not name.startswith('_') and data.get('is_index'):
            change_symbol = "📈" if data['change_percent'] >= 0 else "📉"
            sign = "+" if data['change_percent'] >= 0 else ""
            status = f"[{data.get('latest_date')}]"
            lines.append(f"  {name}: ${data['latest_price']:.2f} ({sign}{data['change_percent']:.2f}%) {change_symbol} {status}")
    
    # Top gainers
    if '_gainers' in market_data and market_data['_gainers']:
        lines.append("\n🚀 TOP GAINERS:")
        for data in market_data['_gainers']:
            sector_info = f" | {data['sector']}" if data.get('sector') else ""
            lines.append(f"  {data['name']} ({data['symbol']}): +{data['change_percent']:.2f}%{sector_info}")
    
    # Top losers
    if '_losers' in market_data and market_data['_losers']:
        lines.append("\n📉 TOP DECLINERS:")
        for data in market_data['_losers']:
            sector_info = f" | {data['sector']}" if data.get('sector') else ""
            lines.append(f"  {data['name']} ({data['symbol']}): {data['change_percent']:.2f}%{sector_info}")
    
    return "\n".join(lines)


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


if __name__ == "__main__":
    data = get_market_data()
    print(format_market_data(data))
