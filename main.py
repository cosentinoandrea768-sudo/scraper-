import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from scraper_logic import get_forex_news_today
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
PORT = int(os.getenv("PORT", 10000))  # Porta Render

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("Imposta BOT_TOKEN e CHAT_ID nelle variabili d'ambiente!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Il bot è attivo. Usa /news per ricevere le ultime news Forex."
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = get_forex_news_today()
    for msg in messages:
        await context.bot.send_message(chat_id=CHAT_ID, text=msg)

async def handle(request):
    """Gestisce le richieste POST del webhook."""
    body = await request.text()
    update = Update.de_json(json.loads(body), app.bot)
    await app.update_queue.put(update)
    return web.Response(text="OK")

# --- Main ---
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("news", news))

# Configura webhook (su Render devi impostare URL tipo https://<tuo-servizio>.onrender.com)
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # es. https://mio-bot.onrender.com
if not WEBHOOK_URL:
    raise ValueError("Imposta la variabile WEBHOOK_URL su Render!")

async def main():
    await app.bot.set_webhook(WEBHOOK_URL)
    print(f"Webhook impostato su {WEBHOOK_URL}")
    # Server aiohttp su Render
    web_app = web.Application()
    web_app.router.add_post("/", handle)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    print(f"Bot pronto sulla porta {PORT}")
    await site.start()

import asyncio
asyncio.run(main())
