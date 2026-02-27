# main.py
import os
import asyncio
from threading import Thread
from datetime import datetime
import pytz
from flask import Flask
from telegram import Bot

from scraper_logic import fetch_forex_factory_events
from logic_impact import evaluate_impact

# ==============================
# ENV VARS
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN o CHAT_ID non impostati")

bot = Bot(token=BOT_TOKEN)

# ==============================
# FLASK
# ==============================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot attivo ✅"

# ==============================
# GLOBAL STATE
# ==============================
sent_events = set()

# ==============================
# INVIO TELEGRAM
# ==============================
async def send_forex_events():
    events = fetch_forex_factory_events()
    if not events:
        print("[INFO] Nessun evento oggi")
        return

    for event in events:
        if event["id"] in sent_events:
            continue

        # Calcolo impatto
        label, score = evaluate_impact(event["name"], event["actual"], event["forecast"])

        message = (
            f"💹 Forex Factory Event ({event['impact'].upper()})\n"
            f"{event['currency']} - {event['name']}\n"
            f"🕒 {event['time']} UTC\n"
            f"Previous: {event['previous']}\n"
            f"Forecast: {event['forecast']}\n"
            f"Actual: {event['actual']}\n"
            f"Impact: {label}"
        )

        try:
            await bot.send_message(chat_id=CHAT_ID, text=message)
            sent_events.add(event["id"])
            print(f"[SENT] {event['name']}")
        except Exception as e:
            print("[TELEGRAM ERROR]", e)

# ==============================
# SCHEDULER
# ==============================
async def scheduler():
    # Messaggio di startup
    try:
        await bot.send_message(chat_id=CHAT_ID, text="🚀 Bot avviato correttamente - Forex Factory Monitor")
        print("[DEBUG] Messaggio di startup inviato")
    except Exception as e:
        print("[TELEGRAM ERROR] Startup:", e)

    while True:
        try:
            await send_forex_events()
        except Exception as e:
            print("[LOOP ERROR]", e)

        await asyncio.sleep(300)  # Controlla ogni 5 minuti

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    # Avvia Flask in background
    def run_flask():
        app.run(host="0.0.0.0", port=PORT)

    Thread(target=run_flask).start()

    # Avvia scheduler
    asyncio.run(scheduler())
