import os
import logging
import requests
from datetime import datetime, timedelta
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
    raise RuntimeError("BOT_TOKEN e CHAT_ID devono essere impostati su Render")

FOREX_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

bot = Bot(token=BOT_TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

sent_events = set()

# Mappa country -> currency
COUNTRY_TO_CURRENCY = {
    "United States": "USD",
    "Eurozone": "EUR",
    "United Kingdom": "GBP",
    "Japan": "JPY",
    "Canada": "CAD",
    "Switzerland": "CHF",
    "Australia": "AUD",
    "New Zealand": "NZD",
}

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
# FOREX
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
    now = datetime.utcnow().replace(tzinfo=pytz.utc)
    week_ago = now - timedelta(days=7)

    high_impact = []
    for event in news:
        if event.get("impact") != "High":
            continue
        try:
            event_dt = datetime.fromisoformat(event.get("date")).astimezone(pytz.utc)
        except Exception:
            continue
        if week_ago <= event_dt <= now:
            high_impact.append(event)

    if initial:
        send_message("🚀 Bot avviato correttamente!")
        if high_impact:
            send_message("📌 Eventi High Impact della settimana passata:")

    for event in high_impact:
        event_id = event.get("id")
        if event_id in sent_events:
            continue

        country = event.get("country", "")
        currency = COUNTRY_TO_CURRENCY.get(country, "N/A")

        try:
            dt = datetime.fromisoformat(event.get("date")).astimezone(pytz.utc)
            date_str = dt.strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            date_str = event.get("date", "N/A")

        message = (
            f"📊 HIGH IMPACT NEWS\n"
            f"💱 Currency: {currency}\n"
            f"📰 Event: {event.get('title')}\n"
            f"⚡ Impact: {event.get('impact')}\n"
            f"⏰ Date/Time: {date_str}\n"
            f"📈 Previous: {event.get('previous', 'N/A')}\n"
            f"📊 Actual: {event.get('actual', 'N/A')}\n"
            f"🔮 Forecast: {event.get('forecast', 'N/A')}"
        )

        send_message(message)
        sent_events.add(event_id)

# ==============================
# FLASK APP
# ==============================

app = Flask(__name__)

@app.route("/")
def health():
    return "Bot attivo", 200

# ==============================
# SCHEDULER START
# ==============================

scheduler = BackgroundScheduler(timezone=pytz.utc)
scheduler.add_job(process_news, "interval", minutes=5)
scheduler.start()

logging.info("Scheduler avviato")
process_news(initial=True)
