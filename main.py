import csv
import asyncio
from datetime import datetime, timedelta
from telegram import Bot
import os
from scraper import scrape_and_update_csv  # aggiorna il csv prima

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
CSV_FILE = "events.csv"
TIMEZONE_OFFSET = 1

async def send_upcoming_events(bot: Bot):
    now = datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)
    start_next_week = now + timedelta(days=(7 - now.weekday()))
    end_next_week = start_next_week + timedelta(days=7)

    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Impact"].lower() == "high" and row["Currency"] in ["USD", "EUR"]:
                event_time = datetime.strptime(row["DateTime"], "%Y-%m-%d %H:%M")
                if start_next_week <= event_time < end_next_week:
                    message = (
                        f"📅 DateTime: {row['DateTime']}\n"
                        f"Event: {row['Event']}\n"
                        f"Currency: {row['Currency']}\n"
                        f"Impact: {row['Impact']}\n"
                        f"Detail: {row['Detail']}\n"
                        f"Actual: {row['Actual']}\n"
                        f"Forecast: {row['Forecast']}\n"
                        f"Previous: {row['Previous']}"
                    )
                    await bot.send_message(chat_id=CHAT_ID, text=message)
                    print(f"Messo in coda: {row['Event']}")

async def main():
    scrape_and_update_csv()  # aggiorna CSV prima di leggere
    async with Bot(BOT_TOKEN) as bot:
        await bot.send_message(
            chat_id=CHAT_ID,
            text="🤖 Bot avviato e pronto a inviare eventi HIGH IMPACT USD/EUR della prossima settimana!"
        )
        await send_upcoming_events(bot)

if __name__ == "__main__":
    asyncio.run(main())
