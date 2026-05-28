import json
from datetime import datetime
from decimal import Decimal
import math

# Concur / Navan travel export
# Real format: JSON array of expense reports
# Problem: distance field nahi hoti — sirf airport codes hote hain
# Solution: Haversine formula from IATA coordinates
# Yahi approach DEFRA travel calculator use karta hai

# kgCO2e per km — DEFRA 2023
# Business class = 2x economy (seat area factor)
FLIGHT_FACTORS = {
    'economy': Decimal('0.255'),
    'business': Decimal('0.510'),
    'first': Decimal('0.765'),
    'unknown': Decimal('0.255'),
}

HOTEL_FACTOR = Decimal('31.0')        # kgCO2e per night — DEFRA 2023
GROUND_FACTOR = Decimal('0.21')       # kgCO2e per km — taxi/cab

# Major airport coordinates (lat, lon)
# Subset — real deployment mein full IATA DB hogi
AIRPORT_COORDS = {
    'BOM': (19.0896, 72.8656),  # Mumbai
    'DEL': (28.5665, 77.1031),  # Delhi
    'BLR': (13.1979, 77.7063),  # Bangalore
    'MAA': (12.9941, 80.1709),  # Chennai
    'HYD': (17.2403, 78.4294),  # Hyderabad
    'CCU': (22.6542, 88.4467),  # Kolkata
    'LHR': (51.4775, -0.4614),  # London Heathrow
    'JFK': (40.6413, -73.7781), # New York
    'DXB': (25.2532, 55.3657),  # Dubai
    'SIN': (1.3644, 103.9915),  # Singapore
}


def haversine_km(lat1, lon1, lat2, lon2):
    """
    Great-circle distance between two points.
    Ye real flight path nahi hai — direct distance hai.
    DEFRA bhi yahi use karta hai with a 1.09 uplift factor for routing.
    """
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def get_flight_distance(origin, destination):
    """Returns (km, flag_message)"""
    orig = AIRPORT_COORDS.get(origin.upper())
    dest = AIRPORT_COORDS.get(destination.upper())

    if not orig or not dest:
        missing = []
        if not orig: missing.append(origin)
        if not dest: missing.append(destination)
        return None, f"Airport coordinates not found: {', '.join(missing)}"

    km = haversine_km(*orig, *dest) * 1.09  # DEFRA routing uplift
    return Decimal(str(round(km, 2))), None


def parse_travel_file(file_content: bytes):
    records = []
    errors = []

    try:
        data = json.loads(file_content.decode('utf-8'))
        # Support both array and {"trips": [...]}
        trips = data if isinstance(data, list) else data.get('trips', data.get('records', []))
    except Exception as e:
        return [], [(0, f"JSON parse failed: {e}")]

    for i, trip in enumerate(trips, start=1):
        trip_type = trip.get('type', 'flight').lower()
        date_str = trip.get('date') or trip.get('travel_date')

        try:
            activity_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        except Exception:
            activity_date = None

        flag_parts = []

        if trip_type == 'flight':
            origin = trip.get('origin', '')
            dest = trip.get('destination', '')
            cabin_raw = trip.get('cabin_class', 'economy').upper()
            if cabin_raw in ('J', 'C', 'BUSINESS', 'BUSINESS CLASS'):
                cabin = 'business'
            elif cabin_raw in ('F', 'P', 'FIRST', 'FIRST CLASS'):
                cabin = 'first'
            else:
                cabin = 'economy'
            travelers = int(trip.get('travelers', 1))

            km, dist_flag = get_flight_distance(origin, dest)
            if dist_flag:
                flag_parts.append(dist_flag)

            if km:
                factor = FLIGHT_FACTORS.get(cabin, FLIGHT_FACTORS['unknown'])
                kgco2e = km * factor * travelers
            else:
                kgco2e = None
                flag_parts.append("Distance unknown — kgCO2e not calculated")

            records.append({
                'raw': trip,
                'scope': 3,
                'category': 'travel',
                'quantity_original': km or Decimal('0'),
                'unit_original': 'km',
                'quantity_normalized': km or Decimal('0'),
                'unit_normalized': 'km',
                'emission_factor': FLIGHT_FACTORS.get(cabin),
                'emission_factor_source': 'DEFRA 2023',
                'kgco2e': kgco2e,
                'activity_date': activity_date,
                'location': f"{origin} → {dest}",
                'description': f"{cabin} class, {travelers} traveler(s)",
                'flag': ' | '.join(flag_parts) if flag_parts else None,
            })

        elif trip_type == 'hotel':
            nights = int(trip.get('nights', 1))
            kgco2e = HOTEL_FACTOR * nights
            records.append({
                'raw': trip,
                'scope': 3,
                'category': 'travel',
                'quantity_original': Decimal(nights),
                'unit_original': 'nights',
                'quantity_normalized': Decimal(nights),
                'unit_normalized': 'nights',
                'emission_factor': HOTEL_FACTOR,
                'emission_factor_source': 'DEFRA 2023',
                'kgco2e': kgco2e,
                'activity_date': activity_date,
                'location': trip.get('city', ''),
                'description': trip.get('hotel_name', ''),
                'flag': None,
            })

        elif trip_type == 'ground':
            km = Decimal(str(trip.get('distance_km', 0)))
            kgco2e = km * GROUND_FACTOR
            records.append({
                'raw': trip,
                'scope': 3,
                'category': 'travel',
                'quantity_original': km,
                'unit_original': 'km',
                'quantity_normalized': km,
                'unit_normalized': 'km',
                'emission_factor': GROUND_FACTOR,
                'emission_factor_source': 'DEFRA 2023',
                'kgco2e': kgco2e,
                'activity_date': activity_date,
                'location': trip.get('city', ''),
                'description': 'Ground transport',
                'flag': None if km > 0 else 'Distance is 0 — verify',
            })
        else:
            errors.append((i, f"Unknown trip type: {trip_type}"))

    return records, errors
