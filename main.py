import csv
import asyncio
from datetime import datetime, timedelta
from telegram import Bot
from config import BOT_TOKEN, CHAT_ID, TIMEZONE_OFFSET, CSV_FILE
from scraper import scrape_and_update_csv  # Assumendo che scraper.py abbia questa funzione

bot = Bot(token=BOT_TOKEN)

async def send_upcoming_events():
    now = datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)

    # Calcola il lunedì della prossima settimana e il lunedì successivo
    start_next_week = now + timedelta(days=(7 - now.weekday()))
    end_next_week = start_next_week + timedelta(days=7)

    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Salta righe vuote o senza DateTime
            if not row["DateTime"].strip():
                continue

            currency = row["Currency"].strip()
            impact = row["Impact"].strip().lower()

            # Filtra solo HIGH Impact USD/EUR
            if impact == "high" and currency in ["USD", "EUR"]:
                try:
                    event_time = datetime.strptime(row["DateTime"].strip(), "%Y-%m-%d %H:%M")
                except ValueError:
                    print(f"Formato DateTime non valido: {row['DateTime']}")
                    continue

                if start_next_week <= event_time < end_next_week:
                    # Messaggio Telegram più leggibile e diviso per linee
                    message = (
                        f"📅 DateTime: {row['DateTime'].strip()}\n"
                        f"Event: {row['Event'].strip()}\n"
                        f"Currency: {currency}\n"
                        f"Impact: {row['Impact'].strip()}\n"
                        f"Detail: {row['Detail'].strip()}\n"
                        f"Actual: {row['Actual'].strip()}\n"
                        f"Forecast: {row['Forecast'].strip()}\n"
                        f"Previous: {row['Previous'].strip()}"
                    )
                    await bot.send_message(chat_id=CHAT_ID, text=message)
                    print(f"Messo in coda: {row['Event'].strip()}")

async def main():
    # 1️⃣ Scraping e aggiornamento CSV
    print("🔍 Avvio scraping e aggiornamento CSV...")
    scrape_and_update_csv(CSV_FILE)
    print("✅ CSV aggiornato!")

    # 2️⃣ Messaggio di avvio Telegram
    await bot.send_message(chat_id=CHAT_ID,
                           text="🤖 Bot avviato e pronto a inviare eventi HIGH IMPACT USD/EUR della prossima settimana!")

    # 3️⃣ Invio eventi filtrati
    await send_upcoming_events()

if __name__ == "__main__":
    asyncio.run(main())
