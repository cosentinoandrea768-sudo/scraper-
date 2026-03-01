# Usa immagine Python leggera
FROM python:3.11-slim

# Evita bytecode e buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cartella di lavoro
WORKDIR /app

# Copia requirements
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copia il codice
COPY . .

# Espone la porta (Render la assegna via $PORT, ma dichiariamo lo stesso)
EXPOSE 10000

# Avvia con Gunicorn (usa --preload se hai problemi con APScheduler multi-worker)
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--timeout", "120", "app:app"]
