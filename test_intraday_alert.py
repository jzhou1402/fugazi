# test_intraday_alert.py
import os
import yfinance as yf
import requests
import numpy as np
from datetime import datetime

# ─── Load Pushover Credentials ──────────────────────────────────────────
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER  = os.getenv("PUSHOVER_USER")
if not PUSHOVER_TOKEN or not PUSHOVER_USER:
    raise RuntimeError("Set PUSHOVER_TOKEN and PUSHOVER_USER in your environment.")

# ─── Alert Function ─────────────────────────────────────────────────────
def send_alert(ticker, pct_change, price):
    msg = f"{ticker} dropped {pct_change:.2f}% to ${price:.2f} in 30m (test alert)"
    payload = {
        "token":    PUSHOVER_TOKEN,
        "user":     PUSHOVER_USER,
        "title":    f"🚨 {ticker} Test Dip",
        "message":  msg,
        "priority": 1
    }
    r = requests.post("https://api.pushover.net/1/messages.json", data=payload)
    if r.status_code != 200:
        print(f"❌ Failed to send alert: {r.status_code} {r.text}")

# ─── Test Logic ─────────────────────────────────────────────────────────
def test_intraday_alert(ticker,
                        lookback_days=1,
                        interval="30m",
                        threshold_multiplier=2):
    """
    Runs one cycle of the intraday dip detector for a single ticker.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Testing {ticker}")
    data = yf.Ticker(ticker).history(period=f"{lookback_days}d", interval=interval)
    if len(data) < 2:
        print("  Not enough data.")
        return

    data["pct_change"] = data["Close"].pct_change() * 100
    changes = data["pct_change"].dropna()

    avg_move      = np.mean(np.abs(changes))
    latest_change = changes.iloc[-1]
    latest_price  = data["Close"].iloc[-1]

    print(f"  Avg 30m move : {avg_move:.2f}%")
    print(f"  Latest 30m Δ : {latest_change:.2f}%")

    if latest_change < 0 and abs(latest_change) > threshold_multiplier * avg_move:
        print("  → Triggering test alert via Pushover!")
        send_alert(ticker, latest_change, latest_price)
    else:
        print("  → No alert (within normal range).")

# ─── Main Entry ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Comma‑separated tickers, default to AAPL
    tickers = os.getenv("TEST_TICKERS", "AAPL").split(",")
    for t in tickers:
        test_intraday_alert(t.strip())