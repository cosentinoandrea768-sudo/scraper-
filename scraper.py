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
    for row in rows:
        try:
            date = row.select_one(".calendar__date").get_text(strip=True)
            time = row.select_one(".calendar__time").get_text(strip=True)
            currency = row.select_one(".calendar__currency").get_text(strip=True)
            impact = row.select_one(".impact").get_text(strip=True)
            event_name = row.select_one(".calendar__event").get_text(strip=True)
            forecast = row.select_one(".forecast").get_text(strip=True)
            previous = row.select_one(".previous").get_text(strip=True)
            detail = row.select_one(".calendar__event__details").get_text(strip=True) if row.select_one(".calendar__event__details") else ""

            # Combina date e time in formato ISO
            dt = datetime.strptime(f"{date} {time}", "%b %d %Y %H:%M")
            iso_date = dt.strftime("%Y-%m-%d %H:%M")

            events.append([iso_date, currency, impact, event_name, "", forecast, previous, detail])
        except:
            continue

    # Scrive CSV aggiornato
    with open(csv_file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["DateTime", "Currency", "Impact", "Event", "Actual", "Forecast", "Previous", "Detail"])
        writer.writerows(events)
