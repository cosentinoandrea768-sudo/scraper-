import os

# Legge le environment variables di Render
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # token reale del bot
CHAT_ID = os.environ.get("CHAT_ID")      # chat ID reale
CSV_FILE = "events.csv"
TIMEZONE_OFFSET = 1  # ore rispetto a UTC
