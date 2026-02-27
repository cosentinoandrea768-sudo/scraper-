import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from scraper_logic import get_forexfactory_news  # importa la logica aggiornata

# Variabili d'ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("Errore: la variabile d'ambiente BOT_TOKEN non è impostata!")
if not CHAT_ID:
    raise ValueError("Errore: la variabile d'ambiente CHAT_ID non è impostata!")

# --- Comandi del bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Il bot è attivo. Usa /news per ricevere le ultime news Forex di oggi."
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        events = get_forexfactory_news()  # recupera le news dal JS di ForexFactory
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
                message += f"  🔗 Link: {event['url']}\n\n"

        await context.bot.send_message(chat_id=CHAT_ID, text=message)

    except Exception as e:
        await context.bot.send_message(chat_id=CHAT_ID, text=f"Errore nel recupero delle news: {e}")

# --- Avvio del bot ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Aggiunta comandi
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))

    print("Bot avviato sulla porta 10000...")
    # run_polling permette di specificare la porta per test locale
    app.run_polling(port=10000)

if __name__ == "__main__":
    main()
