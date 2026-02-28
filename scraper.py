# scraper.py
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import os

# =========================
# Configurazione
# =========================
BASE_URL = "https://www.forexfactory.com/calendar"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
COOKIES = {
    "ff": os.getenv("FF_COOKIE", "")  # opzionale, se vuoi simulare login
}
TIMEZONE_OFFSET = int(os.getenv("TIMEZONE_OFFSET", 1))  # ore rispetto UTC

# =========================
# Funzioni interne
# =========================
def fetch_calendar_page():
    """Scarica la pagina del calendario da Forex Factory con user-agent e cookie."""
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(BASE_URL, headers=headers, cookies=COOKIES, timeout=15)
    resp.raise_for_status()
    return resp.text

def parse_calendar_events(html_content):
    """Estrae gli eventi dal JSON in window.calendarComponentStates."""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Trova lo script con calendarComponentStates
    script_tag = None
    for script in soup.find_all("script"):
        if "calendarComponentStates" in script.text:
            script_tag = script.text
            break
    if not script_tag:
        raise RuntimeError("Impossibile trovare calendarComponentStates nella pagina")
    
    # Estrai la parte JSON
    start_index = script_tag.find("window.calendarComponentStates[1] =") + len("window.calendarComponentStates[1] =")
    end_index = script_tag.find("};", start_index) + 1
    json_str = script_tag[start_index:end_index]

    # Converti in dict
    try:
        calendar_data = json.loads(json_str.replace("'", '"'))
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Errore parsing JSON: {e}")

    # Estrai eventi giorno per giorno
    events_list = []
    for day_entry in calendar_data.get("days", []):
        day_label = day_entry.get("date")
        for ev in day_entry.get("events", []):
            event_details = {
                "date": day_label,
                "name": ev.get("name"),
                "currency": ev.get("currency"),
                "impact": ev.get("impactClass"),
                "time": ev.get("timeLabel"),
                "forecast": ev.get("forecast"),
                "previous": ev.get("previous"),
                "actual": ev.get("actual"),
                "url": f"https://www.forexfactory.com{ev.get('url', '')}"
            }
            events_list.append(event_details)
    return events_list

# =========================
# Funzione pubblica per main.py
# =========================
def get_calendar_events():
    """Restituisce la lista di eventi pronta da usare."""
    html = fetch_calendar_page()
    return parse_calendar_events(html)

# =========================
# Test rapido
# =========================
if __name__ == "__main__":
    events = get_calendar_events()
    print(f"[scraper] Trovati {len(events)} eventi")
    for ev in events[:10]:  # stampa solo i primi 10 per verifica
        print(ev)
