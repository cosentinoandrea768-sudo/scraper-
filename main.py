import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from scraper_logic import get_forex_news_today

# Variabili d'ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
PORT = int(os.getenv("PORT", "10000"))  # default Render port

if not BOT_TOKEN:
    raise ValueError("Errore: la variabile d'ambiente BOT_TOKEN non è impostata!")
if not CHAT_ID:
    raise ValueError("Errore: la variabile d'ambiente CHAT_ID non è impostata!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Il bot è attivo. Usa /news per ricevere le ultime news Forex."
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = get_forex_news_today()
    for msg in messages:
        await context.bot.send_message(chat_id=CHAT_ID, text=msg)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Aggiunta comandi
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))

    print(f"Bot avviato... porta: {PORT}")
    # Render o ambiente simile richiede run_polling con port
    app.run_polling(poll_interval=5)

if __name__ == "__main__":
    main()
