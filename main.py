import csv
from datetime import datetime, timedelta, timezone
from telegram import Bot
from telegram.error import TelegramError
import time

# --- CONFIG ---
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
CSV_FILE = "./events.csv"  # Assicurati che sia nella stessa cartella di main.py
TIMEZONE_OFFSET = 1  # esempio: +1 per CET
CHECK_INTERVAL = 60  # in secondi, quanto spesso controllare gli eventi imminenti

bot = Bot(token=BOT_TOKEN)

def send_upcoming_events():
    now = datetime.now(timezone.utc) + timedelta(hours=TIMEZONE_OFFSET)
    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')  # usa tab se il CSV è tab-delimited
        for row in reader:
            event_time = datetime.strptime(row["DateTime"], "%Y-%m-%d %H:%M")
            if 0 <= (event_time - now).total_seconds() <= CHECK_INTERVAL:
                message = (
                    f"Evento imminente:\n"
                    f"{row['Currency']} - {row['Event']}\n"
                    f"Impact: {row['Impact']}\n"
                    f"Actual: {row['Actual']}, Forecast: {row['Forecast']}, Previous: {row['Previous']}"
                )
                try:
                    bot.send_message(chat_id=CHAT_ID, text=message)
                except TelegramError as e:
                    print(f"Errore invio messaggio: {e}")

if __name__ == "__main__":
    print("Bot avviato...")
    while True:
        send_upcoming_events()
        time.sleep(CHECK_INTERVAL)
