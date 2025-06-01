# InvoiceInsight

**InvoiceInsight** ist eine smarte Softwarelösung zur automatisierten Analyse und Extraktion relevanter Informationen aus Rechnungsdokumenten in verschiedenen Formaten (PDF, Bilder, Scans). Ziel ist es, die manuelle Dateneingabe zu minimieren, Fehler zu reduzieren und die Verarbeitung von Rechnungen effizienter zu gestalten.

---

## Inhalt

1. [Projektbeschreibung](#projektbeschreibung)  
2. [Technologien](#technologien)  
3. [Funktionen](#funktionen)  
4. [API Endpoints](#api-endpoints)  
5. [Installation & Entwicklung](#installation--entwicklung)  
6. [CI/CD Workflow](#cicd-workflow)  
7. [Nächste Schritte](#nächste-schritte)

---

## Projektbeschreibung

InvoiceInsight erkennt automatisch Rechnungsinformationen per OCR und extrahiert relevante Daten wie Rechnungsnummer, Datum, Betrag, Lieferant und Steuersatz. Die Lösung bietet eine REST-API, die Rechnungen entgegennimmt, verarbeitet und Ergebnisse inklusive QR-Codes zurückliefert.

---

## Technologien

- Python 3.12  
- Flask (Web-API)  
- pytesseract (OCR)  
- Pillow (Bildverarbeitung)  
- qrcode (QR-Code Generierung)  
- SQLite (leichte Datenbank)  
- Docker & Docker Compose (Containerisierung und Deployment)  
- GitHub Actions (CI/CD)

---

## Funktionen

- Hochladen von Rechnungsbildern per REST-API  
- OCR-basierte Texterkennung (Deutsch & Englisch)  
- Extraktion von Rechnungsnummer, Datum, Gesamtbetrag, Lieferant, Steuersatz  
- Validierung der extrahierten Daten mit Plausibilitätsprüfung  
- Automatische Generierung und Bereitstellung von QR-Codes mit Rechnungsinfos  
- Speicherung der Rechnungen und Metadaten in SQLite-Datenbank  
- API-Endpoints zum Abrufen von Rechnungen und QR-Codes  
- Lokale und containerisierte Ausführung mittels Docker

---

## API Endpoints

| Methode | URL                     | Beschreibung                         |
|---------|-------------------------|------------------------------------|
| GET     | `/api/test`              | Test-Endpoint, gibt Beispielantwort zurück |
| POST    | `/api/invoice/upload`    | Upload und Verarbeitung einer Rechnung (Bild) |
| GET     | `/api/invoice/qr/<datei>` | Abruf des generierten QR-Code Bildes |
| GET     | `/api/invoices`          | Liste aller gespeicherten Rechnungen |

---

## Installation & Entwicklung

### Voraussetzungen

- Python 3.12  
- Docker (optional für Containerisierung)  
- Tesseract-OCR (systemabhängig)  

### Setup

1. Projekt klonen / lokal anlegen  
2. Virtuelle Umgebung anlegen und aktivieren  
   ```bash
   python3 -m venv venv
   source venv/bin/activate