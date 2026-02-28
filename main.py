import csv
from datetime import datetime, timedelta
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler

CSV_FILE = "events.csv"
CHAT_ID = "IL_TUO_CHAT_ID"
TOKEN = "IL_TUO_BOT_TOKEN"
TIMEZONE_OFFSET = 1  # adatta se vuoi UTC+1

bot = Bot(token=TOKEN)

def send_all_events():
    """Invia tutte le righe del CSV su Telegram."""
    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            message = (
                f"📅 {row['DateTime']}\n"
                f"💱 {row['Currency']}\n"
                f"⚡ Impact: {row['Impact']}\n"
                f"📰 Event: {row['Event']}\n"
                f"🔹 Actual: {row['Actual']}\n"
                f"🔹 Forecast: {row['Forecast']}\n"
                f"🔹 Previous: {row['Previous']}\n"
                f"🔗 Details: {row['Detail']}"
            )
            bot.send_message(chat_id=CHAT_ID, text=message)

def send_upcoming_events():
    """Invia solo eventi imminenti (schedulazione normale)."""
    now = datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)
    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            event_time = datetime.strptime(row["DateTime"], "%Y-%m-%d %H:%M:%S")
            if 0 <= (event_time - now).total_seconds() <= 3600:  # prossima ora
                message = (
                    f"📅 {row['DateTime']}\n"
                    f"💱 {row['Currency']}\n"
                    f"⚡ Impact: {row['Impact']}\n"
                    f"📰 Event: {row['Event']}\n"
                    f"🔹 Actual: {row['Actual']}\n"
                    f"🔹 Forecast: {row['Forecast']}\n"
                    f"🔹 Previous: {row['Previous']}\n"
                    f"🔗 Details: {row['Detail']}"
                )
                bot.send_message(chat_id=CHAT_ID, text=message)

# Messaggio di avvio
bot.send_message(chat_id=CHAT_ID, text="🤖 Bot avviato! Inizio test invio eventi...")

# Invia tutte le news subito
send_all_events()

# Scheduler per eventi futuri
scheduler = BackgroundScheduler()
scheduler.add_job(send_upcoming_events, "interval", minutes=10)
scheduler.start()

print("Bot avviato e scheduler attivo!")
