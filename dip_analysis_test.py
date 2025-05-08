import yfinance as yf
import numpy as np

def simulate_analyze_dip(ticker, fake_today_index=-1):
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="60d")

        if len(hist) < abs(fake_today_index):
            print(f"Not enough data for {ticker}")
            return

        # Calculate daily percent changes
        hist["pct_change"] = hist["Close"].pct_change() * 100
        pct_changes = hist["pct_change"].dropna()

        avg_daily_move = pct_changes.abs().mean()

        # Use a historical date as "today"
        current_price = hist["Close"].iloc[fake_today_index]
        prev_close = hist["Close"].iloc[fake_today_index - 1]
        today_change = ((current_price - prev_close) / prev_close) * 100

        today_date = hist.index[fake_today_index].strftime('%Y-%m-%d')
        print(f"\nSimulating {ticker} on {today_date}")
        print(f"→ Today Change: {today_change:.2f}%")
        print(f"→ Avg Daily Move: {avg_daily_move:.2f}%")

        if today_change < 0 and abs(today_change) > 2 * avg_daily_move:
            print(f"🚨 ALERT: Unusual dip detected for {ticker}!")
        else:
            print(f"✅ No alert: move within expected range.")

    except Exception as e:
        print(f"Error simulating {ticker}: {e}")


simulate_analyze_dip("PDD", fake_today_index=-10)  # Use 10th day from the end as “today”