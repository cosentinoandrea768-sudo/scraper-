import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from logic_impact import get_forex_news_today  # funzione coerente per oggi o settimana prossima

# --- Config Telegram ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("Errore: BOT_TOKEN o CHAT_ID non impostati!")

app = Flask(__name__)
application = ApplicationBuilder().token(BOT_TOKEN).build()

# --- Helper per spezzare messaggi lunghi ---
def split_message(msg, chunk_size=4000):
    return [msg[i:i+chunk_size] for i in range(0, len(msg), chunk_size)]

# --- Comandi Telegram ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Bot attivo. Usa /news per ricevere le news Forex.")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = get_forex_news_today(for_week=False)
    if isinstance(events, list) and isinstance(events[0], dict):
        msg = "📊 News Forex di oggi:\n"
        for e in events:
            msg += f"- {e['prefixedName']} ({e['timeLabel']})\n"
            if e['forecast']:
                msg += f"  📈 Previsione: {e['forecast']}\n"
            if e['actual']:
                msg += f"  📊 Attuale: {e['actual']}\n"
            msg += f"  🔗 {e['url']}\n"
    else:
        msg = "\n".join(events)

    for chunk in split_message(msg):
        await update.message.reply_text(chunk)

# --- Handler ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("news", news))

# --- Webhook per Render ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.create_task(application.process_update(update))
    return "ok"

# --- Endpoint principale ---
@app.route("/")
def index():
    return "Bot attivo!"

# --- Endpoint per test di invio messaggi ---
@app.route("/test")
def test_messages():
    asyncio.create_task(send_test_messages())
    return "Messaggi di test inviati!"

# --- Funzione async per inviare messaggi di test ---
async def send_test_messages():
    bot = application.bot
    try:
        # Messaggio di attivazione
        await bot.send_message(chat_id=CHAT_ID, text="✅ Bot attivo! Messaggio di test.")

        # News settimana prossima
        events = get_forex_news_today(for_week=True)
        if isinstance(events, list) and isinstance(events[0], dict):
            msg = "📊 Test: News Forex settimana prossima:\n"
            for e in events:
                msg += f"- {e['prefixedName']} ({e['timeLabel']})\n"
                if e['forecast']:
                    msg += f"  📈 Previsione: {e['forecast']}\n"
                if e['actual']:
                    msg += f"  📊 Attuale: {e['actual']}\n"
                msg += f"  🔗 {e['url']}\n"
        else:
            msg = "\n".join(events)

        for chunk in split_message(msg):
            await bot.send_message(chat_id=CHAT_ID, text=chunk)
    except Exception as e:
        print(f"Errore invio messaggi test: {e}")

# --- Avvio Flask ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
