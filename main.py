# main.py
import asyncio
import os
from datetime import datetime, timedelta
from telegram import Bot
from scraper import get_calendar_events  # ora corretto

# =========================
# Configurazione
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # ID del canale o gruppo
TIMEZONE_OFFSET = int(os.getenv("TIMEZONE_OFFSET", 1))  # ore rispetto UTC

# =========================
# Funzioni
# =========================
async def send_message(bot: Bot, text: str):
    """Invia un messaggio Telegram."""
    await bot.send_message(chat_id=CHAT_ID, text=text)

async def main():
    """Flusso principale: invio messaggio di avvio + eventi."""
    now = datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)
    start_msg = f"Menu\nData e ora attuale: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Inizializza bot
    async with Bot(BOT_TOKEN) as bot:
        # Messaggio di avvio
        await send_message(bot, start_msg)
        
        # Recupera eventi dal calendario
        events = get_calendar_events()
        if not events:
            await send_message(bot, "[scraper] Nessun evento trovato oggi.")
            return
        
        # Invia i primi eventi (limite a 10 per non spam)
        for ev in events[:10]:
            msg = (
                f"{ev['date']} - {ev['time']}\n"
                f"{ev['name']} ({ev['currency']})\n"
                f"Impatto: {ev['impact']}\n"
                f"Forecast: {ev['forecast']}, Previous: {ev['previous']}, Actual: {ev['actual']}\n"
                f"Link: {ev['url']}"
            )
            await send_message(bot, msg)

# =========================
# Esecuzione
# =========================
if __name__ == "__main__":
    asyncio.run(main())
