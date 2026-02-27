import os
import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot
from logic_impact import evaluate_impact

# ==============================
# ENV VARS
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN o CHAT_ID non impostati")

bot = Bot(token=BOT_TOKEN)
sent_events = set()

# ==============================
# FLASK
# ==============================
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot scraping Forex Factory attivo ✅"

# ==============================
# SCRAPING FUNZION
# ==============================
FF_CALENDAR_URL = "https://www.forexfactory.com/calendar.php?week=this"

def fetch_high_impact_events():
    """
    Ritorna una lista di eventi high impact (3 stelle)
    con struttura:
    {id, currency, name, time, previous, forecast, actual}
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(FF_CALENDAR_URL, headers=headers)
    soup = BeautifulSoup(r.content, "html.parser")

    events = []
    rows = soup.select("tr.calendar__row")
    for row in rows:
        stars = row.select(".impact span.full")
        if len(stars) != 3:
            continue  # solo high impact

        currency_tag = row.select_one(".calendar__currency")
        name_tag = row.select_one(".calendar__event")
        time_tag = row.select_one(".calendar__time")
        prev_tag = row.select_one(".calendar__previous")
        forecast_tag = row.select_one(".calendar__forecast")
        actual_tag = row.select_one(".calendar__actual")

        if not currency_tag or not name_tag or not time_tag:
            continue

        event_id = row.get("id") or f"{currency_tag.text.strip()}_{name_tag.text.strip()}_{time_tag.text.strip()}"
        events.append({
            "id": event_id,
            "currency": currency_tag.text.strip(),
            "name": name_tag.text.strip(),
            "time": time_tag.text.strip(),
            "previous": prev_tag.text.strip() if prev_tag else "-",
            "forecast": forecast_tag.text.strip() if forecast_tag else "-",
            "actual": actual_tag.text.strip() if actual_tag else "-"
        })

    return events

# ==============================
# TELEGRAM
# ==============================
async def send_events():
    events = fetch_high_impact_events()
    for event in events:
        if event["id"] in sent_events:
            continue

        impact_label, impact_score = evaluate_impact(event["name"], event["actual"], event["forecast"])
        message = (
            f"📊 {event['currency']} – {event['name']}\n"
            f"🕒 {event['time']}\n"
            f"Previous: {event['previous']}\n"
            f"Forecast: {event['forecast']}\n"
            f"Actual: {event['actual']}\n"
            f"Impact: {impact_label}"
        )
        try:
            await bot.send_message(chat_id=CHAT_ID, text=message)
            sent_events.add(event["id"])
            print(f"[SENT] {event['name']}")
        except Exception as e:
            print("[TELEGRAM ERROR]", e)

# ==============================
# SCHEDULER
# ==============================
async def scheduler():
    # Messaggio di avvio
    try:
        await bot.send_message(chat_id=CHAT_ID, text="🚀 Bot Forex Factory avviato")
        print("[DEBUG] Messaggio di startup inviato")
    except Exception as e:
        print("[TELEGRAM ERROR] Startup:", e)

    while True:
        try:
            await send_events()
        except Exception as e:
            print("[LOOP ERROR]", e)
        await asyncio.sleep(300)  # ogni 5 minuti

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    from threading import Thread

    # Flask in background
    def run_flask():
        app.run(host="0.0.0.0", port=PORT)
    Thread(target=run_flask).start()

    # Scheduler asyncio
    asyncio.run(scheduler())
