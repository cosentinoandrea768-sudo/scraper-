import os
import asyncio
from datetime import datetime
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
# INVIO EVENTI
# ==============================
async def send_events(today_only=True):
    events = fetch_forex_factory_events()
    if today_only:
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        events = [e for e in events if e["date"] == today_str]

    if not events:
        print("[INFO] Nessun evento trovato")
        return

    for event in events:
        if event["id"] in sent_events:
            continue

        # Filtra solo medium e high impact
        if event["impact"] not in ["medium", "high"]:
            continue

        label, score = evaluate_impact(event["name"], event.get("actual"), event.get("forecast"))
        message = (
            f"📈 {event['impact'].upper()} IMPACT\n"
            f"{event['currency']} - {event['name']}\n"
            f"🕒 {event['time']}\n"
            f"Previous: {event.get('previous', '-')}\n"
            f"Forecast: {event.get('forecast', '-')}\n"
            f"Actual: {event.get('actual', '-')}\n"
            f"Impact: {label} (Score: {score})"
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
        await bot.send_message(chat_id=CHAT_ID, text="🚀 Bot avviato correttamente - invio eventi di oggi")
    except Exception as e:
        print("[TELEGRAM ERROR] Startup:", e)

    # Primo invio immediato
    await send_events(today_only=True)

    # Loop continuo ogni 5 minuti
    while True:
        try:
            await send_events(today_only=False)
        except Exception as e:
            print("[LOOP ERROR]", e)
        await asyncio.sleep(300)

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    from threading import Thread

    # Avvia Flask in background
    def run_flask():
        app.run(host="0.0.0.0", port=PORT)

    Thread(target=run_flask).start()

    # Avvia scheduler
    asyncio.run(scheduler())
