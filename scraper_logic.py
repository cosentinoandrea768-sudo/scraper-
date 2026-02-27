# scraper_logic.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

FOREX_FACTORY_URL = "https://www.forexfactory.com/calendar?day=today"

IMPACT_MAP = {
    "High": "🔴 High Impact",
    "Medium": "🟠 Medium Impact",
    "Low": "⚪ Low Impact"
}

def fetch_today_events():
    """
    Scraping degli eventi di oggi da Forex Factory
    Restituisce una lista di dizionari:
    {
        'time': '14:30',
        'currency': 'USD',
        'impact': 'High',
        'event': 'Nonfarm Payrolls',
        'actual': '...', 
        'forecast': '...', 
        'previous': '...'
    }
    """
    events = []
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(FOREX_FACTORY_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # tutte le righe della calendar table
        rows = soup.select("tr.calendar__row")
        for row in rows:
            impact_tag = row.select_one("td.calendar__impact span")
            if not impact_tag:
                continue
            impact = impact_tag.get("title", "").strip()
            if impact not in ["Medium", "High"]:
                continue  # filtra solo medium e high

            currency_tag = row.select_one("td.calendar__currency")
            event_tag = row.select_one("td.calendar__event")
            time_tag = row.select_one("td.calendar__time")
            actual_tag = row.select_one("td.calendar__actual")
            forecast_tag = row.select_one("td.calendar__forecast")
            previous_tag = row.select_one("td.calendar__previous")

            # se non ci sono dati, metti -
            actual = actual_tag.text.strip() if actual_tag else "-"
            forecast = forecast_tag.text.strip() if forecast_tag else "-"
            previous = previous_tag.text.strip() if previous_tag else "-"

            event = {
                "time": time_tag.text.strip() if time_tag else "-",
                "currency": currency_tag.text.strip() if currency_tag else "-",
                "impact": impact,
                "event": event_tag.text.strip() if event_tag else "-",
                "actual": actual,
                "forecast": forecast,
                "previous": previous
            }
            events.append(event)
    except Exception as e:
        print("[SCRAPER ERROR]", e)
    
    return events


def format_event_message(event):
    """
    Formatta un singolo evento per Telegram
    """
    msg = (
        f"{IMPACT_MAP.get(event['impact'], '⚪')} | {event['currency']}\n"
        f"📝 {event['event']}\n"
        f"⏰ {event['time']}\n"
        f"Actual: {event['actual']} | Forecast: {event['forecast']} | Previous: {event['previous']}"
    )
    return msg
