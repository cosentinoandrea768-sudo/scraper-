from datetime import datetime, timedelta
from market_calendar_tool import scrape_calendar, Site
import pandas as pd

def get_forex_news_today(for_week=False):
    """
    Recupera le news da ForexFactory tramite market-calendar-tool.
    for_week=False -> news di oggi
    for_week=True  -> news della settimana corrente
    Restituisce lista di dict pronti per Telegram.
    """
    try:
        df = scrape_calendar(site=Site.FOREXFACTORY)

        if df is None or df.empty:
            return ["Nessun evento trovato."]

        # Assicuriamoci che la colonna date sia datetime
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        today = datetime.utcnow().date()

        if for_week:
            end_week = today + timedelta(days=7)
            df_filtered = df[(df["date"].dt.date >= today) &
                             (df["date"].dt.date <= end_week)]
        else:
            df_filtered = df[df["date"].dt.date == today]

        if df_filtered.empty:
            return ["Nessun evento trovato."]

        news_list = []

        for _, row in df_filtered.iterrows():
            news_list.append({
                "prefixedName": row.get("event", "N/A"),
                "timeLabel": str(row.get("time", "All Day")),
                "forecast": row.get("forecast", ""),
                "actual": row.get("actual", ""),
                "url": "https://www.forexfactory.com/calendar"
            })

        return news_list

    except Exception as e:
        return [f"Errore nello scraping: {e}"]
