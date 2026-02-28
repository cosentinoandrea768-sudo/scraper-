# main.py
import os
import csv
import pandas as pd
from datetime import datetime
from scraper import init_driver, scroll_to_end, parse_table, get_target_month
from config import TARGET_TIMEZONE
import pytz
import requests

# =========================
# Telegram settings
# =========================
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise RuntimeError("Devi impostare le variabili d'ambiente TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID")

# =========================
# Funzioni
# =========================
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code != 200:
            print(f"[WARN] Errore invio Telegram: {resp.text}")
    except Exception as e:
        print(f"[WARN] Fallito invio Telegram: {e}")


def read_events_from_csv(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        print(f"[WARN] File {file_path} non trovato")
        return pd.DataFrame()
    df = pd.read_csv(file_path)
    return df


def main():
    # Determina mese e anno correnti
    now = datetime.now()
    month = now.strftime("%B")
    year = now.year
    csv_file = f"news/{month}_{year}_news.csv"

    # Inizia lo scraping (opzionale, se vuoi aggiornare il CSV ogni volta)
    driver = init_driver(headless=True)
    url = f"https://www.forexfactory.com/calendar?month=this"
    print(f"[INFO] Navigando a {url}")
    driver.get(url)
    scroll_to_end(driver)

    # Scraping e salvataggio CSV
    print(f"[INFO] Parsing tabella per {month} {year}")
    try:
        parse_table(driver, month, str(year))
    except Exception as e:
        print(f"[ERROR] Fallito scraping: {e}")
    finally:
        driver.quit()

    # Leggi eventi dal CSV generato
    df = read_events_from_csv(csv_file)
    num_events = len(df)
    message = f"📊 Forex Factory: {num_events} eventi rilevanti trovati per {month} {year}."
    print(message)

    # Invia notifica su Telegram
    send_telegram_message(message)


if __name__ == "__main__":
    main()
