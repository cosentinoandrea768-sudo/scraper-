import requests
import re
import json
from datetime import datetime, timezone, timedelta

FOREX_CALENDAR_URL = "https://www.forexfactory.com/calendar"

def get_forexfactory_news(week="this"):
    """
    Recupera le news dal JS embedded di ForexFactory.
    Parametri:
        week: "this" per settimana corrente, "next" per settimana prossima
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
        resp = requests.get(FOREX_CALENDAR_URL, timeout=10)
        resp.raise_for_status()
        html = resp.text

        # Cerca la variabile JS window.calendarComponentStates
        pattern = r"window\.calendarComponentStates\s*=\s*(\{.*?\});"
        match = re.search(pattern, html, re.DOTALL)

        if not match:
            print("❌ Non ho trovato calendarComponentStates nel JS")
            return []

        data_js = match.group(1)

        # Converte JS in JSON valido
        data_json = json.loads(
            re.sub(r",\s*([\]}])", r"\1", data_js.replace("'", '"'))
        )

        # Determina il giorno da leggere
        tz = timezone(timedelta(hours=1))  # Europe/Rome = UTC+1
        today = datetime.now(tz)
        if week == "next":
            today += timedelta(days=7)
        today_str = today.strftime("%b %d")  # es. "Feb 28"

        events_today = []

        # data_json è un dict con chiave "1" → giorni
        for day in data_json.get("1", {}).get("days", []):
            if today_str in day.get("date", ""):
                for event in day.get("events", []):
                    events_today.append({
                        "prefixedName": event.get("prefixedName", "N/A"),
                        "timeLabel": event.get("timeLabel", "All Day"),
                        "forecast": event.get("forecast", ""),
                        "actual": event.get("actual", ""),
                        "url": f"https://www.forexfactory.com{event.get('soloUrl','')}"
                    })
                break

        return events_today

    except Exception as e:
        print(f"Errore nello scraping delle news: {e}")
        return []

# --- Test rapido ---
if __name__ == "__main__":
    print("News settimana corrente:")
    for n in get_forexfactory_news("this"):
        print(n)
    print("\nNews settimana prossima:")
    for n in get_forexfactory_news("next"):
        print(n)
