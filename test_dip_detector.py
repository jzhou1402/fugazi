# test_dip_detector.py
import os
import yfinance as yf
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from price_alert_bot import analyze_stock_drop, send_alert

# ─── Load Pushover Credentials ──────────────────────────────────────────
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER  = os.getenv("PUSHOVER_USER")
if not PUSHOVER_TOKEN or not PUSHOVER_USER:
    raise RuntimeError("Set PUSHOVER_TOKEN and PUSHOVER_USER in your environment.")

# ─── Test Alert Function ────────────────────────────────────────────────
def send_test_alert(ticker, data):
    """Override the alert function to mark it as a test"""
    message = (
        f"🧪 TEST ALERT: {ticker} dropped {data['max_drop']:.1f}% from peak\n"
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
    Tests the dip detector for a single ticker using the actual analyze_stock_drop function.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Testing {ticker}")
    
    try:
        # Temporarily replace the alert function with our test version
        original_send_alert = send_alert
        send_alert = send_test_alert
        
        # Run the actual analysis function
        analyze_stock_drop(ticker, threshold)
        
        # Restore the original alert function
        send_alert = original_send_alert
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        # Make sure to restore the original alert function even if there's an error
        send_alert = original_send_alert

# ─── Main Entry ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Comma‑separated tickers, default to AAPL
    tickers = os.getenv("TEST_TICKERS", "AAPL").split(",")
    for t in tickers:
        test_dip_detector(t.strip()) 