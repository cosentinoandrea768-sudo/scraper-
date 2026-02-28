import os
import pandas as pd
from flask import Flask
from scraper import parse_table, get_target_month
from utils import save_csv
import config
import requests
from datetime import datetime

# Telegram env vars
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

app = Flask(__name__)

def send_telegram_message(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("[WARN] Telegram BOT_TOKEN o CHAT_ID non impostati")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"[ERROR] Impossibile inviare messaggio Telegram: {e}")

@app.route("/")
def home():
    # Invia messaggio di conferma avvio
    send_telegram_message(f"Bot avviato correttamente alle {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Esegue scraping delle news della prossima settimana come test
    month, year = get_target_month()
    driver_data, month = parse_table(driver=None, month=month, year=year)  # Usa driver in base a scraper.py
    save_csv(driver_data, month, year)

    # Legge CSV e invia news
    df = pd.read_csv(f"news/{month}_{year}_news.csv")
    messages = []
    for _, row in df.iterrows():
        messages.append(f"{row['date']} {row['time']} {row['currency']} {row['impact']} {row['event']}")
    for msg in messages[:10]:  # manda solo le prime 10 news per test
        send_telegram_message(msg)

    return "Bot eseguito correttamente!"

if __name__ == "__main__":
    # Avvia Flask web server
    app.run(host="0.0.0.0", port=5000)
