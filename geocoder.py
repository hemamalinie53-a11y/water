"""
Production-ready geocoding module for Water Quality App.
Uses geopy Nominatim + RateLimiter only (no Google Maps API).
Includes fuzzy spell-correction for common city name typos.
"""

import re
import time
import hashlib
from difflib import get_close_matches
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable

# ── Country alias map ──────────────────────────────────────────────────────────
COUNTRY_ALIASES = {
    'uae': 'United Arab Emirates', 'uk': 'United Kingdom',
    'usa': 'United States',        'us': 'United States',
    'gb':  'United Kingdom',       'ksa': 'Saudi Arabia',
    'sa':  'Saudi Arabia',         'nz': 'New Zealand',
    'aus': 'Australia',            'can': 'Canada',
}

# ── Known country names (lowercase) ───────────────────────────────────────────
KNOWN_COUNTRIES = {
    'india','united arab emirates','uae','united kingdom','uk','united states',
    'usa','us','australia','canada','germany','france','japan','china',
    'singapore','malaysia','sri lanka','pakistan','bangladesh','nepal',
    'indonesia','thailand','south africa','brazil','mexico','italy','spain',
    'russia','saudi arabia','ksa','qatar','kuwait','bahrain','oman',
    'new zealand','philippines','vietnam','myanmar','cambodia','turkey',
    'egypt','nigeria','kenya','ghana','ethiopia','argentina','colombia',
    'chile','peru','portugal','netherlands','belgium','sweden','norway',
    'denmark','finland','switzerland','austria','poland','ukraine','greece',
    'iran','iraq','israel','jordan','lebanon','afghanistan','uzbekistan',
    'kazakhstan','taiwan','hong kong','maldives','bhutan','brunei',
    'morocco','algeria','tunisia','libya','sudan','somalia','tanzania',
    'uganda','rwanda','mozambique','zimbabwe','zambia','angola','cameroon',
    'senegal','cuba','haiti','jamaica','venezuela','ecuador','bolivia',
    'paraguay','uruguay','czech republic','slovakia','hungary','romania',
    'bulgaria','serbia','croatia','slovenia','moldova','belarus',
    'latvia','lithuania','estonia','armenia','georgia','azerbaijan',
    'south korea','north korea','mongolia','laos',
}

# ── Names that are both country AND city ──────────────────────────────────────
COUNTRY_CITY_NAMES = {
    'singapore','luxembourg','monaco','kuwait','bahrain','qatar',
    'djibouti','panama','andorra','san marino','maldives','hong kong',
    'macau','taiwan',
}

# ── Indian states ─────────────────────────────────────────────────────────────
INDIAN_STATES = {
    'andhra pradesh','arunachal pradesh','assam','bihar','chhattisgarh',
    'goa','gujarat','haryana','himachal pradesh','jharkhand','karnataka',
    'kerala','madhya pradesh','maharashtra','manipur','meghalaya','mizoram',
    'nagaland','odisha','punjab','rajasthan','sikkim','tamil nadu','telangana',
    'tripura','uttar pradesh','uttarakhand','west bengal','andaman and nicobar',
    'chandigarh','dadra and nagar haveli','daman and diu','delhi',
    'jammu and kashmir','ladakh','lakshadweep','puducherry','pondicherry',
}

DEFAULT_COUNTRY = 'India'

# ── Coordinate overrides for cities where Nominatim returns district centroid ─
# Format: lowercase city name → (lat, lon, display_address)
CITY_OVERRIDES = {
    'ramanathapuram':           (9.365235,  78.834319, 'Ramanathapuram, Tamil Nadu, India'),
    'ramanathapuram, india':    (9.365235,  78.834319, 'Ramanathapuram, Tamil Nadu, India'),
    'ramanathapuram, tamil nadu': (9.365235, 78.834319, 'Ramanathapuram, Tamil Nadu, India'),
    'ramanathapuram, tamil nadu, india': (9.365235, 78.834319, 'Ramanathapuram, Tamil Nadu, India'),
    'kilakarai':                (9.234662,  78.786032, 'Kilakarai, Ramanathapuram, Tamil Nadu, India'),
    'kilakarai, india':         (9.234662,  78.786032, 'Kilakarai, Ramanathapuram, Tamil Nadu, India'),
    'kilakarai, tamil nadu':    (9.234662,  78.786032, 'Kilakarai, Ramanathapuram, Tamil Nadu, India'),
    'kilakarai, tamil nadu, india': (9.234662, 78.786032, 'Kilakarai, Ramanathapuram, Tamil Nadu, India'),
}

