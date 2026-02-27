import requests
from bs4 import BeautifulSoup
import json

FOREX_CALENDAR_URL = "https://www.forexfactory.com/calendar"

def get_calendar_data():
    # Scarica la pagina principale del calendario
    r = requests.get(FOREX_CALENDAR_URL)
    r.raise_for_status()
    
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Cerca lo script contenente window.calendarComponentStates
    scripts = soup.find_all("script")
    calendar_json = None
    for script in scripts:
        if "window.calendarComponentStates" in script.text:
            # Estrai il JSON dopo il primo =
            js_text = script.string
            start = js_text.find("{")
            end = js_text.rfind("}") + 1
            calendar_json = js_text[start:end]
            break
    
    if not calendar_json:
        return []

    # Converte la stringa in dizionario Python
    try:
        data = json.loads(calendar_json)
        # La chiave 1 contiene i giorni
        return data["1"]["days"]
    except Exception as e:
        print("Errore parsing JSON:", e)
        return []

def get_todays_events():
    import datetime
    today_str = datetime.datetime.now().strftime("%b %d")  # Es: Feb 23
    events_today = []
    for day in get_calendar_data():
        if today_str in day["date"]:
            events_today.extend(day["events"])
    return events_today

def format_event(event):
    return (
        f"{event['timeLabel']} - {event['currency']} - {event['name']} "
        f"(Impact: {event['impactName']})\n"
        f"Actual: {event.get('actual','N/A')}, "
        f"Forecast: {event.get('forecast','N/A')}, "
        f"Previous: {event.get('previous','N/A')}\n"
        f"Link: https://www.forexfactory.com{event['url']}\n"
    )

if __name__ == "__main__":
    for ev in get_todays_events():
        print(format_event(ev))
