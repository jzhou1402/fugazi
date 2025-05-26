# test_dip_detector.py
import os
import yfinance as yf
import requests
import numpy as np
import pandas as pd
from datetime import datetime

# ─── Load Pushover Credentials ──────────────────────────────────────────
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER  = os.getenv("PUSHOVER_USER")
if not PUSHOVER_TOKEN or not PUSHOVER_USER:
    raise RuntimeError("Set PUSHOVER_TOKEN and PUSHOVER_USER in your environment.")

# ─── Alert Function ─────────────────────────────────────────────────────
def send_test_alert(ticker, data):
    """Send test alert with detailed drop information"""
    message = (
        f"🚨 TEST ALERT: {ticker} dropped {data['pct_change']:.1f}% from day's high\n"
        f"Current: ${data['current_price']:.2f}\n"
        f"Day's High: ${data['day_high']:.2f}\n"
        f"Yesterday's Close: ${data['prev_close']:.2f} ({data['prev_close_pct']:+.1f}% from prev close)\n"
        f"Volume: {data['volume']:,} (Avg: {data['avg_volume']:,})\n"
        f"Sector: {data['sector']}\n"
        f"Chart: https://finance.yahoo.com/quote/{ticker}"
    )
    
    payload = {
        "token":    PUSHOVER_TOKEN,
        "user":     PUSHOVER_USER,
        "title":    f"🧪 {ticker} Test Drop",
        "message":  message,
        "priority": 1
    }
    resp = requests.post("https://api.pushover.net/1/messages.json", data=payload)
    if resp.status_code != 200:
        print(f"❌ Failed to send alert: {resp.status_code} {resp.text}")

# ─── Test Logic ─────────────────────────────────────────────────────────
def test_dip_detector(ticker, threshold=5.0):
    """
    Tests the dip detector for a single ticker.
    Checks if the stock has dropped significantly from its day's high.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Testing {ticker}")
    
    try:
        tk = yf.Ticker(ticker)
        
        # Get intraday data for current day and previous day's close
        hist = tk.history(period="2d", interval="5m")
        if len(hist) < 2:
            print("  Not enough data.")
            return

        # Get stock info for sector and volume data
        info = tk.info
        
        # Calculate drops
        day_high = hist['High'].max()
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[0]  # First close of the 2-day period
        
        # Calculate percentage changes
        drop_from_high = ((current_price - day_high) / day_high) * 100
        change_from_prev = ((current_price - prev_close) / prev_close) * 100
        
        # Get volume data
        current_volume = hist['Volume'].sum()
        avg_volume = info.get('averageVolume', 0)
        
        print(f"  Day's High: ${day_high:.2f}")
        print(f"  Current: ${current_price:.2f}")
        print(f"  Yesterday's Close: ${prev_close:.2f}")
        print(f"  Drop from high: {abs(drop_from_high):.1f}%")
        print(f"  Change from prev close: {change_from_prev:+.1f}%")
        print(f"  Volume: {current_volume:,} (Avg: {avg_volume:,})")

        if drop_from_high < -threshold:
            print("  → Triggering test alert via Pushover!")
            data = {
                'pct_change': abs(drop_from_high),
                'current_price': current_price,
                'day_high': day_high,
                'prev_close': prev_close,
                'prev_close_pct': change_from_prev,
                'volume': current_volume,
                'avg_volume': avg_volume,
                'sector': info.get('sector', 'Unknown')
            }
            send_test_alert(ticker, data)
        else:
            print("  → No alert (drop below threshold).")

    except Exception as e:
        print(f"  ❌ Error: {e}")

# ─── Main Entry ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Comma‑separated tickers, default to AAPL
    tickers = os.getenv("TEST_TICKERS", "AAPL").split(",")
    for t in tickers:
        test_dip_detector(t.strip()) 