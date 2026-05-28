import csv
import io
from datetime import datetime
from decimal import Decimal

# SAP MM module flat file export ke German column headers
# Source: SAP Help Portal - MM60 / MB51 transaction exports
# WERKS = plant code, MENGE = quantity, MEINS = base unit of measure
# BUDAT = posting date (YYYYMMDD format), MATNR = material number

SAP_COLUMN_MAP = {
    'WERKS': 'plant_code',
    'MATNR': 'material',
    'MENGE': 'quantity',
    'MEINS': 'unit',
    'BUDAT': 'posting_date',
    'BKTXT': 'description',
    # English headers bhi handle karo — kuch SAP configs mein hote hain
    'Plant': 'plant_code',
    'Material': 'material',
    'Quantity': 'quantity',
    'Unit': 'unit',
    'Posting Date': 'posting_date',
}

# Plant code lookup — real deployment mein client provide karta hai ye table
# Ye hardcoded hai — DECISIONS.md mein mention karein
PLANT_LOOKUP = {
    'PL01': 'Mumbai Plant',
    'PL02': 'Delhi Plant',
    'PL03': 'Pune Plant',
    'PL04': 'Chennai Plant',
}

# Unit normalization to liters
# Source: IPCC + common conversion factors
UNIT_TO_LITERS = {
    'L': Decimal('1'),
    'LTR': Decimal('1'),
    'GAL': Decimal('3.785'),   # US gallon
    'GL': Decimal('3.785'),
    'KG': Decimal('1.18'),     # diesel approx (density varies by grade)
    'MT': Decimal('1180'),     # metric tonne of diesel
}

# kgCO2e per liter — DEFRA 2023
FUEL_EMISSION_FACTORS = {
    'diesel': Decimal('2.68'),
    'petrol': Decimal('2.31'),
    'default': Decimal('2.68'),
}


def parse_sap_date(date_str):
    """SAP date formats: YYYYMMDD ya DD.MM.YYYY ya DD/MM/YYYY"""
    date_str = str(date_str).strip()
    for fmt in ('%Y%m%d', '%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def parse_sap_file(file_content: bytes):
    """
    SAP flat file CSV parse karo.
    Returns: (records, errors)
    records = list of dicts with normalized fields
    errors = list of (row_num, reason)
    """
    records = []
    errors = []

    try:
        text = file_content.decode('utf-8', errors='replace')
        reader = csv.DictReader(io.StringIO(text))
    except Exception as e:
        return [], [(0, f"File read failed: {e}")]

    for i, row in enumerate(reader, start=2):
        # German headers ko English mein map karo
        # raw_extras: jo columns COLUMN_MAP mein nahi hain unhe preserve karo
        # Agar client ne extra column bheja toh wo silently drop nahi hoga
        normalized_row = {}
        raw_extras = {}
        for key, val in row.items():
            mapped = SAP_COLUMN_MAP.get(key.strip())
            if mapped:
                normalized_row[mapped] = val.strip() if val else ''
            else:
                raw_extras[key.strip()] = val.strip() if val else ''

        # Required fields check
        missing = [f for f in ['quantity', 'unit', 'posting_date'] if not normalized_row.get(f)]
        if missing:
            errors.append((i, f"Missing fields: {', '.join(missing)}"))
            continue

        # Date parse
        date = parse_sap_date(normalized_row['posting_date'])
        if not date:
            errors.append((i, f"Unparseable date: {normalized_row['posting_date']}"))
            continue

        # Quantity parse — German format: 4.500,000 (dot=thousands, comma=decimal)
        # Simple replace(',', '.') would give 4.500.000 which is invalid
        # Correct: remove dots first (thousands separator), then replace comma with dot
        try:
            qty_str = normalized_row['quantity']
            if ',' in qty_str and '.' in qty_str:
                # German format: 4.500,000 → remove dots → 4500,000 → replace comma → 4500.000
                qty_str = qty_str.replace('.', '').replace(',', '.')
            elif ',' in qty_str:
                # Could be decimal comma: 4500,5 → 4500.5
                qty_str = qty_str.replace(',', '.')
            quantity = Decimal(qty_str)
        except Exception:
            errors.append((i, f"Invalid quantity: {normalized_row['quantity']}"))
            continue

        unit = normalized_row['unit'].upper().strip()
        plant_code = normalized_row.get('plant_code', '')
        location = PLANT_LOOKUP.get(plant_code, plant_code)

        # Material se fuel type detect karo — petrol vs diesel
        material = normalized_row.get('material', '').upper()
        if 'PETROL' in material or 'MS' in material or 'MOGAS' in material:
            fuel_factor = FUEL_EMISSION_FACTORS['petrol']
        else:
            fuel_factor = FUEL_EMISSION_FACTORS['diesel']

        # Liters mein convert karo
        multiplier = UNIT_TO_LITERS.get(unit)
        flag_parts = []
        if not multiplier:
            qty_liters = quantity
            flag_parts.append(f"Unknown unit '{unit}' — could not normalize to liters")
        else:
            qty_liters = quantity * multiplier

        if raw_extras:
            flag_parts.append(f"Extra columns preserved: {list(raw_extras.keys())}")

        kgco2e = qty_liters * fuel_factor

        raw_with_extras = dict(row)

        records.append({
            'raw': raw_with_extras,
            'scope': 1,
            'category': 'fuel',
            'quantity_original': quantity,
            'unit_original': unit,
            'quantity_normalized': qty_liters,
            'unit_normalized': 'L',
            'emission_factor': fuel_factor,
            'emission_factor_source': 'DEFRA 2023',
            'kgco2e': kgco2e,
            'activity_date': date,
            'location': location,
            'description': normalized_row.get('description', ''),
            'flag': ' | '.join(flag_parts) if flag_parts else None,
        })

    return records, errors
