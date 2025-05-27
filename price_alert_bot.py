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
        f"🚨 {ticker} dropped {data['max_drop']:.1f}% from peak\n"
        f"Current: ${data['current_price']:.2f}\n"
        f"Peak Price: ${data['peak_price']:.2f}\n"
        f"Drop Start: {data['drop_start_time']}\n"
        f"Yesterday's Close: ${data['prev_close']:.2f} ({data['prev_close_pct']:+.1f}% from prev close)\n"
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

def analyze_stock_drop(ticker, threshold=5.0):
    """
    Analyze if a stock has dropped significantly from its peak
    threshold: minimum percentage drop to trigger alert
    """
    try:
        tk = yf.Ticker(ticker)
        
        # Get yesterday's close
        prev_day = tk.history(period="2d", interval="1d")
        if len(prev_day) < 2:
            print(f"Not enough data for previous day for {ticker}")
            return
        prev_close = prev_day['Close'].iloc[0]
        
        # Get today's intraday data
        today = tk.history(period="1d", interval="5m")
        if len(today) < 2:
            print(f"Not enough data for today for {ticker}")
            return

        # Get stock info for sector and volume data
        info = tk.info
        
        # Calculate maximum drop
        current_price = today['Close'].iloc[-1]
        
        # Include yesterday's close in the analysis
        all_prices = pd.concat([
            pd.Series([prev_close], index=[today.index[0] - pd.Timedelta(minutes=5)]),
            today['High'],
            today['Low']
        ]).sort_index()
        
        # Calculate rolling maximum and drops
        rolling_max = all_prices.expanding().max()
        drops = ((all_prices - rolling_max) / rolling_max) * 100
        
        # Find the maximum drop
        max_drop_idx = drops.idxmin()
        max_drop = drops.min()
        peak_price = rolling_max[max_drop_idx]
        
        # Find when the peak occurred
        peak_idx = all_prices[all_prices == peak_price].index[0]
        drop_start_time = peak_idx.strftime('%H:%M')
        
        # Calculate change from previous close
        change_from_prev = ((current_price - prev_close) / prev_close) * 100
        
        # Get volume data
        current_volume = today['Volume'].sum()
        avg_volume = info.get('averageVolume', 0)
        
        print(f"{ticker} — Max Drop: {abs(max_drop):.1f}% | Current: ${current_price:.2f}")

        if max_drop < -threshold:
            data = {
                'max_drop': abs(max_drop),
                'current_price': current_price,
                'peak_price': peak_price,
                'drop_start_time': drop_start_time,
                'prev_close': prev_close,
                'prev_close_pct': change_from_prev,
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