import os
import requests
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from flask import Flask
from telegram import Bot
import pytz

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise RuntimeError("Devi impostare BOT_TOKEN e CHAT_ID come Environment Variables!")

FOREX_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
bot = Bot(token=TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Memoria eventi già inviati per evitare duplicati
sent_events = set()
# ==========================================

def fetch_forex_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ForexNewsBot/1.0)",
        "Accept": "application/json"
    }

    try:
        response = requests.get(FOREX_URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info(f"Fetched {len(data)} events from Forex Factory")
        return data
    except Exception as e:
        logging.error(f"Errore fetch Forex Factory: {e}")
        return []

def send_telegram_message(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
        logging.info("Messaggio inviato su Telegram")
    except Exception as e:
        logging.error(f"Errore invio Telegram: {e}")

def check_news(initial=False):
    news = fetch_forex_news()
    for event in news:
        event_id = event.get("id")
        impact = event.get("impact")
        title = event.get("title")
        currency = event.get("currency")
        event_time = event.get("date")

        if impact != "High":
            continue

        if event_id in sent_events:
            continue

        message = (
            f"📊 *HIGH IMPACT NEWS*\n"
            f"💱 {currency}\n"
            f"📰 {title}\n"
            f"⏰ {event_time}"
        )

        # Se è il primo invio all'avvio, aggiungi prefisso "SETTIMANA"
        if initial:
            message = "📌 *NEWS HIGH IMPACT QUESTA SETTIMANA*\n" + message

        send_telegram_message(message)
        sent_events.add(event_id)

# ================= SCHEDULER =================
scheduler = BackgroundScheduler(timezone=pytz.utc)
scheduler.add_job(check_news, 'interval', minutes=5)
scheduler.start()
logging.info("Scheduler avviato. Controllo news ogni 5 minuti.")

# ================= FLASK WEB SERVER =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Forex Telegram Bot è attivo!"

if __name__ == "__main__":
    # Invio messaggio di avvio
    send_telegram_message("🚀 Bot avviato correttamente! Controllo news High Impact questa settimana...")

    # Invia tutte le news High Impact già presenti
    check_news(initial=True)

    # Avvia Flask su porta dinamica
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
