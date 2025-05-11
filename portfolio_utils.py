import json

def load_portfolio(path="portfolio.json"):
    with open(path) as f:
        data = json.load(f)
    # allow either list of strings or list of dicts with "ticker"
    return [s if isinstance(s, str) else s["ticker"] for s in data]