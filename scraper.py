import requests
from datetime import datetime, timedelta

# Costante per timezone
TIMEZONE_OFFSET = 1  # Europe/Rome

# Endpoint ForexFactory JSON
FF_URL = "https://npd-api.forexfactory.com/api.php"

def get_calendar_events(min_impact="medium"):
    """
    Scarica e filtra eventi ForexFactory secondo impatto minimo.
    
    Parametri:
        min_impact: 'low', 'medium', 'high'
    
    Ritorna:
        lista di eventi coerente con il tuo CSV
    """
    impact_map = {"low": 1, "medium": 2, "high": 3}
    min_level = impact_map.get(min_impact.lower(), 2)

    events_list = []

    try:
        resp = requests.get(FF_URL)
        resp.raise_for_status()
        data = resp.json()

        for day in data.get("calendar", []):
            day_dt = datetime.utcfromtimestamp(day.get("dateline", 0)) + timedelta(hours=TIMEZONE_OFFSET)
            for ev in day.get("events", []):
                ev_level = impact_map.get(ev.get("impactName", "low").lower(), 1)
                if ev_level < min_level:
                    continue

                events_list.append({
                    "date": day_dt.strftime("%Y-%m-%d"),
                    "time": ev.get("timeLabel", ""),
                    "currency": ev.get("currency", ""),
                    "impact": ev.get("impactName", "").capitalize(),
                    "title": ev.get("name", ""),
                    "forecast": ev.get("forecast", ""),
                    "previous": ev.get("previous", ""),
                    "actual": ev.get("actual", ""),
                    "url": "https://www.forexfactory.com" + ev.get("url", "")
                })

        return events_list

    except Exception as e:
        print("[scraper] Errore scraping ForexFactory:", e)
        return []
