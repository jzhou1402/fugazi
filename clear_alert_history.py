#!/usr/bin/env python3
import os
import json
from datetime import datetime

def clear_alert_history():
    """Clear the alert history file"""
    alert_file = "alert_history.json"
    try:
        if os.path.exists(alert_file):
            os.remove(alert_file)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Alert history cleared.")
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] No alert history file found.")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Error clearing alert history: {e}")

if __name__ == "__main__":
    clear_alert_history() 