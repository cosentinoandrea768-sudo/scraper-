import requests
import re
import json
from datetime import datetime, timezone, timedelta

FOREX_URL = "https://www.forexfactory.com/calendar.php"

def get_forex_news_today():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
        }
        r = requests.get(FOREX_URL, headers=headers, timeout=10)
        r.raise_for_status()
        html = r.text

        # Cerca window.calendarComponentStates
        match = re.search(r"window\.calendarComponentStates\s*=\s*({.*?});", html, re.DOTALL)
        if not match:
            return ["❌ Variabile calendarComponentStates non trovata."]

        js_obj_str = match.group(1)
        js_obj_str = js_obj_str.replace("'", '"')
        js_obj_str = re.sub(r'(\w+):', r'"\1":', js_obj_str)

        data = json.loads(js_obj_str)

        # Giorno corrente Europe/Rome
        tz = timezone(timedelta(hours=1))
        today_str = datetime.now(tz).strftime("%Y-%m-%d")

        # Cerca news del giorno
        days = data.get("1", {}).get("days", [])
        events_today = []
        for day in days:
            if today_str in day.get("date", ""):
                events_today = day.get("events", [])
                break

        if not events_today:
            return ["Nessun evento trovato oggi."]

        messages = ["📊 News Forex di oggi:\n"]
        for event in events_today:
            line = f"- {event.get('prefixedName','N/A')} ({event.get('timeLabel','All Day')})"
            if event.get("forecast"):
                line += f" | Previsione: {event['forecast']}"
            if event.get("actual"):
                line += f" | Attuale: {event['actual']}"
            if event.get("soloUrl"):
                line += f" | 🔗 https://www.forexfactory.com{event['soloUrl']}"
            messages.append(line)

        return messages

    except Exception as e:
        return [f"Errore durante lo scraping: {e}"]
