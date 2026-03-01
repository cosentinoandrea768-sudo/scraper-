import os
import logging
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from datetime import datetime, timezone
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

def calculate_impact_logic(actual, forecast):
    try:
        actual_val = float(actual)
        forecast_val = float(forecast)
        if actual_val > forecast_val:
            return "Positive ✅"
        elif actual_val < forecast_val:
            return "Negative ❌"
        else:
            return "Neutral ⚪"
    except (TypeError, ValueError):
        return "-"

def process_news(initial=False, daily=False):
    news = fetch_news()

    now = datetime.now(timezone.utc)

    if daily:
        # Per il messaggio giornaliero, filtriamo solo eventi di oggi UTC
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        # Settimana intera (come prima)
        start_of_day = now - timedelta(days=now.weekday())
        end_of_day = now + timedelta(days=7)

    high_impact = [
        event for event in news
        if event.get("impact") == "High"
        and event.get("country") in ("USD", "EUR")
        and event.get("date") is not None
        and start_of_day <= datetime.fromisoformat(event.get("date")).astimezone(timezone.utc) <= end_of_day
    ]

    if initial:
        send_message("🚀 Bot avviato correttamente!")
        if high_impact:
            send_message("📌 Eventi High Impact USD/EUR della settimana:")

    elif daily and high_impact:
        send_message("📌 Eventi High Impact USD/EUR del giorno:")

    for event in high_impact:
        event_id = event.get("id")
        if event_id in sent_events and not daily:
            continue

        try:
            event_date = datetime.fromisoformat(event.get("date")).astimezone(timezone.utc)
        except Exception:
            event_date = event.get("date")

        impact_logic = calculate_impact_logic(event.get("actual"), event.get("forecast"))

        message = (
            f"📊 HIGH IMPACT NEWS\n"
            f"💱 Currency: {event.get('country')}\n"
            f"📰 Event: {event.get('title')}\n"
            f"⚡ Impact: {event.get('impact')}\n"
            f"⏰ Date/Time: {event_date if isinstance(event_date,str) else event_date.strftime('%Y-%m-%d %H:%M %Z')}\n"
            f"📈 Previous: {event.get('previous')}\n"
            f"📊 Actual: {event.get('actual')}\n"
            f"🔮 Forecast: {event.get('forecast')}\n"
            f"💡 Logic Impact: {impact_logic}"
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
scheduler.add_job(process_news, "interval", minutes=5)  # controllo news ogni 5 minuti
scheduler.add_job(
    lambda: process_news(daily=True),
    CronTrigger(hour=6, minute=0, day_of_week="mon-fri", timezone=pytz.timezone("Europe/Rome"))
)  # messaggio giornaliero alle 7 AM UTC+1 (6 AM UTC)
scheduler.start()

logging.info("Scheduler avviato")
process_news(initial=True)
