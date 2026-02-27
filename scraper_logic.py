# scraper_logic.py
from bs4 import BeautifulSoup
from datetime import datetime
from playwright.sync_api import sync_playwright

FOREX_FACTORY_URL = "https://www.forexfactory.com/calendar?day=today"

def fetch_today_events():
    """
    Restituisce una lista di eventi di oggi medium e high impact.
    Ogni evento è un dict con: id, name, time, currency, impact
    """
    events = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(FOREX_FACTORY_URL)
            
            # aspetta che la pagina sia pronta (JS caricato)
            page.wait_for_timeout(3000)
            html = page.content()
            browser.close()
    except Exception as e:
        print("[SCRAPER ERROR] Playwright:", e)
        return []

    soup = BeautifulSoup(html, "html.parser")

    # Seleziona tutte le righe della tabella eventi
    for row in soup.select("tr.calendar__row"):
        impact_tag = row.select_one("td.calendar__impact span")
        if not impact_tag:
            continue
        impact = impact_tag.get("title", "").lower()
        if impact not in ["medium", "high"]:
            continue

        currency_tag = row.select_one("td.calendar__currency")
        currency = currency_tag.get_text(strip=True) if currency_tag else "N/A"

        name_tag = row.select_one("td.calendar__event")
        name = name_tag.get_text(strip=True) if name_tag else "N/A"

        time_tag = row.select_one("td.calendar__time")
        time_text = time_tag.get_text(strip=True) if time_tag else "-"
        event_time = time_text if time_text != "-" else "-"

        event_id = f"{currency}_{name}_{event_time}"
        events.append({
            "id": event_id,
            "name": name,
            "time": event_time,
            "currency": currency,
            "impact": impact
        })

    if not events:
        print("[SCRAPER INFO] Nessun evento trovato oggi")

    return events


def format_event_message(event):
    """
    Restituisce il messaggio pronto per Telegram
    """
    return (
        f"📌 Forex Factory Event\n"
        f"💰 {event['currency']}\n"
        f"🕒 {event['time']}\n"
        f"📝 {event['name']}\n"
        f"⚡ Impact: {event['impact'].capitalize()}"
    )
