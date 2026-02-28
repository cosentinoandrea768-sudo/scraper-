from scheduler import start_scheduler
from config import CHECK_INTERVAL_MINUTES
import time

if __name__ == "__main__":
    print("🚀 Forex Factory Telegram Bot avviato...")
    start_scheduler(CHECK_INTERVAL_MINUTES)

    while True:
        time.sleep(60)
