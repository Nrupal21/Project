"""
Geolocation utilities for the Guides application.

This module provides helper functions for working with geographical locations,
including distance calculations between points on Earth.
"""
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth specified in decimal degrees.
    
    Args:
        lat1, lon1: Latitude and Longitude of point 1 (in decimal degrees)
        lat2, lon2: Latitude and Longitude of point 2 (in decimal degrees)
        
    Returns:
        float: Distance between the two points in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    # Radius of Earth in kilometers
    R = 6371.0
    return R * c
