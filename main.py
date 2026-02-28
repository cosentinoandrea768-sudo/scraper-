import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler

from scraper_logic import get_forexfactory_news

# Variabili d'ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("Errore: BOT_TOKEN non impostato!")
if not CHAT_ID:
    raise ValueError("Errore: CHAT_ID non impostato!")

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# Dispatcher per webhook
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# --- Comandi Telegram ---
def start(update, context):
    update.message.reply_text("Ciao! Il bot è attivo. Usa /news per ricevere le news Forex di oggi.")

def news(update, context):
    events = get_forexfactory_news()
    if not events:
        msg = "Nessun evento trovato oggi."
    else:
        msg = "📊 News Forex di oggi:\n"
        for e in events:
            msg += f"- {e['prefixedName']} ({e['timeLabel']})\n"
            if e['forecast']:
                msg += f"  📈 Previsione: {e['forecast']}\n"
            if e['actual']:
                msg += f"  📊 Attuale: {e['actual']}\n"
            msg += f"  🔗 {e['url']}\n"

    update.message.reply_text(msg)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("news", news))

# --- Webhook endpoint per Render ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Endpoint per controlli
@app.route("/")
def index():
    return "Bot attivo!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Bot in ascolto su porta {port}")
    app.run(host="0.0.0.0", port=port)
