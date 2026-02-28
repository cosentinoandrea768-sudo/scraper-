import csv
from datetime import datetime, timedelta
import telegram
from config import TOKEN, CHAT_ID, CSV_FILE, TIMEZONE_OFFSET

bot = telegram.Bot(token=TOKEN)

def send_upcoming_events():
    now = datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)
    soon = now + timedelta(hours=1)
    messages = []

    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                event_time = datetime.fromisoformat(row["date"])
                if now <= event_time <= soon:
                    messages.append(
                        f"{row['date']} | {row['currency']} | {row['impact']} | {row['event']} | Forecast: {row['forecast']} | Previous: {row['previous']}"
                    )
            except:
                continue

    if messages:
        bot.send_message(chat_id=CHAT_ID, text="\n".join(messages))

if __name__ == "__main__":
    send_upcoming_events()
