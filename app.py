import os
import logging
import requests
from datetime import datetime
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

def process_news(initial=False):
    news = fetch_news()

    if not news:
        logging.info("Nessuna news trovata")
        return

    # Filtro: High Impact + USD/EUR
    filtered_news = [
        event for event in news
        if event.get("impact") == "High"
        and event.get("currency") in ["USD", "EUR"]
    ]

    if not filtered_news:
        logging.info("Nessun evento USD/EUR High Impact trovato")
        return

    # Ordina per data se possibile
    def parse_date(event):
        try:
            return datetime.strptime(event.get("date"), "%Y-%m-%d %H:%M:%S")
        except:
            return datetime.max

    filtered_news.sort(key=parse_date)

    if initial:
        header = "🚀 *Bot avviato correttamente!*\n\n"
        header += "📅 *Eventi HIGH IMPACT della settimana*\n"
        header += "💱 Valute filtrate: USD & EUR\n\n"
    else:
        header = "📅 *Aggiornamento Eventi HIGH IMPACT*\n\n"

    message_body = ""

    for event in filtered_news:
        event_id = event.get("id")

        if event_id in sent_events:
            continue

        currency = event.get("currency")
        title = event.get("title")
        date_str = event.get("date")

        message_body += (
            f"📊 *{currency}*\n"
            f"📰 {title}\n"
            f"⏰ {date_str}\n\n"
        )

        sent_events.add(event_id)

    if message_body:
        full_message = header + message_body
        send_message(full_message)
        logging.info(f"Inviati {len(filtered_news)} eventi filtrati")

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
