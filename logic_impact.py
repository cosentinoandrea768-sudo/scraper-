import re
import json
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright

FOREX_CALENDAR_URL = "https://www.forexfactory.com/calendar"

async def get_forex_news_today(for_week=False):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(FOREX_CALENDAR_URL)
            html = await page.content()
            await browser.close()

        pattern = r"window\.calendarComponentStates\s*=\s*(\{.*?\});"
        match = re.search(pattern, html, re.DOTALL)

        if not match:
            return ["❌ Impossibile trovare calendarComponentStates nella pagina."]

        js_obj_str = match.group(1)
        js_obj_str = js_obj_str.replace("'", '"')
        js_obj_str = re.sub(r'(\w+):', r'"\1":', js_obj_str)
        data = json.loads(js_obj_str)

        tz = timezone(timedelta(hours=1))
        today_str = datetime.now(tz).strftime("%b %d")

        news_list = []

        for day in data.get("1", {}).get("days", []):
            day_date = day.get("date", "")
            if not for_week and today_str not in day_date:
                continue

            for event in day.get("events", []):
                news_list.append({
                    "prefixedName": event.get("prefixedName", "N/A"),
                    "timeLabel": event.get("timeLabel", "All Day"),
                    "forecast": event.get("forecast", ""),
                    "actual": event.get("actual", ""),
                    "url": f"https://www.forexfactory.com{event.get('soloUrl','')}"
                })

        if not news_list:
            return ["Nessun evento trovato."]

        return news_list

    except Exception as e:
        return [f"Errore nello scraping: {e}"]
