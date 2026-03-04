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

italy_tz = pytz.timezone("Europe/Rome")

# ==============================
# GLOBAL STATE
# ==============================

high_impact_events = []
monitored_events = {}
updated_events = set()

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
            timeout=15
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            logging.warning("429 Too Many Requests - rate limit raggiunto")
        else:
            logging.error(f"HTTP error: {e}")
        return []

    except Exception as e:
        logging.error(f"Errore fetch news: {e}")
        return []

# ==============================
# GENERAZIONE ID UNIVOCO
# ==============================

def generate_event_id(event):
    return f"{event.get('title')}_{event.get('date')}_{event.get('country')}"

# ==============================
# IMPACT LOGIC
# ==============================

def impact_logic(event):
    actual = event.get("actual")
    forecast = event.get("forecast")
    title = event.get("title", "").lower()

    if not actual or not forecast:
        return "⚖️ Impatto: n/a"

    try:
        actual_val = float(str(actual).replace("%", ""))
        forecast_val = float(str(forecast).replace("%", ""))

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
# PROCESS NEWS GIORNALIERO
# ==============================

def process_news(initial=False):
    global high_impact_events, monitored_events

    news = fetch_news()
    if not news:
        logging.info("Nessuna news disponibile")
        return

    now = datetime.now(timezone.utc)
    start_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_day = start_day + timedelta(days=1)

    high_impact_events = []
    monitored_events = {}

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
                event["parsed_date"] = event_date
                high_impact_events.append(event)

        except Exception:
            continue

    high_impact_events.sort(key=lambda x: x["parsed_date"])

    logging.info(f"Trovati {len(high_impact_events)} eventi High Impact USD/EUR oggi")

    if initial:
        send_message("🚀 Bot avviato correttamente!")

    if not high_impact_events:
        send_message("📌 Oggi non ci sono eventi High Impact USD/EUR")
        return

    message = "📅 *HIGH IMPACT USD/EUR – OGGI*\n\n"

    for event in high_impact_events:
        event_id = generate_event_id(event)
        event_date_italy = event["parsed_date"].astimezone(italy_tz)
        country_flag = "🇺🇸" if event.get("country") == "USD" else "🇪🇺"

        message += (
            f"🕒 *{event_date_italy.strftime('%H:%M')}*\n"
            f"{country_flag} {event.get('country')}\n"
            f"📰 {event.get('title')}\n"
            f"🔮 Forecast: {event.get('forecast') or 'n/a'}\n"
            f"📈 Previous: {event.get('previous') or 'n/a'}\n\n"
        )

        monitored_events[event_id] = event

    message += 'Aggiornamento dato quando esce "actual"'

    send_message(message)

# ==============================
# MONITORAGGIO ACTUAL
# ==============================

def check_all_events_update():
    global monitored_events, updated_events

    if not monitored_events:
        return

    news = fetch_news()
    if not news:
        return

    for event_id in list(monitored_events.keys()):
        original_event = monitored_events[event_id]

        updated_item = next(
            (item for item in news if generate_event_id(item) == event_id),
            None
        )

        actual_value = (
            updated_item.get("actual")
            if updated_item else None
        )

        if updated_item and actual_value not in [None, ""]:
            country_flag = "🇺🇸" if updated_item.get("country") == "USD" else "🇪🇺"

            update_message = (
                f"📊 *AGGIORNAMENTO NEWS*\n\n"
                f"{country_flag} {updated_item.get('country')}\n"
                f"📰 {updated_item.get('title')}\n"
                f"📊 Actual: {updated_item.get('actual')}\n"
                f"🔮 Forecast: {updated_item.get('forecast') or 'n/a'}\n"
                f"{impact_logic(updated_item)}"
            )

            send_message(update_message)

            updated_events.add(event_id)
            monitored_events.pop(event_id)

            logging.info(f"Aggiornamento inviato per evento {event_id}")
        else:
            logging.info(f"Actual non ancora disponibile per {event_id}")

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

# Job giornaliero
scheduler.add_job(
    process_news,
    CronTrigger(
        hour=6,
        minute=0,
        day_of_week="mon-fri",
        timezone=pytz.utc
    ),
    id="daily_news_job",
    max_instances=1,
    coalesce=True
)

# Job controllo actual ogni 5 minuti
scheduler.add_job(
    check_all_events_update,
    'interval',
    minutes=5,
    id="global_actual_update",
    next_run_time=datetime.now(pytz.utc) + timedelta(minutes=5),
    max_instances=1,
    coalesce=True
)

scheduler.start()
logging.info("Scheduler avviato")

# Esecuzione iniziale
process_news(initial=True)
