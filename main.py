import os
import asyncio
from telegram import Bot
from scraper import get_calendar_events

# --- Environment Variables ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

MIN_IMPACT = "medium"

async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Errore: BOT_TOKEN o CHAT_ID non impostati nelle environment variables.")
        return

    async with Bot(BOT_TOKEN) as bot:
        try:
            # Messaggio di avvio
            await bot.send_message(
                chat_id=CHAT_ID,
                text="✅ Bot avviato correttamente!"
            )

            # Scraping eventi
            events = get_calendar_events(min_impact=MIN_IMPACT)
            print(f"[scraper] Trovati {len(events)} eventi")

            if not events:
                print("[scraper] Nessun evento trovato.")
                return

            # Invio eventi
            for ev in events:
                msg = (
                    f"📅 {ev['date']} {ev['time']} | {ev['currency']} | Impatto: {ev['impact']}\n"
                    f"📰 {ev['title']}\n"
                    f"📊 Forecast: {ev['forecast']} | Previous: {ev['previous']} | Actual: {ev['actual']}\n"
                    f"🔗 {ev['url']}"
                )

                await bot.send_message(chat_id=CHAT_ID, text=msg)

        except Exception as e:
            print("Errore nel bot:", e)

if __name__ == "__main__":
    asyncio.run(main())
