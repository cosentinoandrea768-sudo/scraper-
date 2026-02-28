# main.py

import os
import csv
import asyncio
from datetime import datetime, timedelta
from flask import Flask

from telegram import Bot

# -------------------------
# CONFIG
# -------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TIMEZONE_OFFSET = int(os.getenv("TIMEZONE_OFFSET", 0))  # default 0
CSV_FILE = "events.csv"

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("Le env var BOT_TOKEN e CHAT_ID devono essere settate!")

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# -------------------------
# FUNZIONI TELEGRAM
# -------------------------
async def send_start_message():
    """Invia messaggio di avvio del bot"""
    await bot.send_message(
        chat_id=CHAT_ID,
        text="🤖 Bot avviato e pronto a inviare eventi dal CSV!"
    )
    print("Bot avviato e messaggio di start inviato")

async def send_upcoming_events():
    """Legge il CSV e invia messaggi per eventi futuri"""
    now = datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)

    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                event_time = datetime.strptime(row["DateTime"], "%Y-%m-%d %H:%M")
                if event_time >= now:
                    message = (
                        f"📅 {row['DateTime']} | {row['Currency']} | {row['Impact']} | {row['Event']}\n"
                        f"Detail: {row['Detail']}\n"
                        f"Actual: {row['Actual']} | Forecast: {row['Forecast']} | Previous: {row['Previous']}"
                    )
                    await bot.send_message(chat_id=CHAT_ID, text=message)
                    print(f"Messo in coda: {row['Event']}")
    except FileNotFoundError:
        print(f"Errore: il file CSV '{CSV_FILE}' non esiste nella cartella corrente")
    except KeyError as e:
        print(f"Errore: la colonna '{e.args[0]}' non esiste nel CSV")

# -------------------------
# FLASK PER KEEP-ALIVE
# -------------------------
@app.route("/")
def index():
    return "Bot Telegram operativo!"

# -------------------------
# MAIN
# -------------------------
async def main():
    await send_start_message()
    await send_upcoming_events()

if __name__ == "__main__":
    # Avvia async main
    asyncio.run(main())

    # Avvia Flask su porta 10000
    app.run(host="0.0.0.0", port=10000)
