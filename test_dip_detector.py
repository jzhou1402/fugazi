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
        f"🚨 TEST ALERT: {ticker} dropped {data['max_drop']:.1f}% from peak\n"
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
    Checks for the maximum drop between any two points in the day.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Testing {ticker}")
    
    try:
        tk = yf.Ticker(ticker)
        
        # Get yesterday's close
        prev_day = tk.history(period="2d", interval="1d")
        if len(prev_day) < 2:
            print("  Not enough data for previous day.")
            return
        prev_close = prev_day['Close'].iloc[0]
        
        # Get today's intraday data
        today = tk.history(period="1d", interval="5m")
        if len(today) < 2:
            print("  Not enough data for today.")
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
        
        print(f"  Yesterday's Close: ${prev_close:.2f}")
        print(f"  Peak Price: ${peak_price:.2f} at {drop_start_time}")
        print(f"  Current: ${current_price:.2f}")
        print(f"  Maximum Drop: {abs(max_drop):.1f}%")
        print(f"  Change from prev close: {change_from_prev:+.1f}%")
        print(f"  Volume: {current_volume:,} (Avg: {avg_volume:,})")

        if max_drop < -threshold:
            print("  → Triggering alert!")
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