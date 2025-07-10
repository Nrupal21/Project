"""
Serializers for the destinations app.

This module contains serializers for converting model instances to JSON and back.
"""
from rest_framework import serializers
# GeoDjango Point import removed - using standard float fields for coordinates
from .models import (
    Region, Destination, DestinationImage, 
    Season, Attraction, AttractionImage
)

class RegionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Region model.
    
    Handles conversion of Region model instances to JSON and vice versa.
    """
    class Meta:
        model = Region
        fields = ['id', 'name', 'slug', 'description', 'image', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class DestinationImageSerializer(serializers.ModelSerializer):
    """
    Serializer for the DestinationImage model.
    
    Handles conversion of DestinationImage model instances to JSON and vice versa.
    """
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = DestinationImage
        fields = ['id', 'image', 'image_url', 'caption', 'is_primary', 'order', 'created_at']
        read_only_fields = ['created_at']
    
    def get_image_url(self, obj):
        """
        Get the absolute URL of the image.
        
        Args:
            obj: The DestinationImage instance
            
        Returns:
            str: Absolute URL of the image
        """
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

class SeasonSerializer(serializers.ModelSerializer):
    """
    Serializer for the Season model.
    
    Handles conversion of Season model instances to JSON and vice versa.
    """
    season_range = serializers.CharField(read_only=True)
    
    class Meta:
        model = Season
        fields = ['id', 'name', 'start_month', 'end_month', 'season_range', 
                 'description', 'average_temperature', 'is_peak_season']

class DestinationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Destination model.
    
    Handles conversion of Destination model instances to JSON and vice versa.
    Includes nested serializers for related models.
    """
    region = RegionSerializer(read_only=True)
    region_id = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(),
        source='region',
        write_only=True,
        required=False,
        allow_null=True
    )
    images = DestinationImageSerializer(many=True, read_only=True)
    seasons = SeasonSerializer(many=True, read_only=True)
    latitude = serializers.FloatField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="Latitude for the destination's location"
    )
    longitude = serializers.FloatField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="Longitude for the destination's location"
    )
    
    class Meta:
        model = Destination
        fields = [
            'id', 'name', 'slug', 'region', 'region_id', 'description', 'short_description',
            'latitude', 'longitude', 'address', 'city', 'country', 'postal_code', 'is_featured', 'is_active',
            'created_at', 'updated_at', 'images', 'seasons', 'latitude', 'longitude'
        ]
        read_only_fields = ['created_at', 'updated_at', 'slug']
    
    def validate(self, data):
        """
        Validate the destination data.
        
        Args:
            data (dict): The data to validate
            
        Returns:
            dict: The validated data
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Validate location if latitude and longitude are provided
        latitude = data.pop('latitude', None)
        longitude = data.pop('longitude', None)
        
        if latitude is not None and longitude is not None:
            try:
                data['location'] = Point(float(longitude), float(latitude), srid=4326)
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'location': 'Invalid latitude or longitude values.'
                })
        
        return data
    
    def create(self, validated_data):
        """
        Create a new Destination instance.
        
        Args:
            validated_data (dict): The validated data
            
        Returns:
            Destination: The created Destination instance
        """
        # Handle the case where region is passed as a nested object
        region = validated_data.pop('region', None)
        if region:
            validated_data['region'] = region
            
        return super().create(validated_data)

class AttractionImageSerializer(serializers.ModelSerializer):
    """
    Serializer for the AttractionImage model.
    
    Handles conversion of AttractionImage model instances to JSON and vice versa.
    """
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AttractionImage
        fields = ['id', 'image', 'image_url', 'caption', 'is_primary', 'order', 'created_at']
        read_only_fields = ['created_at']
    
    def get_image_url(self, obj):
        """
        Get the absolute URL of the image.
        
        Args:
            obj: The AttractionImage instance
            
        Returns:
            str: Absolute URL of the image
        """
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

class AttractionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Attraction model.
    
    Handles conversion of Attraction model instances to JSON and vice versa.
    Includes nested serializers for related models.
    """
    destination = serializers.PrimaryKeyRelatedField(queryset=Destination.objects.all())
    images = AttractionImageSerializer(many=True, read_only=True)
    latitude = serializers.FloatField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="Latitude for the attraction's location"
    )
    longitude = serializers.FloatField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="Longitude for the attraction's location"
    )
    
    class Meta:
        model = Attraction
        fields = [
            'id', 'name', 'destination', 'description', 'category',
            'address', 'location', 'opening_hours', 'entry_fee', 'website',
            'contact_phone', 'contact_email', 'is_featured', 'created_at',
            'updated_at', 'images', 'latitude', 'longitude'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        """
        Validate the attraction data.
        
        Args:
            data (dict): The data to validate
            
        Returns:
            dict: The validated data
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Validate location if latitude and longitude are provided
        latitude = data.pop('latitude', None)
        longitude = data.pop('longitude', None)
        
        if latitude is not None and longitude is not None:
            try:
                data['location'] = Point(float(longitude), float(latitude), srid=4326)
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'location': 'Invalid latitude or longitude values.'
                })
        
        return data

class DestinationDetailSerializer(DestinationSerializer):
    """
    Detailed serializer for the Destination model.
    
    Extends the basic DestinationSerializer to include more detailed information
    such as nearby attractions and extended details.
    """
    attractions = AttractionSerializer(many=True, read_only=True)
    
    class Meta(DestinationSerializer.Meta):
        fields = DestinationSerializer.Meta.fields + ['attractions']

class RegionDetailSerializer(RegionSerializer):
    """
    Detailed serializer for the Region model.
    
    Extends the basic RegionSerializer to include a list of destinations
    within the region.
    """
    destinations = DestinationSerializer(many=True, read_only=True)
    
    class Meta(RegionSerializer.Meta):
        fields = RegionSerializer.Meta.fields + ['destinations']
