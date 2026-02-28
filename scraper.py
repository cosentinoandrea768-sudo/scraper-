import requests
import csv
from bs4 import BeautifulSoup
from datetime import datetime

def scrape_and_update_csv(csv_file_path):
    url = "https://www.forexfactory.com/calendar?week=this"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    events = []
    rows = soup.select("tr.calendar__row")
    print(f"[scraper] Trovate {len(rows)} righe nel calendario")  # log debug

    for i, row in enumerate(rows, 1):
        try:
            date = row.select_one(".calendar__date").get_text(strip=True)
            time = row.select_one(".calendar__time").get_text(strip=True)
            currency = row.select_one(".calendar__currency").get_text(strip=True)
            impact = row.select_one(".impact").get_text(strip=True)
            event_name = row.select_one(".calendar__event").get_text(strip=True)
            forecast = row.select_one(".forecast").get_text(strip=True)
            previous = row.select_one(".previous").get_text(strip=True)
            detail = row.select_one(".calendar__event__details").get_text(strip=True) if row.select_one(".calendar__event__details") else ""

            # Combina date e time in ISO
            if not time:
                time = "00:00"  # fallback se ora mancante
            dt = datetime.strptime(f"{date} {time}", "%b %d %Y %H:%M")
            iso_date = dt.strftime("%Y-%m-%d %H:%M")

            events.append([iso_date, currency, impact, event_name, "", forecast, previous, detail])
        except Exception as e:
            print(f"[scraper] Skipping riga {i} per errore: {e}")

    # Scrive CSV aggiornato
    with open(csv_file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["DateTime", "Currency", "Impact", "Event", "Actual", "Forecast", "Previous", "Detail"])
        writer.writerows(events)
    print(f"[scraper] Scritti {len(events)} eventi nel CSV")
