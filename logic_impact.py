import requests
import re
import json
from datetime import datetime, timezone, timedelta

FOREX_CALENDAR_URL = "https://www.forexfactory.com/calendar"

def get_forex_news_today(for_week=False):
    """
    Recupera le news leggendo la variabile JS:
    window.calendarComponentStates
    Versione robusta per produzione.
    """

    try:
        session = requests.Session()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.forexfactory.com/"
        }

        session.headers.update(headers)

        # Prima visita homepage per ottenere cookie
        session.get("https://www.forexfactory.com", timeout=10)

        # Poi calendario
        response = session.get(FOREX_CALENDAR_URL, timeout=10)

        if response.status_code != 200:
            return [f"Errore HTTP: {response.status_code}"]

        html = response.text

        # Estrazione robusta della variabile JS
        match = re.search(
            r"window\.calendarComponentStates\s*=\s*(\{.*?\})\s*;",
            html,
            re.DOTALL
        )

        if not match:
            return ["❌ calendarComponentStates non trovata."]

        js_data = match.group(1)

        # Parsing JSON sicuro
        try:
            data = json.loads(js_data)
        except json.JSONDecodeError:
            return ["❌ Errore parsing JSON interno ForexFactory."]

        # Timezone Europa/Roma
        tz = timezone(timedelta(hours=1))
        today = datetime.now(tz).date()

        news_list = []

        # Struttura tipica: data["1"]["days"]
        for day_block in data.get("1", {}).get("days", []):

            day_str = day_block.get("date", "")

            # Parsing data tipo "Fri Feb 28"
            try:
                parsed_date = datetime.strptime(
                    f"{day_str} {today.year}",
                    "%a %b %d %Y"
                ).date()
            except:
                continue

            if not for_week and parsed_date != today:
                continue

            if for_week:
                if parsed_date < today or parsed_date > today + timedelta(days=7):
                    continue

            for event in day_block.get("events", []):

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
