import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from logic_impact import get_forex_news_today  # funzione aggiornata JS->JSON

# --- Variabili d'ambiente ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("Errore: BOT_TOKEN non impostato!")
if not CHAT_ID:
    raise ValueError("Errore: CHAT_ID non impostato!")

# --- Flask ---
app = Flask(__name__)

# --- Helper per spezzare messaggi troppo lunghi ---
def split_message(msg, max_len=4000):
    """Divide un messaggio lungo in parti più piccole"""
    lines = msg.split("\n")
    chunks = []
    current = ""
    for line in lines:
        if len(current) + len(line) + 1 > max_len:
            chunks.append(current)
            current = line
        else:
            current += "\n" + line if current else line
    if current:
        chunks.append(current)
    return chunks

# --- Comandi Telegram ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Il bot è attivo. Usa /news per ricevere le news Forex.")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = get_forex_news_today()
    for msg in split_message("\n".join(events)):
        await update.message.reply_text(msg)

# --- Application Telegram ---
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("news", news))

# --- Webhook per Render ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.create_task(application.process_update(update))
    return "ok"

# --- Endpoint di controllo ---
@app.route("/")
def index():
    return "Bot attivo!"

# --- Funzione per invio messaggi di test e news settimana prossima ---
async def send_test_messages():
    bot = application.bot
    try:
        # Messaggio di test
        await bot.send_message(chat_id=CHAT_ID, text="✅ Bot attivo! Messaggio di test.")

        # News oggi
        events_today = get_forex_news_today()
        if events_today:
            for msg in split_message("📊 News Forex di oggi:\n" + "\n".join(events_today)):
                await bot.send_message(chat_id=CHAT_ID, text=msg)

        # Per settimana prossima possiamo richiamare la stessa funzione con for_week=True se implementata
        # events_week = get_forex_news_today(for_week=True)
        # if events_week:
        #     for msg in split_message("📊 News Forex settimana prossima:\n" + "\n".join(events_week)):
        #         await bot.send_message(chat_id=CHAT_ID, text=msg)

    except Exception as e:
        print(f"Errore invio messaggi test: {e}")

# --- Avvio Flask + Telegram ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Bot in ascolto su porta {port}")

    # Avvio Flask in thread separato
    from threading import Thread
    Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()

    # Avvio Telegram asincrono per messaggi test
    asyncio.run(send_test_messages())
