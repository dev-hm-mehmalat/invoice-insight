# Basis-Image mit Python 3.12
FROM python:3.12-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere requirements-Datei ins Arbeitsverzeichnis
COPY requirements.txt .

# Installiere Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den Rest des Projekts
COPY . .

# Öffne Port 5001
EXPOSE 5001

# Starte die Flask-Anwendung
CMD ["python", "app.py"]