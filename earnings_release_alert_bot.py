import os
import yfinance as yf
import requests
from datetime import datetime
from portfolio_utils import load_portfolio

# === Load Pushover Credentials from Environment ===
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER  = os.getenv("PUSHOVER_USER")


def check_upcoming_earnings(ticker):
    """
    Checks if the ticker has earnings coming up in the next 2 days
    and sends an alert if found.
    """
    try:
        tk = yf.Ticker(ticker)
        calendar = tk.calendar
        
        if calendar is None or calendar.empty:
            return
            
        # Get the next earnings date
        next_earnings = calendar.iloc[0]
        earnings_date = next_earnings.name  # This is the date
        
        # Calculate days until earnings
        days_until = (earnings_date - datetime.now()).days
        
        if days_until == 2:
            message = f"{ticker} earnings coming up in 2 days on {earnings_date.strftime('%Y-%m-%d')}"
            payload = {
                "token":    PUSHOVER_TOKEN,
                "user":     PUSHOVER_USER,
                "title":    f"📅 {ticker} Earnings Alert",
                "message":  message,
                "priority": 0  # Normal priority
            }
            resp = requests.post("https://api.pushover.net/1/messages.json", data=payload)
            if resp.status_code != 200:
                print(f"⚠️ Earnings alert failed for {ticker}: {resp.status_code} {resp.text}")
                
    except Exception as e:
        print(f"Error checking earnings for {ticker}: {e}")


if __name__ == "__main__":
    portfolio = load_portfolio()
    for sym in portfolio:
        check_upcoming_earnings(sym)