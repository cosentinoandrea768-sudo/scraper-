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
    now = datetime.now(timezone.utc)

    # Se initial=True, manda messaggio di avvio
    if initial:
        send_message("🚀 Bot avviato correttamente!")
    
    # Filtra solo USD e EUR e High Impact
    high_impact = [
        event for event in news
        if event.get("impact") == "High"
        and event.get("country") in ("USD", "EUR")
    ]

    # Filtra le news del giorno corrente UTC+1
    utc1 = pytz.timezone("Etc/GMT-1")
    today = now.astimezone(utc1).date()

    todays_news = []
    for event in high_impact:
        event_date = datetime.fromisoformat(event.get("date")).astimezone(utc1)
        if event_date.date() == today:
            todays_news.append((event, event_date))

    if not todays_news and initial:
        send_message("📌 Nessuna news High Impact USD/EUR oggi")
        return

    if initial and todays_news:
        send_message("📌 Eventi High Impact USD/EUR di oggi:")

    for event, event_date in todays_news:
        event_id = event.get("id")
        if event_id in sent_events:
            continue

        # Calcolo positivo/negativo se actual disponibile
        actual = event.get("actual")
        forecast = event.get("forecast")
        impact_logic = ""
        if actual is not None and forecast is not None:
            try:
                actual_f = float(actual)
                forecast_f = float(forecast)
                if actual_f > forecast_f:
                    impact_logic = "📈 Positivo"
                elif actual_f < forecast_f:
                    impact_logic = "📉 Negativo"
            except ValueError:
                pass  # lascia vuoto se non numerico

        message = (
            f"📊 HIGH IMPACT NEWS\n"
            f"💱 Currency: {event.get('country')}\n"
            f"📰 Event: {event.get('title')}\n"
            f"⚡ Impact: {event.get('impact')}\n"
            f"⏰ Date/Time: {event_date.strftime('%Y-%m-%d %H:%M %Z')}\n"
            f"📈 Previous: {event.get('previous')}\n"
            f"📊 Actual: {actual}\n"
            f"🔮 Forecast: {forecast}\n"
            f"{impact_logic}"
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

# Job giornaliero alle 7:00 UTC+1, lun-ven
trigger = CronTrigger(
    hour=6, minute=0,  # 7:00 UTC+1 = 6:00 UTC
    day_of_week="mon-fri",
    timezone=pytz.utc
)
scheduler.add_job(process_news, trigger)

scheduler.start()
logging.info("Scheduler avviato")

# Messaggio all'avvio
process_news(initial=True)
