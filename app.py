from flask import Flask, request, jsonify, send_from_directory
from invoice_utils import process_invoice_text, validate_invoice_data
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import qrcode
import os
import sqlite3
import re

# Flask App initialisieren
app = Flask(__name__)

# Upload-Ordner für Dokumente (lokal)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# SQLite Datenbank-Verbindung
DATABASE = 'invoiceinsight.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Datenbank initialisieren (wenn noch nicht vorhanden)
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

# API-Endpunkt: Hochladen und OCR-Verarbeitung einer Rechnung mit QR-Code-Erzeugung
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

    # OCR mit pytesseract auf der Datei ausführen
    try:
        img = Image.open(filepath)
        raw_text = pytesseract.image_to_string(img, lang='deu+eng')  # Deutsch + Englisch
    except Exception as e:
        return jsonify({'error': f'OCR fehlgeschlagen: {str(e)}'}), 500

    # Daten extrahieren und validieren
    invoice_data = process_invoice_text(raw_text)
    validation_errors = validate_invoice_data(invoice_data)

    if validation_errors:
        return jsonify({'errors': validation_errors}), 400

    # QR-Code Inhalt (JSON-artiger String mit wichtigen Feldern)
    qr_content = {
        'invoice_number': invoice_data.get('invoice_number'),
        'invoice_date': str(invoice_data.get('invoice_date')),
        'total_amount': invoice_data.get('total_amount'),
        'supplier': invoice_data.get('supplier')
    }
    qr_data_str = str(qr_content)

    # QR-Code generieren und speichern
    qr_img = qrcode.make(qr_data_str)
    qr_filename = f"qr_{os.path.splitext(filename)[0]}.png"
    qr_filepath = os.path.join(app.config['UPLOAD_FOLDER'], qr_filename)
    qr_img.save(qr_filepath)

    # Daten in DB speichern, inkl. QR-Code-Daten
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO invoices (filename, invoice_number, invoice_date, total_amount, tax_rate, supplier, raw_text)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        filename,
        invoice_data.get('invoice_number'),
        invoice_data.get('invoice_date'),
        invoice_data.get('total_amount'),
        invoice_data.get('tax_rate'),
        invoice_data.get('supplier'),
        raw_text
    ))
    conn.commit()
    invoice_id = cursor.lastrowid
    conn.close()

    return jsonify({
        'message': 'Rechnung erfolgreich verarbeitet',
        'invoice_id': invoice_id,
        'invoice_number': invoice_data.get('invoice_number'),
        'invoice_date': invoice_data.get('invoice_date'),
        'total_amount': invoice_data.get('total_amount'),
        'qr_code_url': f'/api/invoice/qr/{qr_filename}'
    }), 201

# Endpoint zum Abrufen des QR-Code-Bildes
@app.route('/api/invoice/qr/<filename>', methods=['GET'])
def get_qr_code(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# API-Endpunkt: Liste aller Rechnungen anzeigen
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

# Einfacher Test-Endpoint, um zu prüfen, ob die API läuft
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

# Root-Route separat, nicht eingerückt
@app.route('/')
def index():
    return "InvoiceInsight API läuft! Benutze /api/test, um die API zu testen."

@app.route('/api/invoice/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    conn = get_db_connection()
    invoice = conn.execute('SELECT * FROM invoices WHERE id = ?', (invoice_id,)).fetchone()
    conn.close()
    if invoice is None:
        return jsonify({'error': 'Rechnung nicht gefunden'}), 404
    return jsonify(dict(invoice))

# Startpunkt für lokalen Test
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)