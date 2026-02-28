from datetime import datetime, timedelta
from market_calendar_tool import scrape_calendar, clean_calendar_data, Site


def get_current_week_events():
    """
    Restituisce lista eventi settimana corrente.
    """
    raw = scrape_calendar(site=Site.FOREXFACTORY, extended=True)
    cleaned = clean_calendar_data(raw)
    df = cleaned.base

    return dataframe_to_list(df)


def get_next_week_events():
    """
    Restituisce lista eventi settimana prossima.
    """
    today = datetime.utcnow()

    # Calcolo prossimo lunedì
    next_monday = today + timedelta(days=(7 - today.weekday()))
    next_sunday = next_monday + timedelta(days=6)

    raw = scrape_calendar(
        site=Site.FOREXFACTORY,
        date_from=next_monday.strftime("%Y-%m-%d"),
        date_to=next_sunday.strftime("%Y-%m-%d"),
        extended=True
    )

    cleaned = clean_calendar_data(raw)
    df = cleaned.base

    return dataframe_to_list(df)


def dataframe_to_list(df):
    """
    Converte DataFrame in lista di dict semplificata
    pronta per Telegram.
    """
    if df.empty:
        return []

    events = []

    for _, row in df.iterrows():
        events.append({
            "date": row.get("Date", ""),
            "time": row.get("Time", ""),
            "event": row.get("Event", ""),
            "impact": row.get("Impact", ""),
        })

    return events
