"""
Serializers for the destinations app.

This module defines serializers for converting destination models
to JSON and handling API requests related to destinations.

Serializers are responsible for:
1. Converting Django models to JSON format for API responses (serialization)
2. Converting JSON data to Django models for API requests (deserialization)
3. Validating incoming data before saving to the database
4. Defining relationships between different models in the API output

These serializers work with the ViewSets in views.py to provide a complete
REST API implementation for the destinations app.
"""

from rest_framework import serializers
from .models import Region, Destination, DestinationImage, Season, Attraction


class RegionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Region model.
    
    Converts Region model instances to JSON format for API responses
    and validates incoming data for API requests.
    """
    class Meta:
        """
        Meta class for RegionSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = Region
        fields = ['id', 'name', 'slug', 'description', 'image']


class DestinationImageSerializer(serializers.ModelSerializer):
    """
    Serializer for the DestinationImage model.
    
    Handles image data related to destinations for API responses.
    """
    class Meta:
        """
        Meta class for DestinationImageSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = DestinationImage
        fields = ['id', 'image', 'caption', 'is_primary', 'order']


class SeasonSerializer(serializers.ModelSerializer):
    """
    Serializer for the Season model.
    
    Converts Season model instances to JSON format for API responses.
    """
    class Meta:
        """
        Meta class for SeasonSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = Season
        fields = ['id', 'name', 'start_month', 'end_month', 'description', 'is_peak']


class AttractionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Attraction model.
    
    Converts Attraction model instances to JSON format for API responses.
    This serializer is used by the AttractionViewSet to handle CRUD operations
    via the REST API. It provides a representation of tourist attractions
    at destinations including location data and contact information.
    
    Key use cases:
    - Listing attractions at a specific destination
    - Retrieving detailed information about a single attraction
    - Creating new attractions through the API
    - Updating existing attraction information
    
    Note that this serializer does not include the destination field directly,
    but the destination can be filtered in the ViewSet using query parameters.
    """
    class Meta:
        """
        Meta class for AttractionSerializer.
        
        Defines the model and fields to include in the serialized representation.
        
        Fields explanation:
        - id: Primary key identifier for the attraction
        - name: Name of the attraction
        - description: Detailed text description of the attraction
        - address: Physical address where the attraction is located
        - latitude: Geographic coordinate for mapping (north-south position)
        - longitude: Geographic coordinate for mapping (east-west position)
        - website: URL to the attraction's official website if available
        - image: Primary image representing the attraction
        """
        model = Attraction
        fields = ['id', 'name', 'description', 'address', 'latitude', 'longitude', 'website', 'image']


class DestinationListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Destination instances.
    
    Provides a simplified representation for list views.
    """
    primary_image = serializers.SerializerMethodField()
    region_name = serializers.CharField(source='region.name', read_only=True)
    
    def get_primary_image(self, obj):
        """
        Get the primary image URL for the destination.
        
        Returns URL of primary image or first available image,
        or None if no images exist.
        
        Args:
            obj: The Destination instance
            
        Returns:
            str: URL of the destination's primary image or None
        """
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image.url
        
        # Fallback to first image
        first_image = obj.images.first()
        if first_image:
            return first_image.image.url
        
        return None
    
    class Meta:
        """
        Meta class for DestinationListSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = Destination
        fields = [
            'id', 'name', 'slug', 'city', 'country', 'primary_image',
            'latitude', 'longitude', 'region_name', 'short_description', 
            'rating', 'price', 'featured'
        ]


class DestinationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed Destination information.
    
    Provides a complete representation including related data
    for detail views.
    """
    images = DestinationImageSerializer(many=True, read_only=True)
    region = RegionSerializer(read_only=True)
    seasons = SeasonSerializer(many=True, read_only=True)
    attractions = AttractionSerializer(many=True, read_only=True)
    
    class Meta:
        """
        Meta class for DestinationDetailSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = Destination
        fields = [
            'id', 'name', 'slug', 'city', 'country', 'region',
            'description', 'short_description', 'latitude', 'longitude',
            'rating', 'price', 'currency', 'featured', 'images',
            'seasons', 'attractions', 'tips', 'created_at', 'updated_at'
        ]


class NearbyDestinationSerializer(serializers.ModelSerializer):
    """
    Serializer for nearby destinations.
    
    Includes distance information in addition to destination details.
    """
    distance = serializers.FloatField()
    image_url = serializers.SerializerMethodField()
    
    def get_image_url(self, obj):
        """
        Get the primary image URL for the destination.
        
        Returns URL of primary image or first available image,
        or None if no images exist.
        
        Args:
            obj: The Destination instance
            
        Returns:
            str: URL of the destination's primary image or None
        """
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image.url
        
        # Fallback to first image
        first_image = obj.images.first()
        if first_image:
            return first_image.image.url
        
        return None
    
    class Meta:
        """
        Meta class for NearbyDestinationSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = Destination
        fields = [
            'id', 'name', 'slug', 'city', 'country', 'latitude', 'longitude',
            'short_description', 'rating', 'price', 'image_url', 'distance'
        ]
