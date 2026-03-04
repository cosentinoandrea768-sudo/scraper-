import os
import logging
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from datetime import datetime, timedelta, timezone
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

italy_tz = pytz.timezone("Europe/Rome")

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
# PROCESS NEWS GIORNALIERO
# ==============================

def process_news(initial=False):

    news = fetch_news()
    if not news:
        logging.info("Nessuna news trovata")
        return

    now = datetime.now(timezone.utc)
    start_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_day = start_day + timedelta(days=1)

    message = "📅 *HIGH IMPACT USD/EUR – OGGI*\n\n"
    found = False

    for event in news:
        if event.get("impact") != "High":
            continue

        if event.get("country") not in ["USD", "EUR"]:
            continue

        try:
            event_date = datetime.fromisoformat(
                event.get("date").replace("Z", "+00:00")
            ).astimezone(timezone.utc)

            if not (start_day <= event_date < end_day):
                continue

            found = True

            event_date_it = event_date.astimezone(italy_tz)
            country_flag = "🇺🇸" if event.get("country") == "USD" else "🇪🇺"

            message += (
                f"🕒 *{event_date_it.strftime('%H:%M')}*\n"
                f"{country_flag} {event.get('country')}\n"
                f"📰 {event.get('title')}\n"
                f"🔮 Forecast: {event.get('forecast') or 'n/a'}\n"
                f"📈 Previous: {event.get('previous') or 'n/a'}\n\n"
            )

        except Exception:
            continue

    if initial:
        send_message("🚀 Bot avviato correttamente!")

    if not found:
        send_message("📌 Oggi non ci sono eventi High Impact USD/EUR")
        return

    send_message(message)

# ==============================
# FLASK APP
# ==============================

app = Flask(__name__)

@app.route("/")
def health():
    return "Bot attivo", 200

# ==============================
# SCHEDULER
# ==============================

scheduler = BackgroundScheduler(timezone=pytz.utc)

scheduler.add_job(
    process_news,
    CronTrigger(hour=6, minute=0, day_of_week="mon-fri", timezone=pytz.utc),
    id="daily_news_job",
    max_instances=1,
    coalesce=True
)

scheduler.start()
logging.info("Scheduler avviato")

# Avvio iniziale al deploy
process_news(initial=True)
