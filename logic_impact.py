import requests
from datetime import datetime, timedelta, timezone

CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

def get_forex_news_today(for_week=False):
    try:
        response = requests.get(CALENDAR_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        tz = timezone(timedelta(hours=1))  # Europe/Rome
        today = datetime.now(tz).date()

        news_list = []

        for event in data:
            event_time = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
            event_time = event_time.astimezone(tz)

            if not for_week:
                if event_time.date() != today:
                    continue

            news_list.append({
                "prefixedName": event.get("title", "N/A"),
                "timeLabel": event_time.strftime("%H:%M"),
                "forecast": event.get("forecast", ""),
                "actual": event.get("actual", ""),
                "url": "https://www.forexfactory.com/calendar"
            })

        if not news_list:
            return ["Nessun evento trovato."]

        return news_list

    except Exception as e:
        return [f"Errore nello scraping: {e}"]
