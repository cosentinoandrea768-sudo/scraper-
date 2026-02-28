import os
import asyncio
import pandas as pd
from scraper import parse_table, init_driver
from utils import save_csv
from datetime import datetime, timedelta
import requests
import config

# =========================
# Telegram helper
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_message(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("[WARN] Telegram env vars non impostate.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code != 200:
            print(f"[WARN] Errore invio Telegram: {resp.text}")
    except Exception as e:
        print(f"[WARN] Impossibile inviare messaggio Telegram: {e}")

# =========================
# Funzioni principali
# =========================
async def main():
    # 1️⃣ Messaggio di avvio
    send_telegram_message("🚀 Bot avviato! Inizio scraping Forex Factory.")

    # 2️⃣ Calcola mese della prossima settimana
    now = datetime.now()
    next_week = now + timedelta(days=7)
    month = next_week.strftime("%B")
    year = str(next_week.year)

    # 3️⃣ Inizializza driver
    driver = init_driver(headless=True)
    url = f"https://www.forexfactory.com/calendar?month={month.lower()}"
    driver.get(url)

    # Salva timezone rilevata
    detected_tz = driver.execute_script("return Intl.DateTimeFormat().resolvedOptions().timeZone")
    config.SCRAPER_TIMEZONE = detected_tz

    # Scroll per caricare tutto
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    await asyncio.sleep(2)

    # 4️⃣ Scarica e salva dati
    data, _ = parse_table(driver, month, year)
    driver.quit()

    if not data:
        send_telegram_message(f"⚠️ Nessun dato trovato per {month} {year}")
        return

    # 5️⃣ Leggi CSV generato e manda messaggi Telegram
    csv_file = f"news/{month}_{year}_news.csv"
    df = pd.read_csv(csv_file)

    message = f"<b>🗓 News Forex Factory - Settimana prossima ({month} {year})</b>\n\n"
    for _, row in df.iterrows():
        message += f"{row['date']} {row['time']} | {row['currency']} | {row['impact']} | {row['event']}\n"
        if row['detail']:
            message += f"🔗 {row['detail']}\n"
    send_telegram_message(message[:4000])  # Telegram limita a ~4096 caratteri

# =========================
# Avvio
# =========================
if __name__ == "__main__":
    asyncio.run(main())
