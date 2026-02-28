# main.py
import csv
import os
from datetime import datetime, timedelta
from telegram import Bot
from flask import Flask

# --- Config ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TIMEZONE_OFFSET = 1  # esempio: CET = UTC+1
CSV_FILE = "events.csv"

# --- Inizializza bot e Flask ---
bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# --- Funzione per inviare eventi filtrati ---
def send_upcoming_events():
    now = datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)
    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Filtra solo USD o EUR ad alto impatto
            if row["Impact"].lower() == "high" and row["Currency"] in ["USD", "EUR"]:
                event_time = datetime.strptime(row["DateTime"], "%Y-%m-%d %H:%M")
                if event_time >= now:
                    # Crea messaggio verticale
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
                    bot.send_message(chat_id=CHAT_ID, text=message)
                    print(f"Messo in coda: {row['Event']}")

# --- Avvio bot ---
@app.route("/")
def index():
    return "Bot attivo e in ascolto!"

if __name__ == "__main__":
    print("Bot avviato...")
    bot.send_message(chat_id=CHAT_ID, text="🤖 Bot avviato e pronto a inviare eventi HIGH IMPACT su USD ed EUR dal CSV!")
    send_upcoming_events()
    # Flask serve su porta 10000 per mantenere attivo il servizio
    app.run(host="0.0.0.0", port=10000)
