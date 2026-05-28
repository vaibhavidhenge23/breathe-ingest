import csv
import io
from datetime import datetime, timedelta
from decimal import Decimal

# Utility portal CSV export — MSEDCL / Tata Power style
# Real problem: billing period calendar month se align nahi karta
# e.g., bill: March 15 to April 14 — ye Q1 hai ya Q2?
# Decision: as-is store karo, period_start/end dono track karo
# Analyst decide karega normalization — DECISIONS.md mein mention hai

# kgCO2e per kWh — India grid emission factor
# Source: CEA (Central Electricity Authority) 2023 — 0.716 kgCO2e/kWh
INDIA_GRID_FACTOR = Decimal('0.716')

UTILITY_COLUMN_MAP = {
    # MSEDCL format
    'Consumer No': 'meter_id',
    'Billing Period': 'billing_period',
    'Units Consumed': 'kwh',
    'Units Consumed (kWh)': 'kwh',
    'Meter Reading Date': 'reading_date',
    'Tariff': 'tariff',
    # Generic format
    'meter_id': 'meter_id',
    'period': 'billing_period',
    'consumption_kwh': 'kwh',
    'date': 'reading_date',
}


def parse_billing_period(period_str):
    """
    Billing period formats:
    - "15/03/2024 - 14/04/2024"
    - "Mar 2024"
    - "2024-03"
    Returns (start_date, end_date) or (None, None)
    """
    period_str = str(period_str).strip()

    # "DD/MM/YYYY - DD/MM/YYYY"
    if ' - ' in period_str:
        parts = period_str.split(' - ')
        try:
            start = datetime.strptime(parts[0].strip(), '%d/%m/%Y').date()
            end = datetime.strptime(parts[1].strip(), '%d/%m/%Y').date()
            return start, end
        except ValueError:
            pass

    # "Mon YYYY" — assume full month
    for fmt in ('%b %Y', '%B %Y'):
        try:
            start = datetime.strptime(period_str, fmt).date()
            # Last day of month
            next_month = start.replace(day=28) + timedelta(days=4)
            end = next_month - timedelta(days=next_month.day)
            return start, end
        except ValueError:
            pass

    # "YYYY-MM"
    try:
        start = datetime.strptime(period_str, '%Y-%m').date()
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month - timedelta(days=next_month.day)
        return start, end
    except ValueError:
        pass

    return None, None


def parse_utility_file(file_content: bytes):
    records = []
    errors = []

    try:
        text = file_content.decode('utf-8', errors='replace')
        reader = csv.DictReader(io.StringIO(text))
    except Exception as e:
        return [], [(0, f"File read failed: {e}")]

    for i, row in enumerate(reader, start=2):
        norm = {}
        for key, val in row.items():
            mapped = UTILITY_COLUMN_MAP.get(key.strip())
            if mapped:
                norm[mapped] = val.strip() if val else ''

        # kWh required
        if not norm.get('kwh'):
            errors.append((i, "Missing kWh value"))
            continue

        try:
            kwh = Decimal(norm['kwh'].replace(',', ''))
        except Exception:
            errors.append((i, f"Invalid kWh: {norm['kwh']}"))
            continue

        period_start, period_end = None, None
        if norm.get('billing_period'):
            period_start, period_end = parse_billing_period(norm['billing_period'])

        flag = None
        if not period_start:
            flag = "Billing period could not be parsed — analyst should verify"

        # Estimated reads common hain — flag if meter_id missing
        if not norm.get('meter_id'):
            flag = (flag or '') + " | Meter ID missing"

        kgco2e = kwh * INDIA_GRID_FACTOR

        records.append({
            'raw': dict(row),
            'scope': 2,
            'category': 'electricity',
            'quantity_original': kwh,
            'unit_original': 'kWh',
            'quantity_normalized': kwh,
            'unit_normalized': 'kWh',
            'emission_factor': INDIA_GRID_FACTOR,
            'emission_factor_source': 'CEA India Grid 2023',
            'kgco2e': kgco2e,
            'activity_date': period_start,
            'period_start': period_start,
            'period_end': period_end,
            'location': norm.get('meter_id', ''),
            'description': norm.get('tariff', ''),
            'flag': flag,
        })

    return records, errors
