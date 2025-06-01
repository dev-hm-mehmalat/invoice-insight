import re
from datetime import datetime

# Beispiel: Erweiterte Extraktionsfunktionen

def extract_invoice_number(text):
    # Flexibleres Muster mit mehreren Varianten und optionaler Leerraumbehandlung
    patterns = [
        r'(Rechnungsnummer|Invoice Number|Invoice No\.?):?\s*([A-Z0-9\-\/]+)',
        r'Nr\.?\s*:\s*([A-Z0-9\-\/]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(2).strip()
    return None

def extract_invoice_date(text):
    # Suche nach gängigen Datumsformaten: dd.mm.yyyy, dd-mm-yyyy, yyyy-mm-dd etc.
    date_patterns = [
        r'(\d{2}[./-]\d{2}[./-]\d{4})',
        r'(\d{4}[./-]\d{2}[./-]\d{2})'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            date_str = match.group(1)
            # Versuche String in datetime zu parsen
            for fmt in ('%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%Y.%m.%d'):
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
    return None

def extract_total_amount(text):
    # Beträge erkennen, z.B. "Gesamtbetrag: 1.234,56" oder "Total: 1234.56"
    match = re.search(r'(Gesamtbetrag|Total|Amount):?\s*([0-9.,]+)', text, re.IGNORECASE)
    if match:
        amt_str = match.group(2).replace('.', '').replace(',', '.')
        try:
            return float(amt_str)
        except ValueError:
            return None
    return None

def extract_supplier(text):
    # Lieferant z.B. "Lieferant: Firma XYZ"
    match = re.search(r'(Lieferant|Supplier):?\s*(.+)', text, re.IGNORECASE)
    if match:
        # Nur die erste Zeile nach dem Schlüssel nehmen
        return match.group(2).split('\n')[0].strip()
    return None

def extract_tax_rate(text):
    # Steuersatz z.B. "MwSt: 19%"
    match = re.search(r'(MwSt|Tax Rate):?\s*(\d{1,2})%', text, re.IGNORECASE)
    if match:
        try:
            return int(match.group(2))
        except ValueError:
            return None
    return None

# Validierungsfunktionen

def validate_invoice_data(invoice):
    errors = []

    # Rechnungsnummer darf nicht leer sein
    if not invoice.get('invoice_number'):
        errors.append('Rechnungsnummer fehlt.')

    # Rechnungsdatum prüfen (kein zukünftiges Datum)
    invoice_date = invoice.get('invoice_date')
    if invoice_date:
        if invoice_date > datetime.today().date():
            errors.append('Rechnungsdatum liegt in der Zukunft.')

    # Betrag plausibel prüfen (positiv)
    total_amount = invoice.get('total_amount')
    if total_amount is None or total_amount <= 0:
        errors.append('Gesamtbetrag ist ungültig oder fehlt.')

    # Steuersatz plausibel prüfen (z.B. 0 - 100)
    tax_rate = invoice.get('tax_rate')
    if tax_rate is not None:
        if tax_rate < 0 or tax_rate > 100:
            errors.append('Steuersatz ist ungültig.')

    return errors

# Beispielhafte Nutzung (im Upload-Handler):

def process_invoice_text(raw_text):
    invoice_data = {
        'invoice_number': extract_invoice_number(raw_text),
        'invoice_date': extract_invoice_date(raw_text),
        'total_amount': extract_total_amount(raw_text),
        'supplier': extract_supplier(raw_text),
        'tax_rate': extract_tax_rate(raw_text)
    }

    # Validierung
    validation_errors = validate_invoice_data(invoice_data)
    if validation_errors:
        # Hier kannst du entscheiden, ob du Fehler zurückgibst oder nur loggst
        print("Validierungsfehler:", validation_errors)
    
    return invoice_data
