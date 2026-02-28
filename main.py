import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio

from scraper_logic import get_forexfactory_news  # funzione JS -> JSON

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
    await update.message.reply_text(
        "Ciao! Il bot è attivo. Usa /news per ricevere le news Forex di oggi."
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = get_forexfactory_news(week="this")
    if not events:
        msg = "Nessun evento trovato oggi."
        await update.message.reply_text(msg)
        return

    msg = "📊 News Forex di oggi:\n"
    for e in events:
        msg += f"- {e['prefixedName']} ({e['timeLabel']})\n"
        if e['forecast']:
            msg += f"  📈 Previsione: {e['forecast']}\n"
        if e['actual']:
            msg += f"  📊 Attuale: {e['actual']}\n"
        msg += f"  🔗 {e['url']}\n"

        # Telegram limite 4096 caratteri
        if len(msg) > 4000:
            await update.message.reply_text(msg)
            msg = ""
    if msg:
        await update.message.reply_text(msg)

# --- Applicazione Telegram ---
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("news", news))

# --- Webhook endpoint per Render ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.ensure_future(application.process_update(update))
    return "ok"

# Endpoint di controllo
@app.route("/")
def index():
    return "Bot attivo!"

# --- Funzione per test di invio diretto ---
async def send_test_messages():
    try:
        bot = application.bot
        # Messaggio di test
        await bot.send_message(chat_id=CHAT_ID, text="✅ Bot attivo! Messaggio di test.")

        # Prova: news settimana prossima
        events = get_forexfactory_news(week="next")
        if events:
            msg = "📊 Prova: News Forex settimana prossima:\n"
            for e in events:
                msg += f"- {e['prefixedName']} ({e['timeLabel']})\n"
                if e['forecast']:
                    msg += f"  📈 Previsione: {e['forecast']}\n"
                if e['actual']:
                    msg += f"  📊 Attuale: {e['actual']}\n"
                msg += f"  🔗 {e['url']}\n"

                if len(msg) > 4000:
                    await bot.send_message(chat_id=CHAT_ID, text=msg)
                    msg = ""
            if msg:
                await bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        print(f"Errore invio messaggi test: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Bot in ascolto su porta {port}")
    
    # Avvio Flask in thread
    from threading import Thread
    Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()
    
    # Avvio invio test messaggi
    asyncio.run(send_test_messages())
