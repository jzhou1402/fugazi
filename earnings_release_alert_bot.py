import os
import yfinance as yf
import requests
from datetime import datetime, timedelta
import time
from portfolio_utils import load_portfolio
import pytz

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
        if earnings_dates is None or len(earnings_dates) == 0:
            return None
            
        # Get current time in UTC
        current_time = datetime.now(pytz.UTC)
        
        # Find the closest upcoming date
        closest_future_date = None
        min_days_until = float('inf')
        
        for date in earnings_dates.index:
            # Convert to timezone-aware datetime if needed
            if date.tzinfo is None:
                date = pytz.UTC.localize(date)
            
            # Only consider future dates
            if date > current_time:
                days_until = (date - current_time).days
                if days_until < min_days_until:
                    min_days_until = days_until
                    closest_future_date = date
                
        return closest_future_date
        
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
            
        # Get current time in UTC
        current_time = datetime.now(pytz.UTC)
        
        # Calculate days until earnings
        days_until = (earnings_date - current_time).days
        
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