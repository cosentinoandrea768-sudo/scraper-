import os
import logging
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
from datetime import datetime, timedelta, timezone
import pytz
from dateutil import parser as date_parser

# ==============================
# CONFIGURAZIONE
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("BOT_TOKEN e CHAT_ID devono essere impostati nelle variabili d'ambiente di Render")

FOREX_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

bot = Bot(token=BOT_TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

sent_events = set()

# Mappa paese → valuta (puoi espandere se necessario)
COUNTRY_TO_CURRENCY = {
    "United States": "USD",
    "Eurozone":      "EUR",
    "Japan":         "JPY",
    "United Kingdom": "GBP",
    "Canada":        "CAD",
    "Australia":     "AUD",
    "Switzerland":   "CHF",
    "China":         "CNY",
    "New Zealand":   "NZD",
}

# ==============================
# TELEGRAM
# ==============================
def send_message(text):
    try:
        bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        logging.info("Messaggio Telegram inviato con successo")
    except Exception as e:
        logging.error(f"Errore invio messaggio Telegram: {e}")

# ==============================
# FETCH & PROCESS NEWS
# ==============================
def fetch_news():
    try:
        resp = requests.get(
            FOREX_URL,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ForexNewsBot/1.0)"},
            timeout=12
        )
        resp.raise_for_status()
        data = resp.json()
        logging.info(f"Scaricati {len(data)} eventi dal calendario Forex Factory")
        return data
    except Exception as e:
        logging.error(f"Errore durante fetch news: {e}")
        return []

def process_news(initial=False):
    news = fetch_news()
    if not news:
        if initial:
            send_message("🚀 Bot avviato, ma nessun dato ricevuto dal calendario al momento.")
        return

    now_utc = datetime.now(timezone.utc)
    time_window_start = now_utc - timedelta(hours=36)     # ultimi ~1.5 giorni
    time_window_end   = now_utc + timedelta(days=7)       # prossimi 7 giorni

    high_impact_events = []

    for event in news:
        impact = (event.get("impact") or "").strip()
        if impact != "High":
            continue

        date_str = event.get("date")
        if not date_str:
            continue

        try:
            # Parsa la data con offset (es: 2026-03-02T10:00:00-05:00)
            event_dt = date_parser.parse(date_str)
            # Converti tutto in UTC
            event_dt_utc = event_dt.astimezone(timezone.utc)
        except Exception as e:
            logging.warning(f"Impossibile parsare data '{date_str}': {e}")
            continue

        # Filtra per finestra temporale
        if not (time_window_start <= event_dt_utc <= time_window_end):
            continue

        high_impact_events.append((event, event_dt_utc))

    logging.info(f"Trovati {len(high_impact_events)} eventi High Impact nella finestra temporale")

    if initial:
        send_message("🚀 *Bot Forex News avviato correttamente!*\nControllo ogni 5 minuti per eventi High Impact.")
        if high_impact_events:
            send_message(f"📢 Trovati *{len(high_impact_events)}* eventi High Impact nei prossimi giorni / recenti.")

    for event, event_dt_utc in high_impact_events:
        event_id = event.get("id") or f"{event.get('title','?')}_{event_dt_utc.isoformat(timespec='minutes')}"
        if event_id in sent_events:
            continue

        currency = COUNTRY_TO_CURRENCY.get(event.get("country"), event.get("country", "—"))

        msg = (
            f"📊 **HIGH IMPACT EVENT**\n"
            f"💱 Valuta: **{currency}**\n"
            f"📰 Evento: {event.get('title', '—')}\n"
            f"⚡ Impatto: {impact}\n"
            f"⏰ Ora (UTC): {event_dt_utc.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"📈 Prec.: {event.get('previous', '—')}\n"
            f"🔮 Previsto: {event.get('forecast', '—')}\n"
            f"📊 Effettivo: {event.get('actual', '—')}"
        )

        send_message(msg)
        sent_events.add(event_id)
        logging.info(f"Inviato evento: {event.get('title')} – {currency}")

# ==============================
# FLASK per health check di Render
# ==============================
app = Flask(__name__)

@app.route("/")
def health():
    return "Bot Forex News è attivo", 200

# ==============================
# AVVIO SCHEDULER e prima esecuzione
# (eseguito al caricamento del modulo – corretto con Gunicorn)
# ==============================
scheduler = BackgroundScheduler(timezone=pytz.utc)
scheduler.add_job(func=process_news, trigger="interval", minutes=5)
scheduler.start()
logging.info("Scheduler avviato – controllo ogni 5 minuti")

# Esecuzione iniziale al boot
process_news(initial=True)

# Nota: NON mettere app.run() qui
# Gunicorn si occuperà di servire l'app Flask
