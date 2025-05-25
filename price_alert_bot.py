import os
import yfinance as yf
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from portfolio_utils import load_portfolio

# === Load Pushover Credentials from Environment ===
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER  = os.getenv("PUSHOVER_USER")

if not PUSHOVER_TOKEN or not PUSHOVER_USER:
    raise RuntimeError("Missing Pushover credentials. "
                       "Please set PUSHOVER_TOKEN and PUSHOVER_USER environment variables.")

def get_sp500_symbols():
    """Get list of S&P 500 symbols"""
    # Using Wikipedia's S&P 500 list
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0]
    return df['Symbol'].tolist()

def send_alert(ticker, data):
    """Send alert with detailed drop information"""
    message = (
        f"🚨 {ticker} dropped {data['pct_change']:.1f}% from day's high\n"
        f"Current: ${data['current_price']:.2f}\n"
        f"Day's High: ${data['day_high']:.2f}\n"
        f"Volume: {data['volume']:,} (Avg: {data['avg_volume']:,})\n"
        f"Sector: {data['sector']}\n"
        f"Chart: https://finance.yahoo.com/quote/{ticker}"
    )
    
    payload = {
        "token":    PUSHOVER_TOKEN,
        "user":     PUSHOVER_USER,
        "title":    f"📉 {ticker} Significant Drop",
        "message":  message,
        "priority": 1
    }
    resp = requests.post("https://api.pushover.net/1/messages.json", data=payload)
    if resp.status_code != 200:
        print(f"⚠️ Alert failed for {ticker}: {resp.status_code} {resp.text}")

def analyze_stock_drop(ticker, threshold=10.0):
    """
    Analyze if a stock has dropped significantly from its day's high
    threshold: minimum percentage drop to trigger alert
    """
    try:
        tk = yf.Ticker(ticker)
        
        # Get intraday data for current day
        hist = tk.history(period="1d", interval="5m")
        if len(hist) < 2:
            print(f"Not enough data for {ticker}")
            return

        # Get stock info for sector and volume data
        info = tk.info
        
        # Calculate drop from day's high
        day_high = hist['High'].max()
        current_price = hist['Close'].iloc[-1]
        pct_change = ((current_price - day_high) / day_high) * 100
        
        # Get volume data
        current_volume = hist['Volume'].sum()  # Total volume for the day
        avg_volume = info.get('averageVolume', 0)
        
        print(f"{ticker} — Drop from high: {abs(pct_change):.1f}% | Current: ${current_price:.2f}")

        if pct_change < -threshold:
            data = {
                'pct_change': abs(pct_change),
                'current_price': current_price,
                'day_high': day_high,
                'volume': current_volume,
                'avg_volume': avg_volume,
                'sector': info.get('sector', 'Unknown')
            }
            send_alert(ticker, data)

    except Exception as e:
        print(f"Error processing {ticker}: {e}")

if __name__ == "__main__":
    # Get S&P 500 symbols
    sp500_symbols = get_sp500_symbols()
    
    # Get portfolio symbols
    portfolio_symbols = load_portfolio()
    
    # Combine both sets of symbols, removing duplicates
    all_symbols = set(sp500_symbols) | set(portfolio_symbols)
    
    print(f"Monitoring {len(all_symbols)} stocks ({len(sp500_symbols)} S&P 500 + {len(portfolio_symbols)} portfolio)")
    
    # Analyze each stock
    for symbol in all_symbols:
        analyze_stock_drop(symbol)