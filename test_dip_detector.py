# test_dip_detector.py
import os
import yfinance as yf
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from price_alert_bot import analyze_stock_data

# ─── Load Environment Variables ──────────────────────────────────────────
load_dotenv()  # Load environment variables from .env file

# ─── Test Logic ─────────────────────────────────────────────────────────
def test_dip_detector(ticker, threshold=5.0):
    """
    Tests the dip detector for a single ticker using the actual analyze_stock_data function.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Testing {ticker}")
    
    try:
        # Run the actual analysis function
        drop_data = analyze_stock_data(ticker, threshold)
        
        if drop_data:
            # Print the drop metrics
            from_time = "Previous Close" if drop_data['is_from_prev_close'] else drop_data['drop_from_time']
            print(f"\nDrop Analysis:")
            print(f"Maximum Drop: {drop_data['max_drop_pct']:.1f}%")
            print(f"Drop: ${drop_data['drop_from_price']:.2f} ({from_time}) → ${drop_data['drop_to_price']:.2f} ({drop_data['drop_to_time']})")
            print(f"Current Price: ${drop_data['current_price']:.2f}")
            
            if drop_data['max_drop_pct'] > threshold:
                print("\nWould send alert:")
                print(f"📉 {ticker} dropped {drop_data['max_drop_pct']:.1f}% from peak")
                print(f"Current: ${drop_data['current_price']:.2f}")
                print(f"Drop: ${drop_data['drop_from_price']:.2f} ({from_time}) → ${drop_data['drop_to_price']:.2f} ({drop_data['drop_to_time']})")
                print(f"Chart: https://finance.yahoo.com/quote/{ticker}")
        else:
            print("  → No data available for analysis.")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

# ─── Main Entry ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Comma‑separated tickers, default to AAPL
    tickers = os.getenv("TEST_TICKERS", "AAPL").split(",")
    for t in tickers:
        test_dip_detector(t.strip()) 