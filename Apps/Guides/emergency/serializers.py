"""
Serializers for the emergency app.

This module defines serializers for emergency models, allowing 
conversion between Python objects and JSON representations for the API.
"""

from rest_framework import serializers
from destinations.serializers import DestinationListSerializer, RegionSerializer
from .models import (
    EmergencyServiceType, EmergencyService, EmergencyContact,
    SafetyInformation, EmergencyGuide
)


class EmergencyServiceTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for EmergencyServiceType model.
    
    Handles serialization of emergency service types with their attributes.
    """
    icon_url = serializers.SerializerMethodField()
    
    def get_icon_url(self, obj):
        """
        Get the absolute URL for the icon.
        
        Args:
            obj: The EmergencyServiceType instance
            
        Returns:
            str: The absolute URL for the icon or None
        """
        request = self.context.get('request')
        if request and obj.icon:
            return request.build_absolute_uri(obj.icon.url)
        return None
    
    class Meta:
        """
        Meta class for EmergencyServiceTypeSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = EmergencyServiceType
        fields = [
            'id', 'name', 'slug', 'icon', 'icon_url',
            'description', 'priority_level', 'is_active'
        ]
        read_only_fields = ['id', 'slug', 'icon_url']


class EmergencyContactSerializer(serializers.ModelSerializer):
    """
    Serializer for EmergencyContact model.
    
    Converts emergency contacts to/from JSON for API responses.
    """
    service_type_name = serializers.CharField(source='service_type.name', read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True)
    
    class Meta:
        """
        Meta class for EmergencyContactSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = EmergencyContact
        fields = [
            'id', 'name', 'number', 'country', 'region', 'region_name',
            'service_type', 'service_type_name', 'description', 
            'dialing_instructions', 'is_toll_free', 'languages', 'is_active'
        ]
        read_only_fields = ['id']


class EmergencyServiceListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing EmergencyService instances.
    
    Provides a condensed representation of emergency services for list views.
    """
    service_type_name = serializers.CharField(source='service_type.name', read_only=True)
    service_type_icon = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    
    def get_service_type_icon(self, obj):
        """
        Get the absolute URL for the service type icon.
        
        Args:
            obj: The EmergencyService instance
            
        Returns:
            str: The absolute URL for the icon or None
        """
        request = self.context.get('request')
        if request and obj.service_type.icon:
            return request.build_absolute_uri(obj.service_type.icon.url)
        return None
    
    def get_location(self, obj):
        """
        Get a string representation of the service's location.
        
        Args:
            obj: The EmergencyService instance
            
        Returns:
            str: The name of the destination or region
        """
        return obj.get_location_display()
    
    class Meta:
        """
        Meta class for EmergencyServiceListSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = EmergencyService
        fields = [
            'id', 'name', 'slug', 'service_type', 'service_type_name',
            'service_type_icon', 'destination', 'region', 'location',
            'address', 'phone_number', 'emergency_number',
            'is_24_hours', 'serves_foreign_travelers', 'is_active'
        ]
        read_only_fields = ['id', 'slug', 'service_type_icon', 'location']


class EmergencyServiceDetailSerializer(EmergencyServiceListSerializer):
    """
    Detailed serializer for EmergencyService.
    
    Extends the list serializer with additional fields for detail views.
    """
    service_type = EmergencyServiceTypeSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()
    
    def get_image_url(self, obj):
        """
        Get the absolute URL for the service image.
        
        Args:
            obj: The EmergencyService instance
            
        Returns:
            str: The absolute URL for the image or None
        """
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None
    
    class Meta(EmergencyServiceListSerializer.Meta):
        """
        Meta class for EmergencyServiceDetailSerializer.
        
        Extends the parent Meta class with additional fields.
        """
        fields = EmergencyServiceListSerializer.Meta.fields + [
            'latitude', 'longitude', 'alt_phone_number', 'email',
            'website', 'hours_of_operation', 'description', 'notes',
            'is_verified', 'verification_date', 'image', 'image_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = EmergencyServiceListSerializer.Meta.read_only_fields + [
            'image_url', 'created_at', 'updated_at'
        ]


class SafetyInformationListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing SafetyInformation instances.
    
    Provides a condensed representation of safety information for list views.
    """
    location = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    risk_level_display = serializers.SerializerMethodField()
    
    def get_location(self, obj):
        """
        Get a string representation of the information's location scope.
        
        Args:
            obj: The SafetyInformation instance
            
        Returns:
            str: The name of the destination or region, or 'General'
        """
        return obj.get_location_display()
    
    def get_category_display(self, obj):
        """
        Get the display name for the category.
        
        Args:
            obj: The SafetyInformation instance
            
        Returns:
            str: The display name of the category
        """
        return obj.get_category_display()
    
    def get_risk_level_display(self, obj):
        """
        Get the display name for the risk level.
        
        Args:
            obj: The SafetyInformation instance
            
        Returns:
            str: The display name of the risk level
        """
        return obj.get_risk_level_display()
    
    class Meta:
        """
        Meta class for SafetyInformationListSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = SafetyInformation
        fields = [
            'id', 'title', 'slug', 'destination', 'region', 'location',
            'category', 'category_display', 'risk_level', 'risk_level_display',
            'summary', 'is_featured', 'is_active', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'location', 'category_display',
                           'risk_level_display', 'updated_at']


class SafetyInformationDetailSerializer(SafetyInformationListSerializer):
    """
    Detailed serializer for SafetyInformation.
    
    Extends the list serializer with additional fields for detail views.
    """
    destination_data = serializers.SerializerMethodField()
    region_data = serializers.SerializerMethodField()
    
    def get_destination_data(self, obj):
        """
        Get detailed information about the destination if it exists.
        
        Args:
            obj: The SafetyInformation instance
            
        Returns:
            dict: Serialized destination data or None
        """
        if obj.destination:
            return DestinationListSerializer(obj.destination, context=self.context).data
        return None
    
    def get_region_data(self, obj):
        """
        Get detailed information about the region if it exists.
        
        Args:
            obj: The SafetyInformation instance
            
        Returns:
            dict: Serialized region data or None
        """
        if obj.region:
            return RegionSerializer(obj.region, context=self.context).data
        return None
    
    class Meta(SafetyInformationListSerializer.Meta):
        """
        Meta class for SafetyInformationDetailSerializer.
        
        Extends the parent Meta class with additional fields.
        """
        fields = SafetyInformationListSerializer.Meta.fields + [
            'content', 'source', 'source_url', 'last_verified',
            'expiry_date', 'destination_data', 'region_data',
            'created_at'
        ]
        read_only_fields = SafetyInformationListSerializer.Meta.read_only_fields + [
            'destination_data', 'region_data', 'created_at'
        ]


class EmergencyGuideListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing EmergencyGuide instances.
    
    Provides a condensed representation of emergency guides for list views.
    """
    emergency_type_display = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    
    def get_emergency_type_display(self, obj):
        """
        Get the display name for the emergency type.
        
        Args:
            obj: The EmergencyGuide instance
            
        Returns:
            str: The display name of the emergency type
        """
        return obj.get_emergency_type_display()
    
    def get_location(self, obj):
        """
        Get a string representation of the guide's location scope.
        
        Args:
            obj: The EmergencyGuide instance
            
        Returns:
            str: The name of the destination or region, or 'General'
        """
        if obj.destination:
            return str(obj.destination)
        elif obj.region:
            return str(obj.region)
        return "General"
    
    class Meta:
        """
        Meta class for EmergencyGuideListSerializer.
        
        Defines the model and fields to include in the serialized representation.
        """
        model = EmergencyGuide
        fields = [
            'id', 'title', 'slug', 'destination', 'region', 'location',
            'emergency_type', 'emergency_type_display', 'summary',
            'is_featured', 'is_active', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'location', 'emergency_type_display', 'updated_at']


