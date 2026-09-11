import math

CITY_COORDINATES = {
    "Ramallah": (31.9038, 35.2034),
    "Nablus": (32.2226, 35.2621),
    "Hebron": (31.5326, 35.0998),
    "Jericho": (31.8611, 35.4618),
}

def verify_location(city: str, reported_lat: float, reported_lon: float, max_radius_km: float = 15.0) -> str:
    if city not in CITY_COORDINATES:
        return "UNKNOWN_LOCATION"
    
    city_lat, city_lon = CITY_COORDINATES[city]
    
    dlat = math.radians(reported_lat - city_lat)
    dlon = math.radians(reported_lon - city_lon)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(city_lat)) * math.cos(math.radians(reported_lat)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance_km = 6371 * c

    return "VERIFIED" if distance_km <= max_radius_km else "LOCATION_MISMATCH"
