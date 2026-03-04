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
updated_events = set()
scheduled_events = set()

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
# FOREX FETCH
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

# ==============================
# IMPACT LOGIC PROFESSIONALE
# ==============================

def impact_logic(event):
    actual = event.get("actual")
    forecast = event.get("forecast")
    title = event.get("title", "").lower()

    if actual is None or forecast is None:
        return "⚖️ Impatto: n/a"

    try:
        actual_val = float(actual)
        forecast_val = float(forecast)

        inverse_keywords = ["unemployment", "jobless", "claims"]
        is_inverse = any(word in title for word in inverse_keywords)

        if is_inverse:
            if actual_val < forecast_val:
                return "📈 Impatto: Positivo"
            elif actual_val > forecast_val:
                return "📉 Impatto: Negativo"
            else:
                return "⚖️ Impatto: Neutro"
        else:
            if actual_val > forecast_val:
                return "📈 Impatto: Positivo"
            elif actual_val < forecast_val:
                return "📉 Impatto: Negativo"
            else:
                return "⚖️ Impatto: Neutro"

    except Exception:
        return "⚖️ Impatto: n/a"

# ==============================
# UPDATE EVENTO CON RETRY
# ==============================

def check_event_update(event_id, retry_count=0):

    MAX_RETRY = 5
    RETRY_DELAY_MINUTES = 2

    news = fetch_news()

    for event in news:
        if event.get("id") == event_id:

            actual = event.get("actual")

            if actual is None:
                if retry_count < MAX_RETRY:
                    logging.info(f"Actual non disponibile per {event_id}, retry {retry_count+1}")

                    scheduler.add_job(
                        check_event_update,
                        trigger="date",
                        run_date=datetime.now(timezone.utc) + timedelta(minutes=RETRY_DELAY_MINUTES),
                        args=[event_id, retry_count + 1]
                    )
                else:
                    logging.info(f"Max retry raggiunto per {event_id}")
                return

            if event_id in updated_events:
                return

            update_message = (
                f"📊 AGGIORNAMENTO NEWS\n"
                f"💱 Currency: {event.get('country')}\n"
                f"📰 Event: {event.get('title')}\n"
                f"📊 Actual: {actual}\n"
                f"🔮 Forecast: {event.get('forecast')}\n"
                f"{impact_logic(event)}"
            )

            send_message(update_message)
            updated_events.add(event_id)
            logging.info(f"Aggiornamento inviato per evento {event_id}")
            return

# ==============================
# PROCESS NEWS GIORNALIERO
# ==============================

def process_news(initial=False):

    news = fetch_news()
    now = datetime.now(timezone.utc)

    high_impact = []

    start_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_day = start_day + timedelta(days=1)

    for event in news:

        if event.get("impact") != "High":
            continue

        if event.get("country") not in ["USD", "EUR"]:
            continue

        try:
            event_date = datetime.fromisoformat(
                event.get("date").replace("Z", "+00:00")
            ).astimezone(timezone.utc)

            if start_day <= event_date < end_day:
                high_impact.append(event)

        except Exception as e:
            logging.warning(f"Errore parsing data evento: {e}")
            continue

    logging.info(f"Trovati {len(high_impact)} eventi High Impact USD/EUR oggi")

    if initial:
        send_message("🚀 Bot avviato correttamente!")

    if not high_impact:
        send_message("📌 Oggi non ci sono eventi High Impact USD/EUR")
        return

    send_message("📌 Eventi High Impact USD/EUR di oggi:")

    for event in high_impact:

        event_id = event.get("id")

        event_date = datetime.fromisoformat(
            event.get("date").replace("Z", "+00:00")
        ).astimezone(timezone.utc)

        # INVIO NEWS
        if event_id not in sent_events:

            message = (
                f"📊 HIGH IMPACT NEWS\n"
                f"💱 Currency: {event.get('country')}\n"
                f"📰 Event: {event.get('title')}\n"
                f"⚡ Impact: {event.get('impact')}\n"
                f"⏰ Date/Time: {event_date.strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"📈 Previous: {event.get('previous')}\n"
                f"📊 Actual: {event.get('actual')}\n"
                f"🔮 Forecast: {event.get('forecast')}"
            )

            send_message(message)
            sent_events.add(event_id)

        # SCHEDULAZIONE CONTROLLO ACTUAL
        if event_id not in scheduled_events and event_date > now:

            run_time = event_date + timedelta(minutes=1)

            scheduler.add_job(
                check_event_update,
                trigger="date",
                run_date=run_time,
                args=[event_id]
            )

            scheduled_events.add(event_id)
            logging.info(f"Schedulato controllo per evento {event_id}")

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

trigger_daily = CronTrigger(
    hour=6,
    minute=0,
    day_of_week="mon-fri",
    timezone=pytz.utc
)

scheduler.add_job(process_news, trigger_daily)
scheduler.start()

logging.info("Scheduler avviato")

process_news(initial=True)
