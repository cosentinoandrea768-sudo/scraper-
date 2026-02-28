from apscheduler.schedulers.background import BackgroundScheduler
from scraper import scrape_forex_factory
from telegram_bot import send_message
from config import IMPACT_FILTER, CURRENCY_FILTER
import hashlib

sent_events = set()

def event_hash(event):
    return hashlib.md5(f"{event['time']}{event['currency']}{event['event']}".encode()).hexdigest()

def check_events():
    df = scrape_forex_factory()

    for _, row in df.iterrows():
        if IMPACT_FILTER and not any(f in row["impact"] for f in IMPACT_FILTER):
            continue

        if CURRENCY_FILTER and row["currency"] not in CURRENCY_FILTER:
            continue

        h = event_hash(row)

        if h not in sent_events:
            message = (
                f"📅 Evento Forex\n"
                f"⏰ {row['time']}\n"
                f"💱 {row['currency']}\n"
                f"🔥 {row['impact']}\n"
                f"📌 {row['event']}"
            )
            send_message(message)
            sent_events.add(h)


def start_scheduler(interval_minutes):
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_events, "interval", minutes=interval_minutes)
    scheduler.start()
