import os
import asyncio
from threading import Thread
from flask import Flask
from telegram import Bot
from scraper_logic import fetch_today_events, format_event_message

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
    return "Scraper Bot attivo ✅"

# ==============================
# GLOBAL STATE
# ==============================
sent_events = set()

# ==============================
# INVIO TELEGRAM
# ==============================
async def send_today_events():
    events = fetch_today_events()
    if not events:
        print("[INFO] Nessuna news oggi")
        return

    for event in events:
        if event['impact'].lower() not in ['medium', 'high']:
            continue

        if event["id"] in sent_events:
            continue

        message = format_event_message(event)
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
        await bot.send_message(chat_id=CHAT_ID, text="🚀 Bot avviato correttamente. Inizio invio news Forex Factory!")
        print("[DEBUG] Messaggio di startup inviato")
    except Exception as e:
        print("[TELEGRAM ERROR] Startup:", e)

    # Primo invio subito all'avvio
    await send_today_events()

    # Poi invio ogni 10 minuti
    while True:
        try:
            await send_today_events()
        except Exception as e:
            print("[LOOP ERROR]", e)
        await asyncio.sleep(600)

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    # Avvia Flask in background
    def run_flask():
        app.run(host="0.0.0.0", port=PORT)

    Thread(target=run_flask).start()

    # Avvia scheduler asincrono
    asyncio.run(scheduler())
