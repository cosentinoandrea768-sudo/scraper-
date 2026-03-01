def process_news(initial=False):
    news = fetch_news()

    if not news:
        logging.info("Nessuna news trovata")
        return

    filtered_news = []

    for event in news:
        impact = str(event.get("impact", ""))
        currency = event.get("currency", "")

        # Controllo più robusto
        if "High" in impact and currency in ["USD", "EUR"]:
            filtered_news.append(event)

    if not filtered_news:
        logging.info("Nessun evento USD/EUR High Impact trovato")
        return

    # Ordina per data
    def parse_date(event):
        try:
            return datetime.strptime(event.get("date"), "%Y-%m-%d %H:%M:%S")
        except:
            return datetime.max

    filtered_news.sort(key=parse_date)

    header = ""
    if initial:
        header = "🚀 *Bot avviato correttamente!*\n\n"

    header += "📅 *Eventi HIGH IMPACT della settimana*\n"
    header += "💱 Valute: USD & EUR\n\n"

    message_body = ""

    for event in filtered_news:
        event_id = event.get("id")

        if event_id in sent_events:
            continue

        currency = event.get("currency")
        title = event.get("title")
        date_str = event.get("date")

        message_body += (
            f"📊 *{currency}*\n"
            f"📰 {title}\n"
            f"⏰ {date_str}\n\n"
        )

        sent_events.add(event_id)

    if message_body:
        send_message(header + message_body)
        logging.info(f"Inviati {len(filtered_news)} eventi filtrati")
