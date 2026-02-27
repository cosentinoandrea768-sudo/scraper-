# -----------------------------
# logic_impact.py
# -----------------------------

def parse_number(value):
    """
    Converte stringhe tipo 0.5%, 1.2K, 3.4M in float
    """
    if value is None or value == "-":
        return None
    try:
        value = str(value).replace("%", "").replace(",", "").strip()
        if "K" in value:
            return float(value.replace("K",""))*1_000
        if "M" in value:
            return float(value.replace("M",""))*1_000_000
        return float(value)
    except:
        return None

def calculate_surprise(actual, forecast):
    actual = parse_number(actual)
    forecast = parse_number(forecast)
    if actual is None or forecast is None or forecast == 0:
        return 0
    return ((actual - forecast)/abs(forecast))*100

POSITIVE_WHEN_HIGHER = [
    "GDP","CPI","Core CPI","Retail Sales","Non Farm Payrolls",
    "PMI","Interest Rate","Industrial Production"
]

POSITIVE_WHEN_LOWER = [
    "Unemployment Rate","Jobless Claims","Initial Jobless Claims"
]

def evaluate_impact(event_name, actual, forecast):
    actual_num = parse_number(actual)
    forecast_num = parse_number(forecast)

    if actual_num is None or forecast_num is None:
        return "⚪ Neutro", 0

    surprise = calculate_surprise(actual, forecast)
    abs_surprise = abs(surprise)

    # Determina se alto o basso è positivo
    category = "higher"
    for key in POSITIVE_WHEN_LOWER:
        if key.lower() in event_name.lower():
            category = "lower"
            break

    direction = 1 if (category=="higher" and actual_num>forecast_num) or (category=="lower" and actual_num<forecast_num) else -1

    # Label forza impatto
    if abs_surprise > 2:
        label = "🟢 Strong Positive" if direction>0 else "🔴 Strong Negative"
    else:
        label = "🟢 Mild Positive" if direction>0 else "🔴 Mild Negative"

    score = direction * (2 if abs_surprise>2 else 1)
    return label, score
