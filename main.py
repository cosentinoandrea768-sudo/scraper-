import asyncio
from telegram import Bot
from scraper import get_calendar_events

# --- Config ---
BOT_TOKEN = "BOT_TOKEN"
CHAT_ID = "CHAT_ID"
MIN_IMPACT = "medium"  # Filtra solo eventi medium o high

# --- Funzione principale ---
async def main():
    async with Bot(BOT_TOKEN) as bot:
        # Messaggio di avvio
        await bot.send_message(chat_id=CHAT_ID, text="✅ Bot avviato!")

        # Scraping eventi
        events = get_calendar_events(min_impact=MIN_IMPACT)
        print(f"[scraper] Trovati {len(events)} eventi con impatto {MIN_IMPACT}")

        # Invio messaggi Telegram
        for ev in events:
            msg = (
                f"📅 {ev['date']} {ev['time']} | {ev['currency']} | Impatto: {ev['impact']}\n"
                f"📰 {ev['title']}\n"
                f"📊 Forecast: {ev['forecast']} | Previous: {ev['previous']} | Actual: {ev['actual']}\n"
                f"🔗 {ev['url']}"
            )
            await bot.send_message(chat_id=CHAT_ID, text=msg)

# --- Entry point ---
if __name__ == "__main__":
    asyncio.run(main())
