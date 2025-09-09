from math import radians, cos, sin, asin, sqrt

# TODO: implement OSMNX distance calculation option and show maps

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    Returns distance in kilometers.
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers.
    return c * r


def km_to_miles(kilometers):
    """
    Convert kilometers to miles.
    
    Args:
        kilometers (float): Distance in kilometers
        
    Returns:
        float: Distance in miles
    """
    return kilometers * 0.621371


def miles_to_km(miles):
    """
    Convert miles to kilometers.
    
    Args:
        miles (float): Distance in miles
        
    Returns:
        float: Distance in kilometers
    """
    return miles * 1.60934


def mph_to_kmh(mph):
    """
    Convert miles per hour to kilometers per hour.
    
    Args:
        mph (float): Speed in miles per hour
        
    Returns:
        float: Speed in kilometers per hour
    """
    return mph * 1.60934


def kmh_to_mph(kmh):
    """
    Convert kilometers per hour to miles per hour.
    
    Args:
        kmh (float): Speed in kilometers per hour
        
    Returns:
        float: Speed in miles per hour
    """
    return kmh * 0.621371


def calculate_time_hours(distance_km, speed_kmh):
    """
    Calculate travel time in hours.
    
    Args:
        distance_km (float): Distance in kilometers
        speed_kmh (float): Speed in kilometers per hour
        
    Returns:
        float: Travel time in hours
    """
    return distance_km / speed_kmh


def calculate_time_hours_from_miles(distance_miles, speed_mph):
    """
    Calculate travel time in hours from miles and mph.
    
    Args:
        distance_miles (float): Distance in miles
        speed_mph (float): Speed in miles per hour
        
    Returns:
        float: Travel time in hours
    """
    return distance_miles / speed_mph