class EmergencyGuideDetailSerializer(EmergencyGuideListSerializer):
    """
    Detailed serializer for EmergencyGuide.
    
    Extends the list serializer with additional fields for detail views.
    """
    destination_data = serializers.SerializerMethodField()
    region_data = serializers.SerializerMethodField()
    related_services = EmergencyServiceListSerializer(many=True, read_only=True)
    
    def get_destination_data(self, obj):
        """
        Get detailed information about the destination if it exists.
        
        Args:
            obj: The EmergencyGuide instance
            
        Returns:
            dict: Serialized destination data or None
        """
        if obj.destination:
            return DestinationListSerializer(obj.destination, context=self.context).data
        return None
    
    def get_region_data(self, obj):
        """
        Get detailed information about the region if it exists.
        
        Args:
            obj: The EmergencyGuide instance
            
        Returns:
            dict: Serialized region data or None
        """
        if obj.region:
            return RegionSerializer(obj.region, context=self.context).data
        return None
    
    class Meta(EmergencyGuideListSerializer.Meta):
        """
        Meta class for EmergencyGuideDetailSerializer.
        
        Extends the parent Meta class with additional fields.
        """
        fields = EmergencyGuideListSerializer.Meta.fields + [
            'before_emergency', 'during_emergency', 'after_emergency',
            'related_services', 'destination_data', 'region_data',
            'created_at'
        ]
        read_only_fields = EmergencyGuideListSerializer.Meta.read_only_fields + [
            'related_services', 'destination_data', 'region_data', 'created_at'
        ]
