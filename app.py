import requests
import logging
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
import pytz

# ================= CONFIG =================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FOREX_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

bot = Bot(token=TOKEN)

logging.basicConfig(level=logging.INFO)

sent_events = set()

# ==========================================

def fetch_forex_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ForexNewsBot/1.0)",
        "Accept": "application/json"
    }

    try:
        response = requests.get(FOREX_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Errore fetch: {e}")
        return []


def send_telegram_message(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Errore Telegram: {e}")


def check_news():
    news = fetch_forex_news()
    now = datetime.utcnow()

    for event in news:
        impact = event.get("impact")
        title = event.get("title")
        currency = event.get("currency")
        event_id = event.get("id")
        event_time = event.get("date")

        if impact != "High":
            continue

        if event_id in sent_events:
            continue

        message = f"""
📊 *HIGH IMPACT NEWS*
💱 {currency}
📰 {title}
⏰ {event_time}
"""

        send_telegram_message(message)
        sent_events.add(event_id)


# Scheduler ogni 5 minuti
scheduler = BackgroundScheduler(timezone=pytz.utc)
scheduler.add_job(check_news, "interval", minutes=5)
scheduler.start()

# Per tenere vivo Render Web Service
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
