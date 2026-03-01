import os
import logging
import requests
from datetime import datetime
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
import pytz

# ==============================
# FLASK APP (DEVE STARE IN ALTO)
# ==============================

app = Flask(__name__)

# ==============================
# CONFIG
# ==============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("BOT_TOKEN e CHAT_ID devono essere impostati su Render")

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
        logging.info("Messaggio inviato su Telegram")
    except Exception as e:
        logging.error(f"Errore invio Telegram: {e}")

# ==============================
# FETCH NEWS
# ==============================

def fetch_news():
    try:
        response = requests.get(
            FOREX_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Errore fetch news: {e}")
        return []

# ==============================
# PROCESS NEWS
# ==============================

def process_news():
    news = fetch_news()

    if not news:
        logging.info("Nessuna news trovata")
        return

    filtered_news = []

    for event in news:
        impact = str(event.get("impact", ""))
        currency = event.get("currency", "")

        if "High" in impact and currency in ["USD", "EUR"]:
            filtered_news.append(event)

    if not filtered_news:
        logging.info("Nessun evento USD/EUR High Impact trovato")
        return

    # Ordina per data
    def parse_date(event):
        try:
            return datetime.strptime(event.get("date"), "%Y-%m-%d %H:%M:%S")
        except:
            return datetime.max

    filtered_news.sort(key=parse_date)

    message = "📅 *Eventi HIGH IMPACT - USD & EUR*\n\n"

    for event in filtered_news:
        event_id = event.get("id")

        if event_id in sent_events:
            continue

        message += (
            f"📊 *{event.get('currency')}*\n"
            f"📰 {event.get('title')}\n"
            f"⏰ {event.get('date')}\n\n"
        )

        sent_events.add(event_id)

    if message.strip() != "📅 *Eventi HIGH IMPACT - USD & EUR*":
        send_message(message)

# ==============================
# HEALTH ROUTE
# ==============================

@app.route("/")
def health():
    return "Bot attivo", 200

# ==============================
# SCHEDULER
# ==============================

scheduler = BackgroundScheduler(timezone=pytz.utc)
scheduler.add_job(process_news, "interval", minutes=5)
scheduler.start()

logging.info("Scheduler avviato")
process_news(
