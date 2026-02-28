# Usa Python 3.11 stabile
FROM python:3.11-slim

# Imposta la working directory
WORKDIR /app

# Copia file requirements e progetto
COPY requirements.txt .
COPY . .

# Aggiorna pip e installa dipendenze
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Espone la porta di Flask
EXPOSE 5000

# Comando per avviare il bot
CMD ["python", "main.py"]
