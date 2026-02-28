# Usa immagine Python leggera
FROM python:3.11-slim

# Evita bytecode e buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cartella di lavoro
WORKDIR /app

# Copia requirements
COPY requirements.txt .

# Installa dipendenze
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copia tutto il progetto
COPY . .

# Espone la porta (Render la assegna dinamicamente)
EXPOSE 10000

# Avvia con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
