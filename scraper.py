import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from config import FOREX_FACTORY_URL

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def scrape_forex_factory():
    driver = init_driver()
    driver.get(FOREX_FACTORY_URL)
    time.sleep(5)

    events = []

    rows = driver.find_elements(By.CSS_SELECTOR, "tr.calendar__row")

    for row in rows:
        try:
            time_el = row.find_element(By.CLASS_NAME, "calendar__time").text
            currency = row.find_element(By.CLASS_NAME, "calendar__currency").text
            impact = row.find_element(By.CLASS_NAME, "calendar__impact").get_attribute("title")
            event = row.find_element(By.CLASS_NAME, "calendar__event").text

            events.append({
                "time": time_el,
                "currency": currency,
                "impact": impact,
                "event": event
            })
        except:
            continue

    driver.quit()
    return pd.DataFrame(events)
