import os
import logging
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
import pytz

# ==============================
# CONFIG
# ==============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("BOT_TOKEN e CHAT_ID devono essere impostati")

FOREX_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

bot = Bot(token=BOT_TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

sent_events = set()

# ==============================
# TELEGRAM
# ==============================

def send_message(text):
    try:
        bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode="Markdown"
        )
        logging.info("Messaggio inviato")
    except Exception as e:
        logging.error(f"Errore Telegram: {e}")

# ==============================
# FOREX NEWS
# ==============================

def fetch_news():
    try:
        response = requests.get(
            FOREX_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Errore fetch news: {e}")
        return []

def process_news(initial=False):
    news = fetch_news()

    high_impact = [
        event for event in news
        if event.get("impact") == "High"
    ]

    if initial:
        send_message("🚀 *Bot avviato correttamente!*")
        if high_impact:
            send_message("📌 *Eventi High Impact di questa settimana:*")

    for event in high_impact:
        event_id = event.get("id")

        if event_id in sent_events:
            continue

        message = (
            f"📊 *HIGH IMPACT NEWS*\n"
            f"💱 {event.get('currency')}\n"
            f"📰 {event.get('title')}\n"
            f"⏰ {event.get('date')}"
        )

        send_message(message)
        sent_events.add(event_id)

# ==============================
# FLASK
# ==============================

app = Flask(__name__)

@app.route("/")
def health():
    return "Bot attivo", 200

# ==============================
# SCHEDULER
# ==============================

scheduler = BackgroundScheduler(timezone=pytz.utc)
scheduler.add_job(process_news, "interval", minutes=5)
scheduler.start()

# ==============================
# STARTUP
# ==============================

if __name__ == "__main__":
    logging.info("Avvio applicazione Docker...")

    # Esegue invio iniziale
    process_news(initial=True)

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
