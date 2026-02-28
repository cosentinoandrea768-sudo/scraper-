from apscheduler.schedulers.blocking import BlockingScheduler
from scraper import scrape_forex_factory
from main import send_upcoming_events

sched = BlockingScheduler()

# Aggiorna CSV ogni ora
sched.add_job(scrape_forex_factory, 'interval', hours=1)

# Controlla eventi prossimi e invia ogni 10 minuti
sched.add_job(send_upcoming_events, 'interval', minutes=10)

if __name__ == "__main__":
    sched.start()
