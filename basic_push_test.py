import requests

# Replace these with your real credentials from https://pushover.net
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER  = os.getenv("PUSHOVER_USER")

def send_test_notification():
    payload = {
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER,
        "title": "🔔 Test Notification",
        "message": "This is a test alert from your AI portfolio manager!",
        "priority": 1
    }
    
    response = requests.post("https://api.pushover.net/1/messages.json", data=payload)
    
    if response.status_code == 200:
        print("✅ Notification sent successfully!")
    else:
        print("❌ Failed to send notification:", response.text)

if __name__ == "__main__":
    send_test_notification()