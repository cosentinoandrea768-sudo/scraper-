from playwright.sync_api import sync_playwright
import re
import json
from datetime import datetime, timezone, timedelta

FOREX_CALENDAR_URL = "https://www.forexfactory.com/calendar"

def get_forex_news_today(for_week=False):
    """
    Recupera le news dal JS embedded di ForexFactory.
    for_week=False -> news di oggi
    for_week=True  -> news della settimana (test settimana prossima)
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(FOREX_CALENDAR_URL)
            html = page.content()
            browser.close()

        # Cerca la variabile JS window.calendarComponentStates
        pattern = r"window\.calendarComponentStates\s*=\s*(\{.*?\});"
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            return ["❌ Impossibile trovare calendarComponentStates nella pagina."]

        js_obj_str = match.group(1)
        js_obj_str = js_obj_str.replace("'", '"')
        js_obj_str = re.sub(r'(\w+):', r'"\1":', js_obj_str)  # chiavi senza virgolette
        data = json.loads(js_obj_str)

        tz = timezone(timedelta(hours=1))  # Europe/Rome
        today_str = datetime.now(tz).strftime("%b %d")  # es. "Feb 28"

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
