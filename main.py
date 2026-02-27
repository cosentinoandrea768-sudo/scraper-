import os
import asyncio
from datetime import datetime
from threading import Thread

from flask import Flask
from telegram import Bot

from scraper_logic import fetch_today_events, format_event_message  # import dalle tue funzioni scraper

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
    return "Bot Forex Factory attivo ✅"

# ==============================
# GLOBAL STATE
# ==============================
sent_events = set()  # per non mandare duplicati

# ==============================
# FUNZIONE INVIO EVENTI
# ==============================
async def send_forex_events():
    today_events = fetch_today_events()  # restituisce lista di dict eventi filtrati medium/high

    if not today_events:
        print("[INFO] Nessun evento ad alto impatto oggi")
        return

    for event in today_events:
        event_id = f"{event['time']}_{event['currency']}_{event['name']}"
        if event_id in sent_events:
            continue

        message = format_event_message(event)  # funzione che formatta testo da inviare
        try:
            await bot.send_message(chat_id=CHAT_ID, text=message)
            sent_events.add(event_id)
            print(f"[SENT] {event['name']}")
        except Exception as e:
            print("[TELEGRAM ERROR]", e)

# ==============================
# SCHEDULER
# ==============================
async def scheduler():
    # Messaggio di startup
    try:
        await bot.send_message(chat_id=CHAT_ID, text="🚀 Bot Forex Factory avviato ✅")
        print("[DEBUG] Messaggio di startup inviato")
    except Exception as e:
        print("[TELEGRAM ERROR] Startup:", e)

    while True:
        try:
            await send_forex_events()
        except Exception as e:
            print("[LOOP ERROR]", e)

        await asyncio.sleep(300)  # ogni 5 minuti

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
