# Mapping of Forex Factory element class names to semantic labels for parsing.
ALLOWED_ELEMENT_TYPES = {
    "calendar__cell": "date",  # Generic cell (used for date continuation rows)
    "calendar__cell calendar__date": "date",  # Date of the news event
    "calendar__cell calendar__time": "time",  # Time of the news event
    "calendar__cell calendar__currency": "currency",  # Affected currency
    "calendar__cell calendar__impact": "impact",  # Expected impact level (color-coded)
    "calendar__cell calendar__detail": "detail",  # Detail/URL for the event
    "calendar__cell calendar__event event": "event",  # News event title
    "calendar__cell calendar__actual": "actual",  # Actual reported value
    "calendar__cell calendar__forecast": "forecast",  # Forecasted value
    "calendar__cell calendar__previous": "previous",  # Previously reported value
}

EXCLUDED_ELEMENT_TYPES = [
    "calendar__cell calendar__graph",  # Graph cell not relevant
]

ICON_COLOR_MAP = {
    "icon icon--ff-impact-yel": "yellow",
    "icon icon--ff-impact-ora": "orange",
    "icon icon--ff-impact-red": "red",
    "icon icon--ff-impact-gra": "gray"
}

ALLOWED_CURRENCY_CODES = ['CAD', 'EUR', 'GBP', 'USD']
ALLOWED_IMPACT_COLORS = ['red', 'orange', 'gray']

TARGET_TIMEZONE = "Europe/London"
SCRAPER_TIMEZONE = None  # Populated dynamically during scraping