# ── Known city names for fuzzy spell correction ───────────────────────────────
# Only city part (before comma) — used for typo matching
KNOWN_CITIES = [
    # Tamil Nadu
    'Salem', 'Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli', 'Tirunelveli',
    'Vellore', 'Erode', 'Thoothukudi', 'Dindigul', 'Thanjavur', 'Ranipet',
    'Sivakasi', 'Karur', 'Ooty', 'Ramanathapuram', 'Theni', 'Virudhunagar',
    'Namakkal', 'Krishnagiri', 'Dharmapuri', 'Cuddalore', 'Nagapattinam',
    'Kancheepuram', 'Tiruppur', 'Hosur', 'Kumbakonam', 'Kilakarai',
    # Other Indian cities
    'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Kolkata', 'Pune', 'Ahmedabad',
    'Jaipur', 'Surat', 'Lucknow', 'Nagpur', 'Indore', 'Bhopal', 'Patna',
    'Vadodara', 'Ludhiana', 'Agra', 'Nashik', 'Faridabad', 'Meerut',
    'Rajkot', 'Varanasi', 'Srinagar', 'Aurangabad', 'Dhanbad', 'Amritsar',
    'Allahabad', 'Ranchi', 'Howrah', 'Jabalpur', 'Gwalior', 'Vijayawada',
    'Jodhpur', 'Madurai', 'Raipur', 'Kota', 'Chandigarh', 'Guwahati',
    'Solapur', 'Hubli', 'Mysore', 'Tiruchirappalli', 'Bareilly', 'Aligarh',
    'Moradabad', 'Jalandhar', 'Bhubaneswar', 'Noida', 'Gurgaon', 'Kochi',
    'Thiruvananthapuram', 'Kozhikode', 'Thrissur', 'Mangalore', 'Shimla',
    # International
    'Dubai', 'Abu Dhabi', 'Riyadh', 'Doha', 'Kuwait', 'Muscat',
    'Singapore', 'Kuala Lumpur', 'Bangkok', 'Jakarta', 'Colombo',
    'Dhaka', 'Kathmandu', 'Tokyo', 'Beijing', 'Seoul', 'Shanghai',
    'London', 'Paris', 'Berlin', 'Rome', 'Madrid', 'Amsterdam', 'Moscow',
    'New York', 'Los Angeles', 'Toronto', 'Sydney', 'Melbourne',
    'Cairo', 'Lagos', 'Nairobi', 'Sao Paulo', 'Buenos Aires',
]


def fuzzy_correct_city(user_input: str) -> tuple:
    """
    Attempt to fuzzy-correct the city part of a location string.

    Returns:
        (corrected_input: str, was_corrected: bool, suggestion: str | None)
    """
    raw    = user_input.strip()
    parts  = [p.strip() for p in raw.split(',')]
    city   = parts[0]

    # Try to find a close match for the city name
    matches = get_close_matches(city, KNOWN_CITIES, n=1, cutoff=0.75)

    if matches and matches[0].lower() != city.lower():
        corrected_city = matches[0]
        # Rebuild full string with corrected city
        parts[0] = corrected_city
        corrected = ', '.join(parts)
        return corrected, True, corrected_city

    return raw, False, None

# ── Common location suggestions shown in UI ───────────────────────────────────
COMMON_LOCATIONS = [
    "-- Type your own --",
    # India
    "Salem, India", "Chennai, India", "Mumbai, India", "Delhi, India",
    "Bangalore, India", "Hyderabad, India", "Kolkata, India",
    "Coimbatore, India", "Madurai, India", "Kochi, Kerala, India",
    "Ooty, Tamil Nadu, India", "Jaipur, India", "Ahmedabad, India",
    "Pune, India", "Surat, India", "Lucknow, India", "Nagpur, India",
    "Ramanathapuram, India", "Sivakasi, India", "Theni, India",
    # Middle East
    "Dubai, UAE", "Abu Dhabi, UAE", "Riyadh, Saudi Arabia",
    "Doha, Qatar", "Kuwait City, Kuwait", "Muscat, Oman",
    # Asia
    "Singapore", "Kuala Lumpur, Malaysia", "Bangkok, Thailand",
    "Jakarta, Indonesia", "Colombo, Sri Lanka", "Dhaka, Bangladesh",
    "Kathmandu, Nepal", "Tokyo, Japan", "Beijing, China", "Seoul, South Korea",
    # Europe
    "London, UK", "Paris, France", "Berlin, Germany", "Rome, Italy",
    "Madrid, Spain", "Amsterdam, Netherlands", "Moscow, Russia",
    # Americas
    "New York, USA", "Los Angeles, USA", "Toronto, Canada",
    "Sao Paulo, Brazil", "Buenos Aires, Argentina",
    # Africa / Oceania
    "Cairo, Egypt", "Lagos, Nigeria", "Nairobi, Kenya",
    "Sydney, Australia", "Melbourne, Australia",
]


def _uid() -> str:
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:12]


def _make_geocoder():
    """Create Nominatim + RateLimiter (max 1 req/sec, 2 retries)."""
    geolocator = Nominatim(user_agent=f"wq_app_{_uid()}", timeout=10)
    return RateLimiter(
        geolocator.geocode,
        min_delay_seconds=1.1,
        max_retries=2,
        error_wait_seconds=3.0,
        swallow_exceptions=False,
    )


