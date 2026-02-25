# chart_generator.py
"""Generate market charts for email."""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta
import io
import base64


def create_index_chart():
    """Create 30-day chart for major indices."""
    try:
        # Get 30 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        indices = {
            'S&P 500': 'SPY',
            'Nasdaq': 'QQQ',
            'Dow Jones': 'DIA',
        }
        
        plt.figure(figsize=(12, 6))
        try:
            plt.style.use('seaborn-v0_8-darkgrid')
        except OSError:
            plt.style.use('seaborn-darkgrid')
        except OSError:
            pass  # Use default style
        
        for name, symbol in indices.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if len(hist) > 0:
                # Normalize to 100 for comparison
                normalized = (hist['Close'] / hist['Close'].iloc[0]) * 100
                plt.plot(hist.index, normalized, label=name, linewidth=2)
        
        plt.title('Major Indices - Last 30 Days (Normalized)', fontsize=14, fontweight='bold')
        plt.xlabel('Date', fontsize=11)
        plt.ylabel('Normalized Price (Start = 100)', fontsize=11)
        plt.legend(loc='best', fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return f'<img src="data:image/png;base64,{image_base64}" style="max-width: 100%; height: auto;">'
        
    except Exception as e:
        print(f"Error creating chart: {e}")
        return ""


def create_sector_performance_chart(market_data):
    """Create bar chart of sector performance."""
    try:
        from brief_generator import get_sector_summary
        
        sector_summary = get_sector_summary(market_data)
        
        if not sector_summary:
            return ""
        
        # Sort sectors by performance
        sectors = sorted(sector_summary.items(), key=lambda x: x[1], reverse=True)
        names = [s[0] for s in sectors]
        values = [s[1] for s in sectors]
        
        # Create colors (green for positive, red for negative)
        colors = ['#34a853' if v >= 0 else '#ea4335' for v in values]
        
        plt.figure(figsize=(10, 6))
        plt.barh(names, values, color=colors)
        plt.xlabel('Performance (%)', fontsize=11)
        plt.title('Sector Performance Today', fontsize=14, fontweight='bold')
        plt.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
        plt.grid(True, axis='x', alpha=0.3)
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return f'<img src="data:image/png;base64,{image_base64}" style="max-width: 100%; height: auto;">'
        
    except Exception as e:
        print(f"Error creating sector chart: {e}")
        return ""


if __name__ == "__main__":
    print("Testing chart generation...")
    chart = create_index_chart()
    print("Chart generated!" if chart else "Chart failed")
