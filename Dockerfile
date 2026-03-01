# ==============================
# Dockerfile per Bot Forex Telegram
# ==============================

# Base image Python slim
FROM python:3.11-slim

# Imposta la working directory
WORKDIR /app

# Copia requirements e installa le dipendenze
COPY requirements.txt .

# Aggiorna pip e installa le dipendenze
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copia tutto il progetto nel container
COPY . .

# Esponi la porta (Render passerà $PORT)
EXPOSE 10000

# Avvio del bot con Gunicorn, legge $PORT da Render
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-10000} --workers 1"]
