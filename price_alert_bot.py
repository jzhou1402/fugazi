import os
import yfinance as yf
import requests
import numpy as np
from portfolio_utils import load_portfolio

# === Load Pushover Credentials from Environment ===
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER  = os.getenv("PUSHOVER_USER")

if not PUSHOVER_TOKEN or not PUSHOVER_USER:
    raise RuntimeError("Missing Pushover credentials. "
                       "Please set PUSHOVER_TOKEN and PUSHOVER_USER environment variables.")

def send_alert(ticker, pct_change, price):
    message = f"{ticker} dropped {pct_change:.2f}% to ${price:.2f} in 30m (unusual dip)"
    payload = {
        "token":    PUSHOVER_TOKEN,
        "user":     PUSHOVER_USER,
        "title":    f"🚨 {ticker} Intraday Dip",
        "message":  message,
        "priority": 1
    }
    resp = requests.post("https://api.pushover.net/1/messages.json", data=payload)
    if resp.status_code != 200:
        print(f"⚠️ Alert failed for {ticker}: {resp.status_code} {resp.text}")

def analyze_dip_intraday(ticker, lookback_days=5, interval="30m", threshold_multiplier=2):
    """
    Fetches the last `lookback_days` of intraday data at `interval`,
    computes the avg absolute % move per interval, and if the most
    recent interval's drop exceeds threshold_multiplier×avg, fires alert.
    """
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period=f"{lookback_days}d", interval=interval)

        if len(hist) < 2:
            print(f"Not enough data for {ticker}.")
            return

        # compute % change per bar
        hist["pct_change"] = hist["Close"].pct_change() * 100
        changes = hist["pct_change"].dropna()

        avg_move     = np.mean(np.abs(changes))
        latest_change = changes.iloc[-1]
        latest_price  = hist["Close"].iloc[-1]

        print(f"{ticker} — Last 30m: {latest_change:.2f}%   |   Avg 30m move: {avg_move:.2f}%")

        if latest_change < 0 and abs(latest_change) > threshold_multiplier * avg_move:
            send_alert(ticker, latest_change, latest_price)

    except Exception as e:
        print(f"Error processing {ticker}: {e}")

if __name__ == "__main__":
    portfolio = load_portfolio()
    for sym in portfolio:
        analyze_dip_intraday(sym)