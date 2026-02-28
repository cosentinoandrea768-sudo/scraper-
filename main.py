import os
import threading
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from logic_impact import get_forex_news_today  # funzione JS->JSON

# --- Variabili d'ambiente ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("Errore: BOT_TOKEN o CHAT_ID non impostato!")

# --- Flask ---
app = Flask(__name__)

# --- Comandi Telegram ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Bot attivo!")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = get_forex_news_today()
    for msg in messages:
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

# Endpoint di controllo
@app.route("/")
def index():
    return "Bot attivo!"

# --- Funzione invio messaggi test ---
async def send_test_messages():
    try:
        bot = application.bot
        # Messaggio di test
        await bot.send_message(chat_id=CHAT_ID, text="✅ Bot attivo! Messaggio di test.")
        # News del giorno
        messages = get_forex_news_today()
        for msg in messages:
            await bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        print(f"Errore invio messaggi test: {e}")

# --- Avvio Flask + messaggi test ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Bot in ascolto su porta {port}")
    
    # Flask su thread separato
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()
    # Invio messaggi test
    asyncio.run(send_test_messages())
