import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Variabili d'ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
PORT = int(os.getenv("PORT", 10000))  # Porta per Render (default 10000)

if not BOT_TOKEN:
    raise ValueError("Errore: la variabile d'ambiente BOT_TOKEN non è impostata!")
if not CHAT_ID:
    raise ValueError("Errore: la variabile d'ambiente CHAT_ID non è impostata!")

# URL del JSON con gli eventi ForexFactory
FOREX_JSON_URL = "https://www.forexfactory.com/calendar-feed?week=this"

# --- Server HTTP dummy per Render ---
def start_dummy_server():
    server = HTTPServer(("0.0.0.0", PORT), SimpleHTTPRequestHandler)
    print(f"Server HTTP dummy in ascolto sulla porta {PORT}")
    server.serve_forever()

threading.Thread(target=start_dummy_server, daemon=True).start()

# --- Bot Telegram ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Il bot è attivo. Usa /news per ricevere le ultime news Forex."
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(FOREX_JSON_URL)
        response.raise_for_status()
        data = response.json()

        # Estrarre le news del primo giorno nel feed
        events = data['days'][0]['events']
        if not events:
            message = "Nessun evento trovato oggi."
        else:
            message = "📊 News Forex di oggi:\n"
            for event in events:
                message += f"- {event['prefixedName']} ({event['timeLabel']})\n"
                if event.get("forecast"):
                    message += f"  📈 Previsione: {event['forecast']}\n"
                if event.get("actual"):
                    message += f"  📊 Attuale: {event['actual']}\n"

        await context.bot.send_message(chat_id=CHAT_ID, text=message)

    except Exception as e:
        await context.bot.send_message(chat_id=CHAT_ID, text=f"Errore nel recupero delle news: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Comandi
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))

    print("Bot Telegram avviato...")
    app.run_polling()

if __name__ == "__main__":
    main()
