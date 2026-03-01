import os
import requests
from flask import Flask
from datetime import datetime

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

ALLOWED_CURRENCIES = ["USD", "EUR"]


def fetch_news():
    try:
        response = requests.get(CALENDAR_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Errore fetch news: {e}")
        return []


def filter_news(news):
    filtered = []

    for event in news:
        currency = event.get("currency")
        impact = event.get("impact")

        if currency in ALLOWED_CURRENCIES and impact in ["High", "Medium"]:
            filtered.append(event)

    return filtered


def format_news(news):
    if not news:
        return "📭 Nessuna news rilevante USD/EUR questa settimana."

    message = "📅 *News Economiche della Settimana*\n\n"

    for event in news:
        date = event.get("date", "")
        time = event.get("time", "")
        currency = event.get("currency", "")
        title = event.get("title", "")
        impact = event.get("impact", "")

        message += (
            f"🗓 {date} {time}\n"
            f"💱 {currency}\n"
            f"📰 {title}\n"
            f"⚠️ Impatto: {impact}\n\n"
        )

    return message


def send_to_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Variabili Telegram mancanti.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Errore invio Telegram: {e}")


def process_news():
    news = fetch_news()
    filtered = filter_news(news)
    message = format_news(filtered)
    send_to_telegram(message)


@app.route("/")
def home():
    return "Bot attivo ✅"


@app.route("/send-news")
def send_news():
    process_news()
    return "News inviate su Telegram ✅"


if __name__ == "__main__":
    # Invio automatico all'avvio
    process_news()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
