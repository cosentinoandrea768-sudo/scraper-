import os
import asyncio
from threading import Thread
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from scraper_logic import get_forex_news  # funzione JS->JSON

# ----------------------
# Variabili d'ambiente
# ----------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("Errore: BOT_TOKEN non impostato!")
if not CHAT_ID:
    raise ValueError("Errore: CHAT_ID non impostato!")

# ----------------------
# Flask app
# ----------------------
app = Flask(__name__)

# ----------------------
# Funzioni Telegram
# ----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Il bot è attivo.\nUsa /news per ricevere le news Forex di oggi."
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = get_forex_news(for_week=False)
    if not events:
        await update.message.reply_text("Nessun evento trovato oggi.")
        return

    await send_messages_chunked(events, CHAT_ID)

# Funzione per spezzare e inviare messaggi lunghi
async def send_messages_chunked(events, chat_id, max_len=4000):
    msg = "📊 News Forex:\n"
    for e in events:
        line = f"- {e['prefixedName']} ({e['timeLabel']})\n"
        if e['forecast']:
            line += f"  📈 Previsione: {e['forecast']}\n"
        if e['actual']:
            line += f"  📊 Attuale: {e['actual']}\n"
        line += f"  🔗 {e['url']}\n"
        if len(msg) + len(line) > max_len:
            await application.bot.send_message(chat_id=chat_id, text=msg)
            msg = ""
        msg += line
    if msg:
        await application.bot.send_message(chat_id=chat_id, text=msg)

# ----------------------
# Application Telegram
# ----------------------
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("news", news))

# ----------------------
# Webhook per Render
# ----------------------
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.create_task(application.process_update(update))
    return "ok"

# Endpoint di controllo
@app.route("/")
def index():
    return "Bot attivo!"

# ----------------------
# Messaggi di test all'avvio
# ----------------------
async def send_test_messages():
    try:
        bot = application.bot
        # Messaggio test
        await bot.send_message(chat_id=CHAT_ID, text="✅ Bot attivo! Messaggio di test.")
        # News settimana prossima
        events_next_week = get_forex_news(for_week=True, week_offset=1)
        if events_next_week:
            await send_messages_chunked(events_next_week, CHAT_ID)
    except Exception as e:
        print(f"Errore invio messaggi test: {e}")

# ----------------------
# Avvio Flask + Telegram
# ----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Bot in ascolto su porta {port}")

    # Avvio Flask in thread separato
    Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()

    # Avvio Telegram asincrono per invio messaggi test
    asyncio.run(send_test_messages())
