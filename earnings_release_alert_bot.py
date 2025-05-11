import os
import yfinance as yf
import requests
from datetime import datetime, timedelta
import time
from portfolio_utils import load_portfolio

# === Load Pushover Credentials from Environment ===
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER  = os.getenv("PUSHOVER_USER")

def get_earnings_date(ticker):
    """
    Get the next earnings date for a ticker using yfinance.
    Includes rate limiting and error handling.
    """
    try:
        # Add a small delay to avoid rate limits
        time.sleep(0.5)
        
        stock = yf.Ticker(ticker)
        # Get earnings dates
        earnings_dates = stock.earnings_dates
        
        if earnings_dates is None:
            return None
            
        # Get the next earnings date (first row)
        next_earnings = earnings_dates.index[0]
        return next_earnings
        
    except Exception as e:
        print(f"Error fetching earnings date for {ticker}: {e}")
        return None

def check_upcoming_earnings(ticker):
    """
    Checks if the ticker has earnings coming up in the next 2 days
    and sends an alert if found.
    """
    try:
        earnings_date = get_earnings_date(ticker)
        
        if earnings_date is None:
            return
            
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