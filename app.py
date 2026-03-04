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
# GLOBAL STATE
# ==============================

monitored_events = {}

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
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            logging.warning("429 Too Many Requests")
        else:
            logging.error(f"HTTP error: {e}")
        return []
    except Exception as e:
        logging.error(f"Errore fetch news: {e}")
        return []

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
        actual_val = float(str(actual).replace("%", "").replace("K","000"))
        forecast_val = float(str(forecast).replace("%", "").replace("K","000"))

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
    global monitored_events

    news = fetch_news()
    if not news:
        return

    monitored_events = {}

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

            # Salviamo evento per monitoraggio actual
            key = (event.get("title"), event.get("country"))
            monitored_events[key] = event

        except Exception:
            continue

    if initial:
        send_message("🚀 Bot avviato correttamente!")

    if not found:
        send_message("📌 Oggi non ci sono eventi High Impact USD/EUR")
        return

    message += 'Aggiornamento dato quando esce "actual"'
    send_message(message)

# ==============================
# CONTROLLO ACTUAL
# ==============================

def check_all_events_update():
    global monitored_events

    if not monitored_events:
        logging.info("Nessun evento da monitorare")
        return

    news = fetch_news()
    if not news:
        return

    for key in list(monitored_events.keys()):
        title, country = key

        updated_item = next(
            (
                item for item in news
                if item.get("title") == title
                and item.get("country") == country
            ),
            None
        )

        if not updated_item:
            continue

        actual_value = updated_item.get("actual")

        if actual_value not in [None, ""]:
            country_flag = "🇺🇸" if country == "USD" else "🇪🇺"

            update_message = (
                f"📊 *AGGIORNAMENTO NEWS*\n\n"
                f"{country_flag} {country}\n"
                f"📰 {title}\n"
                f"📊 Actual: {updated_item.get('actual')}\n"
                f"🔮 Forecast: {updated_item.get('forecast') or 'n/a'}\n"
                f"{impact_logic(updated_item)}"
            )

            send_message(update_message)
            monitored_events.pop(key)

            logging.info(f"Actual inviato per {title}")
        else:
            logging.info(f"Actual non ancora disponibile per {title}")

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

scheduler.add_job(
    check_all_events_update,
    "interval",
    minutes=5,
    id="actual_update_job",
    next_run_time=datetime.now(pytz.utc) + timedelta(minutes=5),
    max_instances=1,
    coalesce=True
)

scheduler.start()
logging.info("Scheduler avviato")

# Avvio iniziale
process_news(initial=True)
