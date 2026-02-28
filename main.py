import os
import csv
from datetime import datetime, timedelta
from telegram import Bot
from telegram.error import TelegramError

# --- CONFIGURAZIONE ---
BOT_TOKEN = os.environ.get("BOT :TOKEN")  # attenzione allo spazio!
CHAT_ID = os.environ.get("CHAT_ID")
TIMEZONE_OFFSET = 0  # se vuoi aggiustare l'orario
CSV_FILE = "events.csv"  # deve essere nella stessa cartella
PORT = int(os.environ.get("PORT", 10000))  # fallback a 10000

bot = Bot(token=BOT_TOKEN)

def send_upcoming_events():
    """Legge events.csv e manda messaggi per ogni evento futuro."""
    now = datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)
    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Controllo DateTime
                try:
                    event_time = datetime.strptime(row["DateTime"], "%Y-%m-%d %H:%M")
                except KeyError:
                    print("Errore: la colonna 'DateTime' non esiste nel CSV.")
                    return
                except ValueError:
                    print(f"Formato DateTime non valido: {row['DateTime']}")
                    continue

                # Manda solo eventi futuri
                if event_time >= now:
                    message = (
                        f"📅 Evento imminente:\n"
                        f"⏰ {row['DateTime']}\n"
                        f"💱 {row['Currency']} - {row['Impact']}\n"
                        f"📝 {row['Event']}\n"
                        f"📊 Forecast: {row['Forecast']}\n"
                        f"🔹 Previous: {row['Previous']}\n"
                        f"🖋 Dettagli: {row['Detail']}"
                    )
                    try:
                        bot.send_message(chat_id=CHAT_ID, text=message)
                        print(f"Messo in coda: {row['Event']}")
                    except TelegramError as e:
                        print(f"Errore Telegram: {e}")
    except FileNotFoundError:
        print(f"Errore: {CSV_FILE} non trovato!")

if __name__ == "__main__":
    print("Bot avviato...")

    # --- TEST MESSAGGIO DI AVVIO ---
    try:
        bot.send_message(chat_id=CHAT_ID, text="🤖 Bot avviato e pronto a inviare eventi dal CSV!")
    except TelegramError as e:
        print(f"Errore invio messaggio di avvio: {e}")

    # --- INVIO EVENTI DAL CSV ---
    send_upcoming_events()

    # --- Se vuoi aggiungere webhook su Render ---
    # Render mostra avviso se non c'è server web, quindi possiamo aprire una porta dummy
    from flask import Flask
    app = Flask(__name__)

    @app.route("/")
    def index():
        return "Bot attivo!", 200

    app.run(host="0.0.0.0", port=PORT)
