import requests
import re
import json
from datetime import datetime, timezone, timedelta

FOREX_CALENDAR_URL = "https://www.forexfactory.com/calendar"

def get_forex_news_today(for_week=False):
    """
    Recupera le news dal JS embedded di ForexFactory.
    Versione robusta anti-403 per Render.
    """
    try:
        session = requests.Session()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": "https://www.forexfactory.com/"
        }

        session.headers.update(headers)

        # Prima richiesta per ottenere cookie
        session.get("https://www.forexfactory.com", timeout=10)

        # Seconda richiesta calendario
        resp = session.get(FOREX_CALENDAR_URL, timeout=10)

        if resp.status_code != 200:
            return [f"Errore HTTP: {resp.status_code}"]

        html = resp.text

        pattern = r"window\.calendarComponentStates\s*=\s*(\{.*?\});"
        match = re.search(pattern, html, re.DOTALL)

        if not match:
            return ["❌ Impossibile trovare calendarComponentStates nella pagina."]

        js_obj_str = match.group(1)
        js_obj_str = js_obj_str.replace("'", '"')
        js_obj_str = re.sub(r'(\w+):', r'"\1":', js_obj_str)

        data = json.loads(js_obj_str)

        tz = timezone(timedelta(hours=1))
        today_str = datetime.now(tz).strftime("%b %d")

        news_list = []

        for day in data.get("1", {}).get("days", []):
            day_date = day.get("date", "")

            if not for_week and today_str not in day_date:
                continue

            for event in day.get("events", []):
                news_list.append({
                    "prefixedName": event.get("prefixedName", "N/A"),
                    "timeLabel": event.get("timeLabel", "All Day"),
                    "forecast": event.get("forecast", ""),
                    "actual": event.get("actual", ""),
                    "url": f"https://www.forexfactory.com{event.get('soloUrl','')}"
                })

        if not news_list:
            return ["Nessun evento trovato."]

        return news_list

    except Exception as e:
        return [f"Errore nello scraping: {e}"]
