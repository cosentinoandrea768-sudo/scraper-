import os
import re
import json
import pytz
import pandas as pd
from datetime import datetime
import config
from urllib.request import urlopen


def read_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def extract_date_parts(text, year):
    pattern = r'\b(?P<day>Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b\s+' \
              r'(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b\s+' \
              r'(?P<date>\d{1,2})\b'
    match = re.search(pattern, text)
    if match:
        month_number = datetime.strptime(match.group("month"), "%b").month
        day = int(match.group("date"))
        formatted_date = f"{day:02d}/{month_number:02d}/{year}"
        return {"day": match.group("day"), "date": formatted_date}
    return None


def filter_row(row):
    if row['currency'] not in config.ALLOWED_CURRENCY_CODES:
        return False
    if row['impact'].lower() not in config.ALLOWED_IMPACT_COLORS:
        return False
    return True


def convert_time_zone(date_str, time_str, from_zone_str, to_zone_str):
    if not time_str or not date_str:
        return time_str
    if time_str.lower() in ["all day", "tentative"]:
        return time_str
    try:
        from_zone = pytz.timezone(from_zone_str)
        to_zone = pytz.timezone(to_zone_str)
        naive_dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %I:%M%p")
        localized_dt = from_zone.localize(naive_dt)
        converted_dt = localized_dt.astimezone(to_zone)
        return converted_dt.strftime("%H:%M")
    except Exception as e:
        print(f"[WARN] Failed to convert '{time_str}' on {date_str}: {e}")
        return time_str


def find_location_timezone():
    try:
        with urlopen('http://ipinfo.io/json') as response:
            data = json.load(response)
            return data.get('timezone')
    except Exception:
        return None


def reformat_data(data: list, year: str) -> list:
    current_date = ''
    current_time = ''
    current_day = ''
    structured_rows = []

    for row in data:
        new_row = row.copy()
        if "date" in new_row and new_row['date'] != "empty":
            date_parts = extract_date_parts(new_row["date"], year)
            if date_parts:
                current_date = date_parts["date"]
                current_day = date_parts["day"]

        if "time" in new_row:
            if new_row["time"] != "empty":
                current_time = new_row["time"].strip()
            else:
                new_row["time"] = current_time

        if len(row) == 1:
            continue

        new_row["day"] = current_day
        new_row["date"] = current_date

        scraper_timezone = config.SCRAPER_TIMEZONE or find_location_timezone()
        if scraper_timezone and config.TARGET_TIMEZONE:
            new_row["time"] = convert_time_zone(
                current_date, current_time, scraper_timezone, config.TARGET_TIMEZONE
            )
        else:
            new_row["time"] = current_time

        for key in ["currency", "impact", "event", "detail", "actual", "forecast", "previous"]:
            new_row[key] = row.get(key, "")

        # Replace "empty" with ""
        for key, value in new_row.items():
            if value == "empty":
                new_row[key] = ""

        if filter_row(new_row):
            structured_rows.append(new_row)

    return structured_rows


def save_csv(data, month, year):
    structured_rows = reformat_data(data, year)
    if not structured_rows:
        return False
    header = list(structured_rows[0].keys())
    df = pd.DataFrame(structured_rows, columns=header)
    os.makedirs("news", exist_ok=True)
    df.to_csv(f"news/{month}_{year}_news.csv", index=False)
    return True
