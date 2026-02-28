import time
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from config import ALLOWED_ELEMENT_TYPES, ICON_COLOR_MAP
from utilities import save_csv
import config


def init_driver(headless=True):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("window-size=1920x1080")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def scroll_to_end(driver):
    previous_position = None
    while True:
        current_position = driver.execute_script("return window.pageYOffset;")
        driver.execute_script("window.scrollTo(0, window.pageYOffset + 500);")
        time.sleep(2)
        if current_position == previous_position:
            break
        previous_position = current_position


def parse_table(driver, month, year):
    data = []
    table = driver.find_element(By.CLASS_NAME, "calendar__table")

    for row in table.find_elements(By.TAG_NAME, "tr"):
        row_data = {}
        event_id = row.get_attribute("data-event-id")

        for element in row.find_elements(By.TAG_NAME, "td"):
            class_name = element.get_attribute("class")

            if class_name in ALLOWED_ELEMENT_TYPES:
                key = ALLOWED_ELEMENT_TYPES[class_name]

                if "calendar__impact" in class_name:
                    color = None
                    for impact in element.find_elements(By.TAG_NAME, "span"):
                        color = ICON_COLOR_MAP.get(impact.get_attribute("class"))
                    row_data[key] = color if color else "impact"

                elif "calendar__detail" in class_name and event_id:
                    row_data[key] = f"https://www.forexfactory.com/calendar?month={month}#detail={event_id}"
                elif element.text:
                    row_data[key] = element.text
                else:
                    row_data[key] = "empty"

        if row_data:
            data.append(row_data)

    save_csv(data, month, year)
    return data, month


def main():
    parser = argparse.ArgumentParser(description="Scrape Forex Factory calendar.")
    parser.add_argument("--months", nargs="+", help='Target months: e.g., this next')
    args = parser.parse_args()
    month_params = args.months if args.months else ["this"]

    for param in month_params:
        driver = init_driver()
        url = f"https://www.forexfactory.com/calendar?month={param}"
        print(f"[INFO] Navigating to {url}")
        driver.get(url)
        detected_tz = driver.execute_script("return Intl.DateTimeFormat().resolvedOptions().timeZone")
        print(f"[INFO] Browser timezone: {detected_tz}")
        config.SCRAPER_TIMEZONE = detected_tz
        scroll_to_end(driver)

        now = datetime.now()
        if param.lower() == "this":
            month, year = now.strftime("%B"), now.year
        elif param.lower() == "next":
            next_month = (now.month % 12) + 1
            year = now.year if now.month < 12 else now.year + 1
            month = datetime(year, next_month, 1).strftime("%B")
        else:
            month, year = param.capitalize(), now.year

        print(f"[INFO] Scraping data for {month} {year}")
        try:
            parse_table(driver, month, str(year))
        except Exception as e:
            print(f"[ERROR] Failed to scrape {param} ({month} {year}): {e}")
        driver.quit()
        time.sleep(3)


if __name__ == "__main__":
    main()
