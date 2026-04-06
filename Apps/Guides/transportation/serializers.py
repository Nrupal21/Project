"""
Serializers for the transportation app.

This module defines serializers for transportation models, allowing 
conversion between Python objects and JSON representations for the API.
"""

from rest_framework import serializers
from destinations.serializers import DestinationListSerializer
from .models import (
    TransportationType, TransportationProvider, Route,
    Schedule, TransportationOption, TransportationImage
)


class TransportationImageSerializer(serializers.ModelSerializer):
    """
    Serializer for TransportationImage model.
    
    Handles serialization of transportation images with their metadata.
    """
    image_url = serializers.SerializerMethodField()
    
    def get_image_url(self, obj):
        """
        Get the absolute URL for the image.
        
        Args:
            obj: The TransportationImage instance
            
        Returns:
            str: The absolute URL for the image or None
        """
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None
    
    class Meta:
        """
        Meta class for TransportationImageSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = TransportationImage
        fields = [
            'id', 'image', 'image_url', 'alt_text', 'caption',
            'is_primary', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'image_url']


class TransportationTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for TransportationType model.
    
    Converts transportation types to/from JSON for API responses.
    """
    icon_url = serializers.SerializerMethodField()
    
    def get_icon_url(self, obj):
        """
        Get the absolute URL for the icon.
        
        Args:
            obj: The TransportationType instance
            
        Returns:
            str: The absolute URL for the icon or None
        """
        request = self.context.get('request')
        if request and obj.icon:
            return request.build_absolute_uri(obj.icon.url)
        return None
    
    class Meta:
        """
        Meta class for TransportationTypeSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = TransportationType
        fields = [
            'id', 'name', 'slug', 'icon', 'icon_url',
            'description', 'is_public', 'is_active'
        ]
        read_only_fields = ['id', 'slug', 'icon_url']


class TransportationProviderListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing TransportationProvider instances.
    
    Provides a condensed representation of providers for list views.
    """
    logo_url = serializers.SerializerMethodField()
    transportation_types = TransportationTypeSerializer(many=True, read_only=True)
    
    def get_logo_url(self, obj):
        """
        Get the absolute URL for the provider logo.
        
        Args:
            obj: The TransportationProvider instance
            
        Returns:
            str: The absolute URL for the logo or None
        """
        request = self.context.get('request')
        if request and obj.logo:
            return request.build_absolute_uri(obj.logo.url)
        return None
    
    class Meta:
        """
        Meta class for TransportationProviderListSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = TransportationProvider
        fields = [
            'id', 'name', 'slug', 'logo', 'logo_url',
            'transportation_types', 'is_partner', 'is_active'
        ]
        read_only_fields = ['id', 'slug', 'logo_url']


class TransportationProviderDetailSerializer(TransportationProviderListSerializer):
    """
    Detailed serializer for TransportationProvider.
    
    Extends the list serializer with additional fields for detail views.
    """
    images = serializers.SerializerMethodField()
    
    def get_images(self, obj):
        """
        Get related images for the transportation provider.
        
        Args:
            obj: The TransportationProvider instance
            
        Returns:
            list: Serialized transportation images
        """
        # Import ContentType here to avoid circular import
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(TransportationProvider)
        images = TransportationImage.objects.filter(
            content_type=content_type,
            object_id=obj.id
        )
        
        return TransportationImageSerializer(
            images, 
            many=True, 
            context=self.context
        ).data
    
    class Meta(TransportationProviderListSerializer.Meta):
        """
        Meta class for TransportationProviderDetailSerializer.
        
        Extends the parent Meta class with additional fields.
        """
        fields = TransportationProviderListSerializer.Meta.fields + [
            'website', 'phone_number', 'email', 'description', 'images'
        ]


class RouteListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Route instances.
    
    Provides a condensed representation of routes for list views.
    """
    origin_name = serializers.CharField(source='origin.name', read_only=True)
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    transportation_types = TransportationTypeSerializer(many=True, read_only=True)
    
    class Meta:
        """
        Meta class for RouteListSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = Route
        fields = [
            'id', 'name', 'slug', 'origin', 'origin_name',
            'destination', 'destination_name', 'transportation_types',
            'distance_km', 'is_popular', 'is_active'
        ]
        read_only_fields = ['id', 'slug']


class RouteDetailSerializer(RouteListSerializer):
    """
    Detailed serializer for Route.
    
    Extends the list serializer with additional fields for detail views.
    """
    providers = TransportationProviderListSerializer(many=True, read_only=True)
    origin = DestinationListSerializer(read_only=True)
    destination = DestinationListSerializer(read_only=True)
    images = serializers.SerializerMethodField()
    
    def get_images(self, obj):
        """
        Get related images for the route.
        
        Args:
            obj: The Route instance
            
        Returns:
            list: Serialized transportation images
        """
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(Route)
        images = TransportationImage.objects.filter(
            content_type=content_type,
            object_id=obj.id
        )
        
        return TransportationImageSerializer(
            images, 
            many=True, 
            context=self.context
        ).data
    
    class Meta(RouteListSerializer.Meta):
        """
        Meta class for RouteDetailSerializer.
        
        Extends the parent Meta class with additional fields.
        """
        fields = RouteListSerializer.Meta.fields + [
            'providers', 'typical_duration', 'description',
            'images', 'created_at', 'updated_at'
        ]
        read_only_fields = RouteListSerializer.Meta.read_only_fields + [
            'created_at', 'updated_at'
        ]


class ScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for Schedule model.
    
    Converts schedule information to/from JSON with related entities.
    """
    route_name = serializers.CharField(source='route.name', read_only=True)
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    transportation_type_name = serializers.CharField(
        source='transportation_type.name', 
        read_only=True
    )
    
    class Meta:
        """
        Meta class for ScheduleSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = Schedule
        fields = [
            'id', 'route', 'route_name', 'provider', 'provider_name',
            'transportation_type', 'transportation_type_name',
            'departure_time', 'arrival_time', 'days_of_week',
            'is_daily', 'price_economy', 'price_business',
            'has_wifi', 'has_power_outlets', 'has_meal_service',
            'notes', 'booking_url', 'is_active'
        ]
        read_only_fields = ['id']


class ScheduleDetailSerializer(ScheduleSerializer):
    """
    Detailed serializer for Schedule.
    
    Extends the base serializer with additional fields for detail views.
    """
    route = RouteListSerializer(read_only=True)
    provider = TransportationProviderListSerializer(read_only=True)
    transportation_type = TransportationTypeSerializer(read_only=True)
    
    class Meta(ScheduleSerializer.Meta):
        """
        Meta class for ScheduleDetailSerializer.
        
        Extends the parent Meta class with additional fields.
        """
        fields = ScheduleSerializer.Meta.fields + [
            'created_at', 'updated_at'
        ]
        read_only_fields = ScheduleSerializer.Meta.read_only_fields + [
            'created_at', 'updated_at'
        ]


class TransportationOptionSerializer(serializers.ModelSerializer):
    """
    Serializer for TransportationOption model.
    
    Represents transportation options available at a destination.
    """
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    transport_type_name = serializers.CharField(source='transport_type.name', read_only=True)
    transport_type_icon = serializers.SerializerMethodField()
    providers_count = serializers.SerializerMethodField()
    
    def get_transport_type_icon(self, obj):
        """
        Get the absolute URL for the transport type icon.
        
        Args:
            obj: The TransportationOption instance
            
        Returns:
            str: The absolute URL for the icon or None
        """
        request = self.context.get('request')
        if request and obj.transport_type.icon:
            return request.build_absolute_uri(obj.transport_type.icon.url)
        return None
    
    def get_providers_count(self, obj):
        """
        Get the count of providers for this transportation option.
        
        Args:
            obj: The TransportationOption instance
            
        Returns:
            int: Number of providers
        """
        return obj.providers.count()
    
    class Meta:
        """
        Meta class for TransportationOptionSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = TransportationOption
        fields = [
            'id', 'destination', 'destination_name',
            'transport_type', 'transport_type_name', 'transport_type_icon',
            'availability', 'avg_price_level', 'providers_count',
            'local_tips', 'is_recommended', 'is_active'
        ]
        read_only_fields = ['id', 'providers_count', 'transport_type_icon']


class TransportationOptionDetailSerializer(TransportationOptionSerializer):
    """
    Detailed serializer for TransportationOption.
    
    Extends the base serializer with additional fields for detail views.
    """
    providers = TransportationProviderListSerializer(many=True, read_only=True)
    transport_type = TransportationTypeSerializer(read_only=True)
    
    class Meta(TransportationOptionSerializer.Meta):
        """
        Meta class for TransportationOptionDetailSerializer.
        
        Extends the parent Meta class with additional fields.
        """
        fields = TransportationOptionSerializer.Meta.fields + ['providers']
