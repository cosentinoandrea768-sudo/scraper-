import os
import requests
import logging
from datetime import datetime, timedelta
from flask import Flask
from telegram import Bot

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise RuntimeError("Devi impostare BOT_TOKEN e CHAT_ID come Environment Variables!")

FOREX_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
ALLOWED_CURRENCIES = ["USD", "EUR"]

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

def process_news():
    news = fetch_forex_news()
    filtered_news = []

    # Data inizio settimana passata (lunedi) e fine settimana passata (domenica)
    today = datetime.utcnow()
    start_last_week = today - timedelta(days=today.weekday() + 7)  # lunedi scorso
    end_last_week = start_last_week + timedelta(days=6)  # domenica scorsa

    for event in news:
        try:
            event_id = event.get("id")
            currency = event.get("currency")
            impact = event.get("impact")
            title = event.get("title")
            event_time_str = event.get("date")  # formato yyyy-mm-dd
            event_time = datetime.strptime(event_time_str, "%Y-%m-%d")

            if event_id in sent_events:
                continue
            if impact != "High":
                continue
            if currency not in ALLOWED_CURRENCIES:
                continue
            if not (start_last_week.date() <= event_time.date() <= end_last_week.date()):
                continue

            message = (
                f"📊 *HIGH IMPACT NEWS*\n"
                f"💱 {currency}\n"
                f"📰 {title}\n"
                f"⏰ {event_time_str}"
            )
            filtered_news.append((event_id, message))
        except Exception as e:
            logging.error(f"Errore nel parsing evento: {e}")

    # Invia i messaggi filtrati
    if filtered_news:
        send_telegram_message(f"📌 *NEWS HIGH IMPACT USD/EUR SETTIMANA SCORSA ({start_last_week.date()} - {end_last_week.date()})*")
        for event_id, msg in filtered_news:
            send_telegram_message(msg)
            sent_events.add(event_id)
    else:
        send_telegram_message("ℹ️ Nessun evento USD/EUR High Impact trovato la settimana scorsa.")

# ================= FLASK WEB SERVER =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Forex Telegram Bot è attivo!"

@app.route("/send-news")
def send_news():
    process_news()
    return "News inviate su Telegram ✅"

# ================= MAIN =================
if __name__ == "__main__":
    # Messaggio all'avvio
    send_telegram_message("🚀 Bot avviato correttamente! Controllo news USD/EUR High Impact settimana scorsa...")

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
