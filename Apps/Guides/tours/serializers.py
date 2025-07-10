"""
Serializers for the tours app.

This module defines serializers for converting Tour, TourCategory, and TourDate models
to and from JSON format for the API.
"""
from rest_framework import serializers
from .models import Tour, TourCategory, TourDate

class TourCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the TourCategory model.
    
    Converts TourCategory instances to/from JSON representations.
    
    Attributes:
        Meta: Configuration class defining the model and fields to serialize
    """
    tour_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TourCategory
        fields = ['id', 'name', 'description', 'icon', 'image', 'tour_count']
    
    def get_tour_count(self, obj):
        """
        Calculate the number of active tours in this category.
        
        Args:
            obj: TourCategory instance
            
        Returns:
            int: Number of active tours in this category
        """
        return obj.tour_set.filter(is_active=True).count()

class TourDateSerializer(serializers.ModelSerializer):
    """
    Serializer for the TourDate model.
    
    Converts TourDate instances to/from JSON representations.
    
    Attributes:
        Meta: Configuration class defining the model and fields to serialize
    """
    available_spots = serializers.SerializerMethodField()
    
    class Meta:
        model = TourDate
        fields = ['id', 'tour', 'start_date', 'end_date', 'price', 'capacity', 'available_spots']
        
    def get_available_spots(self, obj):
        """
        Calculate the number of available spots for this tour date.
        
        Args:
            obj: TourDate instance
            
        Returns:
            int: Number of available spots
        """
        # Assuming Booking model has a spots field
        booked_spots = sum(booking.spots for booking in obj.booking_set.all())
        return max(0, obj.capacity - booked_spots)

class TourSerializer(serializers.ModelSerializer):
    """
    Serializer for the Tour model.
    
    Converts Tour instances to/from JSON representations.
    Includes the category details and the nearest available dates.
    
    Attributes:
        Meta: Configuration class defining the model and fields to serialize
    """
    category_detail = TourCategorySerializer(source='category', read_only=True)
    next_dates = serializers.SerializerMethodField()
    
    class Meta:
        model = Tour
        fields = [
            'id', 'title', 'slug', 'short_description', 'description', 
            'price', 'discount_price', 'image', 'gallery_images',
            'duration_days', 'location', 'map_coordinates', 'included_activities',
            'what_to_bring', 'is_active', 'is_featured', 'category',
            'category_detail', 'next_dates', 'created_at', 'updated_at'
        ]
    
    def get_next_dates(self, obj):
        """
        Get the next 3 available dates for this tour.
        
        Args:
            obj: Tour instance
            
        Returns:
            list: List of serialized TourDate objects
        """
        # Get the next 3 available dates
        next_dates = obj.tourdate_set.filter(
            start_date__gte='2025-06-29'
        ).order_by('start_date')[:3]
        
        return TourDateSerializer(next_dates, many=True).data
