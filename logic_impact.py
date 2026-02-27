import requests
import re
import json
from datetime import datetime

FOREX_URL = "https://www.forexfactory.com/calendar.php"

def get_forex_news_today():
    """
    Scarica la pagina di ForexFactory e legge la variabile JS
    window.calendarComponentStates per estrarre le news del giorno corrente.
    """
    try:
        r = requests.get(FOREX_URL)
        r.raise_for_status()
        html = r.text

        # Cerca window.calendarComponentStates = {...};
        match = re.search(r"window\.calendarComponentStates\s*=\s*({.*?});\s*</script>", html, re.DOTALL)
        if not match:
            return ["Impossibile trovare la variabile calendarComponentStates nella pagina."]

        js_obj_str = match.group(1)

        # Sostituisci eventuali differenze tra JS e JSON
        js_obj_str = js_obj_str.replace("'", '"')  # cambia apostrofi
        js_obj_str = re.sub(r'(\w+):', r'"\1":', js_obj_str)  # chiavi senza virgolette

        data = json.loads(js_obj_str)

        # Giorno corrente UTC
        today = datetime.utcnow().strftime("%Y-%m-%d")

        events_today = []
        for day in data["calendar"]["days"]:
            if day["date"] == today:
                events_today = day.get("events", [])
                break

        if not events_today:
            return ["Nessun evento trovato oggi."]

        # Formatta le news
        messages = ["📊 News Forex di oggi:\n"]
        for event in events_today:
            line = f"- {event['prefixedName']} ({event['timeLabel']})"
            if event.get("forecast"):
                line += f" | Previsione: {event['forecast']}"
            if event.get("actual"):
                line += f" | Attuale: {event['actual']}"
            messages.append(line)

        return messages

    except Exception as e:
        return [f"Errore durante lo scraping: {e}"]
