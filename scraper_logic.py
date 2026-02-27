# scraper_logic.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz

BASE_URL = "https://www.forexfactory.com/calendar.php?week=this"

def fetch_forex_factory_events():
    """
    Restituisce una lista di eventi Forex Factory della settimana corrente,
    filtrando solo medium e high impact, con previous, forecast e actual.
    """
    try:
        response = requests.get(BASE_URL, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except Exception as e:
        print("[ERROR] Fetching Forex Factory:", e)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    events = []

    # Forex Factory organizza gli eventi in righe della tabella
    rows = soup.select("tr.calendar__row")
    today = datetime.now(pytz.timezone("UTC")).date()

    for row in rows:
        # Controlla l'impatto
        impact_span = row.select_one("td.calendar__impact span")
        if not impact_span:
            continue
        impact_class = impact_span.get("class", [])
        if "medium" in impact_class:
            impact = "medium"
        elif "high" in impact_class:
            impact = "high"
        else:
            continue  # salta low impact

        # Ora e data evento
        time_td = row.select_one("td.calendar__time")
        if not time_td:
            continue
        event_time_str = time_td.text.strip()
        if not event_time_str:
            event_time_str = "00:00"

        # Controlla se l'evento è oggi
        # Forex Factory mostra la data nel dataset in un td con classe 'calendar__date'
        date_td = row.select_one("td.calendar__date")
        if date_td and date_td.text.strip():
            date_str = date_td.text.strip()
            try:
                event_date = datetime.strptime(date_str, "%b %d").replace(year=today.year).date()
            except:
                event_date = today
        else:
            event_date = today

        if event_date != today:
            continue

        # Nome evento e valuta
        name_td = row.select_one("td.calendar__event")
        currency_td = row.select_one("td.calendar__currency")
        previous_td = row.select_one("td.calendar__previous")
        forecast_td = row.select_one("td.calendar__forecast")
        actual_td = row.select_one("td.calendar__actual")

        event = {
            "id": row.get("id") or f"{currency_td.text.strip() if currency_td else 'X'}_{name_td.text.strip() if name_td else 'Event'}_{event_date}",
            "name": name_td.text.strip() if name_td else "Unknown",
            "currency": currency_td.text.strip() if currency_td else "-",
            "impact": impact,
            "date": event_date.strftime("%Y-%m-%d"),
            "time": event_time_str,
            "previous": previous_td.text.strip() if previous_td else "-",
            "forecast": forecast_td.text.strip() if forecast_td else "-",
            "actual": actual_td.text.strip() if actual_td else "-"
        }

        events.append(event)

    return events
