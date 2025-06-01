from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
import qrcode
import os
import sqlite3
import re

from invoice_utils import process_invoice_text

app = Flask(__name__)

# Upload-Ordner
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# SQLite Datenbankpfad
DATABASE = 'invoiceinsight.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            invoice_number TEXT,
            invoice_date TEXT,
            total_amount REAL,
            tax_rate REAL,
            supplier TEXT,
            raw_text TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Hilfsfunktionen für Extraktion (Platzhalter)
def extract_invoice_number(text):
    # Beispiel-RegEx, anpassen je nach Rechnungsformat
    match = re.search(r'Rechnung\s*Nr\.?\s*[:\-]?\s*(\S+)', text, re.IGNORECASE)
    return match.group(1) if match else None

def extract_invoice_date(text):
    # Beispiel-RegEx für Datum (dd.mm.yyyy)
    match = re.search(r'(\d{2}\.\d{2}\.\d{4})', text)
    return match.group(1) if match else None

def extract_total_amount(text):
    # Beispiel-RegEx für Betrag, z.B. 1234,56 oder 1.234,56
    match = re.search(r'Gesamt(?:betrag)?\s*[:\-]?\s*([\d\.,]+)', text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace('.', '').replace(',', '.')
        try:
            return float(amount_str)
        except ValueError:
            return None
    return None

# API-Endpunkt: Rechnung hochladen und verarbeiten
@app.route('/api/invoice/upload', methods=['POST'])
def upload_invoice():
    if 'file' not in request.files:
        return jsonify({'error': 'Keine Datei im Request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Keine Datei ausgewählt'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        img = Image.open(filepath)
        raw_text = pytesseract.image_to_string(img, lang='deu+eng')
    except Exception as e:
        return jsonify({'error': f'OCR fehlgeschlagen: {str(e)}'}), 500

    invoice_number = extract_invoice_number(raw_text)
    invoice_date = extract_invoice_date(raw_text)
    total_amount = extract_total_amount(raw_text)

    # Optional: Validierung (hier kannst du eigene Logik ergänzen)
    errors = []
    if not invoice_number:
        errors.append('Rechnungsnummer nicht gefunden.')
    if not invoice_date:
        errors.append('Rechnungsdatum nicht gefunden.')
    if not total_amount:
        errors.append('Gesamtbetrag nicht gefunden.')

    if errors:
        return jsonify({'errors': errors}), 400

    # QR-Code generieren
    qr_content = {
        'invoice_number': invoice_number,
        'invoice_date': invoice_date,
        'total_amount': total_amount
    }
    qr_data_str = str(qr_content)
    qr_img = qrcode.make(qr_data_str)
    qr_filename = f"qr_{os.path.splitext(filename)[0]}.png"
    qr_filepath = os.path.join(app.config['UPLOAD_FOLDER'], qr_filename)
    qr_img.save(qr_filepath)

    # In DB speichern
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO invoices (filename, invoice_number, invoice_date, total_amount, tax_rate, supplier, raw_text)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        filename,
        invoice_number,
        invoice_date,
        total_amount,
        None,  # tax_rate (kann später ergänzt werden)
        None,  # supplier (kann später ergänzt werden)
        raw_text
    ))
    conn.commit()
    invoice_id = cursor.lastrowid
    conn.close()

    return jsonify({
        'message': 'Rechnung erfolgreich verarbeitet',
        'invoice_id': invoice_id,
        'invoice_number': invoice_number,
        'invoice_date': invoice_date,
        'total_amount': total_amount,
        'qr_code_url': f'/api/invoice/qr/{qr_filename}'
    }), 201

# QR-Code abrufen
@app.route('/api/invoice/qr/<filename>', methods=['GET'])
def get_qr_code(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Liste aller Rechnungen
@app.route('/api/invoices', methods=['GET'])
def list_invoices():
    conn = get_db_connection()
    invoices = conn.execute('SELECT * FROM invoices').fetchall()
    conn.close()
    result = []
    for inv in invoices:
        result.append({
            'id': inv['id'],
            'filename': inv['filename'],
            'invoice_number': inv['invoice_number'],
            'invoice_date': inv['invoice_date'],
            'total_amount': inv['total_amount']
        })
    return jsonify(result)

# Einzelne Rechnung abrufen
@app.route('/api/invoice/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    conn = get_db_connection()
    invoice = conn.execute('SELECT * FROM invoices WHERE id = ?', (invoice_id,)).fetchone()
    conn.close()
    if invoice is None:
        return jsonify({'error': 'Rechnung nicht gefunden'}), 404
    return jsonify(dict(invoice))

# Test-Endpoint
@app.route('/api/test', methods=['GET'])
def api_test():
    return jsonify({
        "message": "API läuft!",
        "sample_invoice": {
            "invoice_number": "INV-12345",
            "invoice_date": "2025-06-01",
            "total_amount": 1234.56,
            "supplier": "Beispiel GmbH"
        }
    })

# Root-Route
@app.route('/')
def index():
    return "InvoiceInsight API läuft! Benutze /api/test, um die API zu testen."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)