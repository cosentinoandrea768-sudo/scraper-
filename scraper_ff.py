import requests
from datetime import datetime, timedelta

# Offset per Europe/Rome
TIMEZONE_OFFSET = 1  

# Endpoint API JSON di ForexFactory
BASE_URL = "https://npd-api.forexfactory.com/api.php"

def fetch_ff_events(min_impact="medium"):
    """
    Scarica gli eventi dal ForexFactory JSON API.
    
    Parametri:
        min_impact: 'low', 'medium', 'high' - filtra solo eventi di almeno questo impatto

    Ritorna:
        lista di dizionari con eventi aggiornati
    """
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()
        data = response.json()

        events_list = []

        # Mappa per il filtro impatto
        impact_levels = {"low": 1, "medium": 2, "high": 3}
        min_level = impact_levels.get(min_impact.lower(), 2)

        for day in data.get("calendar", []):
            day_date = datetime.utcfromtimestamp(day.get("dateline")) + timedelta(hours=TIMEZONE_OFFSET)
            for ev in day.get("events", []):
                ev_level = impact_levels.get(ev.get("impactName", "low").lower(), 1)
                if ev_level >= min_level:
                    events_list.append({
                        "date": day_date.strftime("%Y-%m-%d"),
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
        print("[scraper_ff] Errore nel fetch eventi:", e)
        return []
