from utils.api_clients import fetch_fmp_events
from datetime import datetime

def get_today_events():
    all_events = fetch_fmp_events()
    today = datetime.utcnow().date()

    today_events = []
    for event in all_events:
        try:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
            if event_date == today:
                today_events.append({
                    "title": event.get("event", "Unnamed"),
                    "datetime": event.get("date", "Unknown"),
                    "impact": event.get("impact", "N/A")
                })
        except Exception as e:
            print(f"[Parse Error] {e}")

    return today_events
