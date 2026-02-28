from flask import Flask
import threading
import time
import os
from scraper import parse_table, init_driver
from utils import save_csv
import config
import pandas as pd
from datetime import datetime, timedelta
import requests

# -----------------------
# Config Telegram
# -----------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# -----------------------
# Funzioni Telegram
# -----------------------
def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("[WARN] Telegram BOT_TOKEN or CHAT_ID missing")
        return
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(TELEGRAM_API, data=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram message: {e}")

# -----------------------
# Funzioni Bot
# -----------------------
def run_scraper_test():
    """Scrape next week's news as a test and send to Telegram"""
    driver = init_driver()
    now = datetime.now()
    next_week = now + timedelta(days=7)
    month = next_week.strftime("%B")
    year = str(next_week.year)

    try:
        data, month = parse_table(driver, month, year)
        send_telegram_message(f"[INFO] Scraping done for {month} {year}. {len(data)} events found.")
    except Exception as e:
        send_telegram_message(f"[ERROR] Failed scraping: {e}")
    finally:
        driver.quit()

# -----------------------
# Flask Server
# -----------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Forex Factory Bot is running ✅"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# -----------------------
# Avvio Thread Bot
# -----------------------
def start_bot():
    send_telegram_message("🤖 Bot avviato su Render!")
    run_scraper_test()

if __name__ == "__main__":
    # Thread Flask
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Thread bot in background
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()
