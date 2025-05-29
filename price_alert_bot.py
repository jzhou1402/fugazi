import os
import yfinance as yf
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from portfolio_utils import load_portfolio
import json

# ─── Load Environment Variables ──────────────────────────────────────────
load_dotenv()  # Load environment variables from .env file

# === Load Pushover Credentials from Environment ===
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER  = os.getenv("PUSHOVER_USER")

if not PUSHOVER_TOKEN or not PUSHOVER_USER:
    raise RuntimeError("Missing Pushover credentials. "
                       "Please set PUSHOVER_TOKEN and PUSHOVER_USER in your environment or .env file.")

def get_sp500_symbols():
    """Get list of S&P 500 symbols"""
    # Using Wikipedia's S&P 500 list
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0]
    return df['Symbol'].tolist()

# ─── Analysis Functions ─────────────────────────────────────────────────
def analyze_stock_data(ticker, threshold=5.0):
    """
    Analyzes stock data to detect significant drops.
    Returns a dict with drop metrics:
    - max_drop_pct: Maximum percentage drop
    - drop_from_price: Starting price of the maximum drop
    - drop_to_price: Ending price of the maximum drop
    - drop_from_time: Starting time of the maximum drop
    - drop_to_time: Ending time of the maximum drop
    - current_price: Current price of the stock
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Analyzing {ticker}")
    
    # Get the data
    tk = yf.Ticker(ticker)
    
    # Get yesterday's close
    prev_day = tk.history(period="2d", interval="1d")
    if len(prev_day) < 2:
        print(f"  ❌ {ticker}: Not enough data for previous day.")
        return None
    prev_close = prev_day['Close'].iloc[0]
    
    # Get today's intraday data
    today = tk.history(period="1d", interval="5m")
    if len(today) < 2:
        print(f"  ❌ {ticker}: Not enough data for today.")
        return None

    # Calculate maximum drop
    current_price = today['Close'].iloc[-1]
    
    # Create a list of all price points we want to analyze
    price_points = []
    
    # Add yesterday's close
    price_points.append({
        'timestamp': today.index[0] - pd.Timedelta(minutes=5),
        'price': prev_close,
        'is_prev_close': True
    })
    
    # Add today's high and low prices
    for idx, row in today.iterrows():
        price_points.append({
            'timestamp': idx,
            'price': row['High'],
            'is_prev_close': False
        })
        price_points.append({
            'timestamp': idx,
            'price': row['Low'],
            'is_prev_close': False
        })
    
    # Convert to DataFrame and sort by timestamp
    price_df = pd.DataFrame(price_points)
    price_df = price_df.sort_values('timestamp')
    
    # Calculate rolling maximum
    price_df['rolling_max'] = price_df['price'].expanding().max()
    
    # Calculate percentage drops
    price_df['drop_pct'] = ((price_df['price'] - price_df['rolling_max']) / price_df['rolling_max']) * 100
    
    # Find the maximum drop
    max_drop_idx = price_df['drop_pct'].idxmin()
    max_drop = price_df.loc[max_drop_idx, 'drop_pct']
    
    # Get the peak price and time
    peak_price = price_df.loc[max_drop_idx, 'rolling_max']
    peak_row = price_df[price_df['price'] == peak_price].iloc[0]
    
    # Get the drop end price and time
    drop_end_row = price_df.loc[max_drop_idx]
    
    return {
        'max_drop_pct': abs(max_drop),
        'drop_from_price': peak_price,
        'drop_to_price': drop_end_row['price'],
        'drop_from_time': peak_row['timestamp'].strftime('%H:%M'),
        'drop_to_time': drop_end_row['timestamp'].strftime('%H:%M'),
        'is_from_prev_close': peak_row['is_prev_close'],
        'current_price': current_price
    }

# ─── Alert Tracking ───────────────────────────────────────────────────
class AlertTracker:
    def __init__(self):
        self.alert_file = "alert_history.json"
        self.alerts = self._load_alerts()
    
    def _load_alerts(self):
        """Load alert history from JSON file"""
        try:
            if os.path.exists(self.alert_file):
                with open(self.alert_file, 'r') as f:
                    data = json.load(f)
                    # Convert string dates back to datetime objects
                    return {ticker: (datetime.fromisoformat(time), price) 
                           for ticker, (time, price) in data.items()}
            return {}
        except Exception as e:
            print(f"❌ Error loading alert history: {e}")
            return {}
    
    def _save_alerts(self):
        """Save alert history to JSON file"""
        try:
            # Convert datetime objects to ISO format strings for JSON serialization
            data = {ticker: (time.isoformat(), price) 
                   for ticker, (time, price) in self.alerts.items()}
            with open(self.alert_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"❌ Error saving alert history: {e}")
    
    def should_alert(self, ticker, current_price, threshold):
        """Check if we should send an alert for this ticker"""
        if ticker not in self.alerts:
            print(f"  ✓ {ticker}: No previous alerts, will send if threshold met")
            return True
        
        last_time, last_price = self.alerts[ticker]
        # If it's a new day, reset the tracking
        if last_time.date() != datetime.now().date():
            print(f"  ✓ {ticker}: New day, will send if threshold met")
            return True
        
        # Calculate new drop from last alert price
        new_drop = ((last_price - current_price) / last_price) * 100
        should_alert = new_drop >= threshold
        if should_alert:
            print(f"  ✓ {ticker}: New drop of {new_drop:.1f}% from last alert price ${last_price:.2f}")
        else:
            print(f"  ⚠️ {ticker}: Drop of {new_drop:.1f}% from last alert price ${last_price:.2f} below threshold")
        return should_alert
    
    def record_alert(self, ticker, current_price):
        """Record that we sent an alert for this ticker"""
        self.alerts[ticker] = (datetime.now(), current_price)
        self._save_alerts()  # Save after each new alert
        print(f"  ✓ {ticker}: Alert recorded at ${current_price:.2f}")

# Create a global alert tracker
alert_tracker = AlertTracker()

def analyze_stock_drop(ticker, threshold=10.0):
    """
    Analyzes stock data and sends an alert if a significant drop is detected.
    Only sends a new alert if the price has dropped by the threshold amount again.
    """
    try:
        # Analyze the stock data
        drop_data = analyze_stock_data(ticker, threshold)
        
        # If a significant drop was detected, check if we should alert
        if drop_data and drop_data['max_drop_pct'] > threshold:
            print(f"  📊 {ticker}: Detected drop of {drop_data['max_drop_pct']:.1f}%")
            if alert_tracker.should_alert(ticker, drop_data['current_price'], threshold):
                send_alert(ticker, drop_data)
                alert_tracker.record_alert(ticker, drop_data['current_price'])
            else:
                print(f"  ⚠️ {ticker}: Drop detected but no alert sent (already alerted)")
        elif drop_data:
            print(f"  ℹ️ {ticker}: Maximum drop of {drop_data['max_drop_pct']:.1f}% below threshold")
        else:
            print(f"  ℹ️ {ticker}: No valid data for analysis")
            
    except Exception as e:
        print(f"  ❌ {ticker}: Error during analysis: {e}")

# ─── Alert Functions ───────────────────────────────────────────────────
def send_alert(ticker, data):
    """Send alert with detailed drop information"""
    from_time = "Previous Close" if data['is_from_prev_close'] else data['drop_from_time']
    
    message = (
        f"📉 {ticker} dropped {data['max_drop_pct']:.1f}% from peak\n"
        f"Current: ${data['current_price']:.2f}\n"
        f"Drop: ${data['drop_from_price']:.2f} ({from_time}) → ${data['drop_to_price']:.2f} ({data['drop_to_time']})\n"
        f"Chart: https://finance.yahoo.com/quote/{ticker}"
    )
    
    payload = {
        "token":    PUSHOVER_TOKEN,
        "user":     PUSHOVER_USER,
        "title":    f"{ticker} Drop Alert",
        "message":  message,
        "priority": 1
    }
    resp = requests.post("https://api.pushover.net/1/messages.json", data=payload)
    if resp.status_code != 200:
        print(f"  ❌ {ticker}: Failed to send alert: {resp.status_code} {resp.text}")
    else:
        print(f"  ✓ {ticker}: Alert sent successfully")

# ─── Main Entry ─────────────────────────────────────────────────────────
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