def _norm(s: str) -> str:
    return s.strip().lower()


def _resolve_alias(s: str) -> str:
    return COUNTRY_ALIASES.get(_norm(s), s.strip())


def _is_country(s: str) -> bool:
    return _norm(s) in KNOWN_COUNTRIES

def _is_country_city(s: str) -> bool:
    return _norm(s) in COUNTRY_CITY_NAMES

def _is_indian_state(s: str) -> bool:
    return _norm(s) in INDIAN_STATES


def _build_queries(user_input: str) -> list:
    """Build ordered plain-string query list (most → least specific)."""
    raw   = user_input.strip()
    parts = [p.strip() for p in raw.split(',') if p.strip()]
    n     = len(parts)
    queries = []

    if n == 0:
        return []

    if n == 1:
        token = parts[0]
        if _is_country_city(token) or _is_country(token):
            queries += [token]
        else:
            queries += [f"{token}, {DEFAULT_COUNTRY}", token]

    elif n == 2:
        city, second = parts[0], parts[1]
        resolved = _resolve_alias(second)
        if _is_country(second) or resolved != second.strip():
            queries += [f"{city}, {resolved}", f"{city}, {second}", raw]
        elif _is_indian_state(second):
            queries += [
                f"{city}, {second}, {DEFAULT_COUNTRY}",
                f"{city}, {DEFAULT_COUNTRY}", raw,
            ]
        else:
            queries += [
                f"{city}, {resolved}",
                f"{city}, {second}, {DEFAULT_COUNTRY}",
                f"{city}, {DEFAULT_COUNTRY}", raw,
            ]

    elif n == 3:
        city, state, country_raw = parts[0], parts[1], parts[2]
        country = _resolve_alias(country_raw)
        queries += [
            f"{city}, {state}, {country}",
            f"{city}, {country}", raw,
        ]

    else:
        queries += [raw, ', '.join(parts[-3:]), ', '.join(parts[-2:])]

    # Deduplicate
    seen, result = set(), []
    for q in queries:
        if q not in seen:
            seen.add(q)
            result.append(q)
    return result


def geocode_location(user_input: str) -> dict:
    """
    Geocode any location string using Nominatim + RateLimiter.

    Returns:
        {
            'success':   bool,
            'latitude':  float | None,
            'longitude': float | None,
            'address':   str | None,
            'error':     str | None,
        }
    """
    raw = user_input.strip()
    if not raw:
        return {
            'success': False, 'latitude': None, 'longitude': None,
            'address': None, 'error': 'Empty input. Please enter a location.',
            'corrected': None,
        }

    # ── Fuzzy spell correction ─────────────────────────────────────────────────
    corrected_input, was_corrected, suggestion = fuzzy_correct_city(raw)
    geocode_input = corrected_input   # use corrected version for geocoding

    # ── Check coordinate overrides first ──────────────────────────────────────
    override_key = corrected_input.strip().lower()
    if override_key in CITY_OVERRIDES:
        lat, lon, addr = CITY_OVERRIDES[override_key]
        return {
            'success':    True,
            'latitude':   lat,
            'longitude':  lon,
            'address':    addr,
            'error':      None,
            'corrected':  suggestion if was_corrected else None,
            'used_input': corrected_input,
        }

    geocode  = _make_geocoder()
    queries  = _build_queries(geocode_input)
    last_err = None

    for query in queries:
        try:
            result = geocode(query, exactly_one=True, language='en')
            if result:
                return {
                    'success':   True,
                    'latitude':  result.latitude,
                    'longitude': result.longitude,
                    'address':   result.address,
                    'error':     None,
                    'corrected': suggestion if was_corrected else None,
                    'used_input': geocode_input,
                }
        except GeocoderTimedOut:
            last_err = 'Request timed out.'
            # Retry once with a fresh geocoder
            try:
                time.sleep(2)
                retry = _make_geocoder()
                result = retry(query, exactly_one=True, language='en')
                if result:
                    return {
                        'success':   True,
                        'latitude':  result.latitude,
                        'longitude': result.longitude,
                        'address':   result.address,
                        'error':     None,
                        'corrected': suggestion if was_corrected else None,
                        'used_input': geocode_input,
                    }
            except Exception as e:
                last_err = str(e)
        except (GeocoderServiceError, GeocoderUnavailable) as e:
            last_err = f'Geocoding service error: {e}'
            time.sleep(3)
        except Exception as e:
            last_err = str(e)

    return {
        'success':    False,
        'latitude':   None,
        'longitude':  None,
        'address':    None,
        'corrected':  None,
        'used_input': geocode_input,
        'error': (
            f"Location '{raw}' not found. "
            "Please enter a full address like 'City, Country' — e.g. 'Salem, India' or 'Dubai, UAE'"
        ),
    }
