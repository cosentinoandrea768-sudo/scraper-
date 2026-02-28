import requests
import re
import json
from datetime import datetime, timezone, timedelta

FOREX_CALENDAR_URL = "https://www.forexfactory.com/calendar"

def get_forex_news(for_week=False):
    """
    Recupera le news dal JS embedded di ForexFactory.
    Se for_week=True, restituisce tutte le news della settimana.
    Altrimenti solo le news di oggi.
    Restituisce una lista di dizionari:
    [
        {
            "prefixedName": "...",
            "timeLabel": "...",
            "forecast": "...",
            "actual": "...",
            "url": "..."
        }, ...
    ]
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/115.0 Safari/537.36"
        }
        resp = requests.get(FOREX_CALENDAR_URL, headers=headers, timeout=10)
        resp.raise_for_status()
        html = resp.text

        # Cerca la variabile JS window.calendarComponentStates
        pattern = r"window\.calendarComponentStates\s*=\s*(\{.*?\});"
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            print("❌ Non ho trovato calendarComponentStates nel JS")
            return []

        data_js = match.group(1)
        # Converte in JSON valido (rimuove trailing commas e singoli apici)
        data_json = json.loads(
            re.sub(r",\s*([\]}])", r"\1", data_js.replace("'", '"'))
        )

        tz = timezone(timedelta(hours=1))  # Europe/Rome
        today_str = datetime.now(tz).strftime("%b %d")  # es. "Feb 28"

        news_list = []

        # data_json è un dict con chiave "1" → giorni
        for day in data_json.get("1", {}).get("days", []):
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

        return news_list

    except Exception as e:
        print(f"Errore nello scraping delle news: {e}")
        return []

# Test rapido
if __name__ == "__main__":
    news = get_forex_news(for_week=True)
    for n in news:
        print(n)
