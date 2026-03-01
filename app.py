import os
import logging
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
from datetime import datetime
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

    high_impact = [event for event in news if event.get("impact") == "High"]

    if initial:
        send_message("🚀 Bot avviato correttamente!")
        if high_impact:
            send_message("📌 Eventi High Impact di questa settimana:")

    for event in high_impact:
        event_id = event.get("id")
        if event_id in sent_events:
            continue

        # Pulizia dei dati
        currency = event.get("currency") or "N/A"
        title = event.get("title") or "N/A"
        impact = event.get("impact") or "N/A"
        date_str = event.get("date") or ""
        time_str = event.get("time") or ""

        # Formattazione data/ora
        dt_str = f"{date_str} {time_str}".strip()
        if dt_str:
            try:
                dt = datetime.fromisoformat(dt_str)
                dt = dt.astimezone(pytz.utc)
                dt_formatted = dt.strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                dt_formatted = dt_str
        else:
            dt_formatted = "N/A"

        previous = event.get("previous") or "N/A"
        actual = event.get("actual") or "N/A"
        forecast = event.get("forecast") or "N/A"

        message = (
            f"📊 HIGH IMPACT NEWS\n"
            f"💱 Currency: {currency}\n"
            f"📰 Event: {title}\n"
            f"⚡ Impact: {impact}\n"
            f"⏰ Date/Time: {dt_formatted}\n"
            f"📈 Previous: {previous}\n"
            f"🔮 Forecast: {forecast}\n"
            f"📊 Actual: {actual}"
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
