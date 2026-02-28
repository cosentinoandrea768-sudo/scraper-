import csv
from datetime import datetime, timedelta
from telegram import Bot
from config import BOT_TOKEN, CHAT_ID, TIMEZONE_OFFSET, CSV_FILE

# Inizializza il bot Telegram
bot = Bot(token=BOT_TOKEN)
print("Bot avviato...")

def send_upcoming_events():
    now = datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)
    upcoming_events = []

    # Legge il CSV
    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    event_time = datetime.strptime(row["DateTime"], "%Y-%m-%d %H:%M")
                except ValueError:
                    print(f"Formato data non valido: {row['DateTime']}")
                    continue

                if event_time >= now:
                    upcoming_events.append(row)

    except FileNotFoundError:
        print(f"File CSV non trovato: {CSV_FILE}")
        return

    # Invia i messaggi per ogni evento futuro
    for event in upcoming_events:
        message = (
            f"📌 Evento: {event['Event']}\n"
            f"🕒 Data/Ora: {event['DateTime']}\n"
            f"💰 Valuta: {event['Currency']}\n"
            f"⚡ Impatto: {event['Impact']}\n"
            f"📊 Forecast: {event['Forecast']}\n"
            f"🔙 Previous: {event['Previous']}\n"
            f"📝 Dettagli: {event['Detail']}"
        )
        bot.send_message(chat_id=CHAT_ID, text=message)
        print(f"Inviato evento: {event['Event']}")

# Avvio invio eventi
send_upcoming_events()
