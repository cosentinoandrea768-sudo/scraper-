import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from scraper_logic import get_forexfactory_news

# Variabili d'ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("Errore: BOT_TOKEN non impostato!")
if not CHAT_ID:
    raise ValueError("Errore: CHAT_ID non impostato!")

app = Flask(__name__)

# --- Funzioni Telegram ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Il bot è attivo. Usa /news per ricevere le news Forex di oggi.")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    await update.message.reply_text(msg)

# --- Applicazione Telegram ---
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("news", news))

# --- Webhook endpoint per Render ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.create_task(application.process_update(update))
    return "ok"

# Endpoint per controllo
@app.route("/")
def index():
    return "Bot attivo!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Bot in ascolto su porta {port}")
    app.run(host="0.0.0.0", port=port)
