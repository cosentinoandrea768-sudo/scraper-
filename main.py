import csv
import os
import asyncio
from datetime import datetime, timedelta
from telegram import Bot
from flask import Flask

# --- Config ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TIMEZONE_OFFSET = 1
CSV_FILE = "events.csv"

# --- Inizializza bot e Flask ---
bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# --- Funzione async per inviare eventi ---
async def send_upcoming_events():
    now = datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)
    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Impact"].lower() == "high" and row["Currency"] in ["USD", "EUR"]:
                event_time = datetime.strptime(row["DateTime"], "%Y-%m-%d %H:%M")
                if event_time >= now:
                    message = (
                        f"📅 DateTime: {row['DateTime']}\n"
                        f"Event: {row['Event']}\n"
                        f"Currency: {row['Currency']}\n"
                        f"Impact: {row['Impact']}\n"
                        f"Detail: {row['Detail']}\n"
                        f"Actual: {row['Actual']}\n"
                        f"Forecast: {row['Forecast']}\n"
                        f"Previous: {row['Previous']}"
                    )
                    await bot.send_message(chat_id=CHAT_ID, text=message)
                    print(f"Messo in coda: {row['Event']}")

# --- Avvio bot ---
@app.route("/")
def index():
    return "Bot attivo e in ascolto!"

if __name__ == "__main__":
    async def main():
        print("Bot avviato...")
        await bot.send_message(chat_id=CHAT_ID, text="🤖 Bot avviato e pronto a inviare eventi HIGH IMPACT USD/EUR dal CSV!")
        await send_upcoming_events()
        # Flask serve su porta 10000
        app.run(host="0.0.0.0", port=10000)

    asyncio.run(main())
