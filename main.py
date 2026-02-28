import csv
from datetime import datetime, timedelta
import os
from telegram import Bot
from flask import Flask

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")   # variabile ambiente
CHAT_ID = os.getenv("CHAT_ID")       # variabile ambiente
TIMEZONE_OFFSET = 1                  # ore di offset rispetto UTC
CSV_FILE = "events.csv"              # nome del CSV
# ========================================

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

def send_upcoming_events():
    now = datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)
    
    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # FILTRO: High Impact solo per USD o EUR
            if row["Impact"] != "High" or row["Currency"] not in ["USD", "EUR"]:
                continue
            
            event_time = datetime.strptime(row["DateTime"], "%Y-%m-%d %H:%M")
            # Ignora eventi passati
            if event_time < now:
                continue

            message = (
                f"📅 {row['DateTime']} | {row['Currency']} | {row['Impact']} | {row['Event']}\n"
                f"Detail: {row['Detail']}\n"
                f"Actual: {row['Actual']} | Forecast: {row['Forecast']} | Previous: {row['Previous']}"
            )
            bot.send_message(chat_id=CHAT_ID, text=message)
            print(f"Messo in coda: {row['Event']}")

if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="🤖 Bot avviato e pronto a inviare eventi HIGH IMPACT USD/EUR dal CSV!")
    print("Bot avviato...")

    send_upcoming_events()

    # Flask app per mantenere il processo live su Render
    @app.route("/")
    def index():
        return "Bot Telegram attivo! 🚀"

    app.run(host="0.0.0.0", port=10000)
