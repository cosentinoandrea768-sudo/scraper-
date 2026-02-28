# scraper.py
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta

# =========================
# Configurazione
# =========================
BASE_URL = "https://www.forexfactory.com/calendar"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
COOKIES = {
    "ff": "your_forexfactory_cookie_here"  # opzionale, se vuoi simulare login
}
TIMEZONE_OFFSET = 1  # ore rispetto UTC

# =========================
# Funzioni
# =========================
def fetch_calendar_page():
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(BASE_URL, headers=headers, cookies=COOKIES, timeout=15)
    resp.raise_for_status()
    return resp.text

def parse_calendar_events(html):
    soup = BeautifulSoup(html, "html.parser")
    
    # Trova lo script con calendarComponentStates
    script_tag = None
    for script in soup.find_all("script"):
        if "calendarComponentStates" in script.text:
            script_tag = script.text
            break
    if not script_tag:
        raise RuntimeError("Impossibile trovare calendarComponentStates nella pagina")
    
    # Estrai la parte JSON
    start = script_tag.find("window.calendarComponentStates[1] =") + len("window.calendarComponentStates[1] =")
    end = script_tag.find("};", start) + 1
    json_str = script_tag[start:end]

    # Converti in dict
    try:
        calendar_data = json.loads(json_str.replace("'", '"'))
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Errore parsing JSON: {e}")

    # Estrai eventi giorno per giorno
    all_events = []
    for day in calendar_data.get("days", []):
        day_date = day.get("date")
        for ev in day.get("events", []):
            event_info = {
                "date": day_date,
                "name": ev.get("name"),
                "currency": ev.get("currency"),
                "impact": ev.get("impactClass"),
                "time": ev.get("timeLabel"),
                "forecast": ev.get("forecast"),
                "previous": ev.get("previous"),
                "actual": ev.get("actual"),
                "url": f"https://www.forexfactory.com{ev.get('url', '')}"
            }
            all_events.append(event_info)
    return all_events

# =========================
# Test rapido
# =========================
if __name__ == "__main__":
    html = fetch_calendar_page()
    events = parse_calendar_events(html)
    print(f"[scraper] Trovati {len(events)} eventi")
    for ev in events[:10]:  # stampa solo i primi 10 per verifica
        print(ev)
