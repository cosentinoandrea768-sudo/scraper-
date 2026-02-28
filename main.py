# main.py
import argparse
import time
from datetime import datetime
import config
from scraper import init_driver, scroll_to_end, parse_table

def determine_month_year(param):
    """Ritorna il mese leggibile e l'anno in base al parametro ('this', 'next' o nome del mese)."""
    now = datetime.now()
    if param == "this":
        month = now.strftime("%B")
        year = now.year
    elif param == "next":
        next_month = (now.month % 12) + 1
        year = now.year if now.month < 12 else now.year + 1
        month = datetime(year, next_month, 1).strftime("%B")
    else:
        month = param.capitalize()
        year = now.year
    return month, year

def main():
    parser = argparse.ArgumentParser(description="Scrape Forex Factory calendar.")
    parser.add_argument(
        "--months",
        nargs="+",
        help='Target months to scrape, e.g., "this next" or "January February"'
    )
    args = parser.parse_args()

    month_params = args.months if args.months else ["this"]

    for param in month_params:
        param_lower = param.lower()
        url = f"https://www.forexfactory.com/calendar?month={param_lower}"
        print(f"\n[INFO] Navigating to {url}")

        # Inizializza il driver
        driver = init_driver()
        try:
            driver.get(url)
            detected_tz = driver.execute_script(
                "return Intl.DateTimeFormat().resolvedOptions().timeZone"
            )
            print(f"[INFO] Browser timezone detected: {detected_tz}")
            config.SCRAPER_TIMEZONE = detected_tz

            # Scrolla fino in fondo per caricare tutti gli eventi
            scroll_to_end(driver)

            # Determina mese e anno leggibili
            month, year = determine_month_year(param_lower)
            print(f"[INFO] Scraping data for {month} {year}")

            # Parse della tabella e salvataggio CSV
            parse_table(driver, month, str(year))
            print(f"[SUCCESS] Data saved for {month} {year}")

        except Exception as e:
            print(f"[ERROR] Failed to scrape {param} ({month} {year}): {e}")
        finally:
            driver.quit()
            time.sleep(2)  # Piccola pausa tra scraping di più mesi

if __name__ == "__main__":
    main()
