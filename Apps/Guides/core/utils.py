"""
Core utility functions for the TravelGuide application.

This module provides shared utility functions that are used across multiple apps
to ensure consistent behavior and reduce code duplication. It includes functions
for data validation, formatting, caching, and common business logic operations.

Key Features:
- Location-based calculations using Haversine formula
- Data validation and sanitization utilities
- Caching helpers for improved performance
- Common formatting functions for consistent display
- Error handling utilities for robust operation
"""

import logging
import hashlib
from math import radians, sin, cos, sqrt, atan2
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, InvalidOperation
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from django.conf import settings

# Configure logger for this module
logger = logging.getLogger(__name__)

# Constants for geographical calculations
EARTH_RADIUS_KM = 6371.0  # Earth's radius in kilometers
DEFAULT_SEARCH_RADIUS = 15  # Default search radius in kilometers
MAX_SEARCH_RADIUS = 100  # Maximum allowed search radius in kilometers


class LocationUtils:
    """
    Utility class for location-based calculations and operations.
    
    This class provides methods for calculating distances between coordinates,
    finding nearby locations, and validating geographical data.
    """
    
    @staticmethod
    def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate the great-circle distance between two points on Earth using Haversine formula.
        
        This method calculates the shortest distance between two points on the surface
        of a sphere (Earth) given their latitude and longitude coordinates.
        
        Args:
            lat1 (float): Latitude of the first point in decimal degrees
            lng1 (float): Longitude of the first point in decimal degrees
            lat2 (float): Latitude of the second point in decimal degrees
            lng2 (float): Longitude of the second point in decimal degrees
            
        Returns:
            float: Distance between the two points in kilometers
            
        Example:
            >>> distance = LocationUtils.calculate_distance(40.7128, -74.0060, 34.0522, -118.2437)
            >>> print(f"Distance: {distance:.2f} km")
        """
        try:
            # Convert latitude and longitude from degrees to radians
            lat1_rad = radians(lat1)
            lng1_rad = radians(lng1)
            lat2_rad = radians(lat2)
            lng2_rad = radians(lng2)
            
            # Calculate differences
            dlat = lat2_rad - lat1_rad
            dlng = lng2_rad - lng1_rad
            
            # Apply Haversine formula
            a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlng/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            
            # Calculate distance
            distance = EARTH_RADIUS_KM * c
            
            logger.debug(f"Calculated distance: {distance:.2f} km between ({lat1}, {lng1}) and ({lat2}, {lng2})")
            return distance
            
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return float('inf')  # Return infinity on error to indicate invalid distance
    
    @staticmethod
    def get_bounding_box(lat: float, lng: float, radius_km: float) -> Tuple[float, float, float, float]:
        """
        Calculate bounding box coordinates for a given center point and radius.
        
        This method calculates the minimum and maximum latitude and longitude
        values that form a rectangular bounding box around a center point.
        This is useful for optimizing database queries by filtering locations
        within a rectangular area before applying more precise distance calculations.
        
        Args:
            lat (float): Center latitude in decimal degrees
            lng (float): Center longitude in decimal degrees
            radius_km (float): Radius in kilometers
            
        Returns:
            Tuple[float, float, float, float]: (min_lat, max_lat, min_lng, max_lng)
        """
        try:
            # Convert to radians for calculation
            lat_rad = radians(lat)
            
            # Calculate latitude range (approximately 111 km per degree)
            lat_range = radius_km / 111.0
            
            # Calculate longitude range (varies with latitude)
            lng_range = radius_km / (111.0 * cos(lat_rad))
            
            min_lat = lat - lat_range
            max_lat = lat + lat_range
            min_lng = lng - lng_range
            max_lng = lng + lng_range
            
            logger.debug(f"Bounding box for ({lat}, {lng}) with radius {radius_km}km: "
                        f"lat[{min_lat:.6f}, {max_lat:.6f}], lng[{min_lng:.6f}, {max_lng:.6f}]")
            
            return min_lat, max_lat, min_lng, max_lng
            
        except Exception as e:
            logger.error(f"Error calculating bounding box: {e}")
            return lat, lat, lng, lng  # Return point coordinates on error
    
    @staticmethod
    def validate_coordinates(lat: float, lng: float) -> bool:
        """
        Validate latitude and longitude coordinates.
        
        This method checks if the provided coordinates are within valid ranges:
        - Latitude: -90 to 90 degrees
        - Longitude: -180 to 180 degrees
        
        Args:
            lat (float): Latitude to validate
            lng (float): Longitude to validate
            
        Returns:
            bool: True if coordinates are valid, False otherwise
        """
        try:
            return (-90 <= lat <= 90) and (-180 <= lng <= 180)
        except (TypeError, ValueError):
            return False


class CacheUtils:
    """
    Utility class for caching operations and cache key management.
    
    This class provides methods for generating consistent cache keys,
    managing cache expiration, and implementing common caching patterns.
    """
    
    # Cache timeout constants (in seconds)
    CACHE_TIMEOUT_SHORT = 300      # 5 minutes
    CACHE_TIMEOUT_MEDIUM = 1800    # 30 minutes
    CACHE_TIMEOUT_LONG = 3600      # 1 hour
    CACHE_TIMEOUT_DAILY = 86400    # 24 hours
    
    @staticmethod
    def generate_cache_key(*args, prefix: str = 'travelguide') -> str:
        """
        Generate a consistent cache key from the provided arguments.
        
        This method creates a cache key by combining a prefix with the
        provided arguments and generating a hash for uniqueness.
        
        Args:
            *args: Variable arguments to include in the cache key
            prefix (str): Prefix for the cache key (default: 'travelguide')
            
        Returns:
            str: Generated cache key
            
        Example:
            >>> key = CacheUtils.generate_cache_key('destinations', 'nearby', 40.7128, -74.0060)
            >>> print(key)  # 'travelguide:destinations:nearby:a1b2c3d4...'
        """
        try:
            # Convert all arguments to strings and join them
            key_parts = [str(arg) for arg in args]
            key_string = ':'.join(key_parts)
            
            # Generate hash for long keys to ensure consistent length
            if len(key_string) > 200:
                key_hash = hashlib.md5(key_string.encode()).hexdigest()
                return f"{prefix}:hash:{key_hash}"
            else:
                return f"{prefix}:{key_string}"
                
        except Exception as e:
            logger.error(f"Error generating cache key: {e}")
            # Return a fallback key based on timestamp
            return f"{prefix}:fallback:{timezone.now().timestamp()}"
    
    @staticmethod
    def get_or_set_cache(key: str, callable_func, timeout: int = None, *args, **kwargs):
        """
        Get value from cache or set it by calling the provided function.
        
        This method implements the common caching pattern of checking the cache
        first, and if the value is not found, calling a function to generate
        the value and storing it in the cache.
        
        Args:
            key (str): Cache key to use
            callable_func: Function to call if cache miss occurs
            timeout (int): Cache timeout in seconds
            *args: Arguments to pass to the callable function
            **kwargs: Keyword arguments to pass to the callable function
            
        Returns:
            Any: Cached value or result from callable function
        """
        if timeout is None:
            timeout = CacheUtils.CACHE_TIMEOUT_MEDIUM
            
        try:
            # Try to get value from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {key}")
                return cached_value
            
            # Cache miss - call function and cache result
            logger.debug(f"Cache miss for key: {key}, calling function")
            result = callable_func(*args, **kwargs)
            
            # Store in cache
            cache.set(key, result, timeout)
            return result
            
        except Exception as e:
            logger.error(f"Error in cache operation for key {key}: {e}")
            # Fallback to calling function directly
            return callable_func(*args, **kwargs)


class DataValidationUtils:
    """
    Utility class for data validation and sanitization.
    
    This class provides methods for validating and sanitizing various types
    of data commonly used in the travel guide application.
    """
    
    @staticmethod
    def validate_rating(rating: Any) -> Optional[Decimal]:
        """
        Validate and convert a rating value to a proper Decimal.
        
        This method ensures that rating values are within the valid range
        (typically 0.0 to 5.0) and converts them to Decimal for precise storage.
        
        Args:
            rating (Any): Rating value to validate
            
        Returns:
            Optional[Decimal]: Validated rating as Decimal, or None if invalid
        """
        try:
            if rating is None:
                return None
                
            # Convert to Decimal
            rating_decimal = Decimal(str(rating))
            
            # Validate range (0.0 to 5.0)
            if 0 <= rating_decimal <= 5:
                return rating_decimal.quantize(Decimal('0.1'))  # Round to 1 decimal place
            else:
                logger.warning(f"Rating {rating} is outside valid range (0-5)")
                return None
                
        except (ValueError, TypeError, InvalidOperation) as e:
            logger.error(f"Error validating rating {rating}: {e}")
            return None
    
    @staticmethod
    def validate_price(price: Any) -> Optional[Decimal]:
        """
        Validate and convert a price value to a proper Decimal.
        
        This method ensures that price values are positive and converts
        them to Decimal for precise monetary calculations.
        
        Args:
            price (Any): Price value to validate
            
        Returns:
            Optional[Decimal]: Validated price as Decimal, or None if invalid
        """
        try:
            if price is None:
                return None
                
            # Convert to Decimal
            price_decimal = Decimal(str(price))
            
            # Validate that price is positive
            if price_decimal >= 0:
                return price_decimal.quantize(Decimal('0.01'))  # Round to 2 decimal places
            else:
                logger.warning(f"Price {price} is negative")
                return None
                
        except (ValueError, TypeError, InvalidOperation) as e:
            logger.error(f"Error validating price {price}: {e}")
            return None
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = None) -> str:
        """
        Sanitize text input by removing unwanted characters and limiting length.
        
        This method cleans text input by stripping whitespace, removing
        potentially harmful characters, and optionally limiting length.
        
        Args:
            text (str): Text to sanitize
            max_length (int, optional): Maximum allowed length
            
        Returns:
            str: Sanitized text
        """
        try:
            if not isinstance(text, str):
                text = str(text)
                
            # Strip whitespace
            text = text.strip()
            
            # Remove null bytes and control characters
            text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
            
            # Limit length if specified
            if max_length and len(text) > max_length:
                text = text[:max_length].rstrip()
                
            return text
            
        except Exception as e:
            logger.error(f"Error sanitizing text: {e}")
            return ""


# Convenience functions for common operations
def calculate_distance_between_points(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Convenience function for calculating distance between two geographical points.
    
    This is a wrapper around LocationUtils.calculate_distance for easier access.
    
    Args:
        lat1 (float): Latitude of the first point
        lng1 (float): Longitude of the first point
        lat2 (float): Latitude of the second point
        lng2 (float): Longitude of the second point
        
    Returns:
        float: Distance in kilometers
    """
    return LocationUtils.calculate_distance(lat1, lng1, lat2, lng2)


def generate_cache_key_for_location(lat: float, lng: float, radius: float, prefix: str = 'location') -> str:
    """
    Generate a cache key for location-based queries.
    
    This function creates a consistent cache key for location-based operations
    by combining coordinates and radius with proper rounding for cache efficiency.
    
    Args:
        lat (float): Latitude
        lng (float): Longitude
        radius (float): Search radius
        prefix (str): Cache key prefix
        
    Returns:
        str: Generated cache key
    """
    # Round coordinates to reduce cache key variations
    lat_rounded = round(lat, 4)
    lng_rounded = round(lng, 4)
    radius_rounded = round(radius, 1)
    
    return CacheUtils.generate_cache_key(prefix, lat_rounded, lng_rounded, radius_rounded)
