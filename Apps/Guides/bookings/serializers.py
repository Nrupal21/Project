"""
Serializers for the bookings app.

This module defines serializers for converting booking and payment models
to JSON and handling API requests related to bookings.
"""

from rest_framework import serializers
from .models import Booking, Payment
from tours.models import Tour, TourDate


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Payment model.
    
    Converts Payment model instances to JSON format for API responses
    and validates incoming data for API requests.
    """
    class Meta:
        """
        Meta class for PaymentSerializer.
        
        Defines the model and fields to include in serialized representation.
        """
        model = Payment
        fields = [
            'id', 'booking', 'amount', 'payment_method',
            'transaction_id', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Booking model.
    
    Provides a complete representation of a booking including
    related payment information.
    """
    # Include payment information as nested serializer
    payments = PaymentSerializer(many=True, read_only=True)
    
    # Add derived fields
    is_paid = serializers.BooleanField(read_only=True)
    can_be_canceled = serializers.SerializerMethodField()
    tour_name = serializers.CharField(source='tour.name', read_only=True)
    tour_image = serializers.SerializerMethodField()
    
    def get_can_be_canceled(self, obj):
        """
        Determine if booking can be canceled based on business rules.
        
        Args:
            obj: The Booking instance
            
        Returns:
            bool: True if booking can be canceled, False otherwise
        """
        return obj.can_cancel()
    
    def get_tour_image(self, obj):
        """
        Get the primary image URL for the tour.
        
        Args:
            obj: The Booking instance
            
        Returns:
            str: URL of the tour's primary image or None
        """
        # Get primary tour image if available
        request = self.context.get('request')
        if obj.tour and hasattr(obj.tour, 'images'):
            primary_image = obj.tour.images.filter(is_primary=True).first()
            if primary_image and request:
                return request.build_absolute_uri(primary_image.image.url)
            
            # Fallback to first image
            first_image = obj.tour.images.first()
            if first_image and request:
                return request.build_absolute_uri(first_image.image.url)
        
        return None
    
    class Meta:
        """
        Meta class for BookingSerializer.
        
        Defines the model and fields to include in serialized representation.
        """
        model = Booking
        fields = [
            'id', 'user', 'tour', 'tour_name', 'tour_date', 'tour_image',
            'participants', 'total_price', 'status', 'special_requests',
            'is_paid', 'created_at', 'updated_at', 'payments',
            'can_be_canceled', 'cancellation_reason', 'canceled_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 
                           'canceled_at', 'is_paid']


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new bookings.
    
    Handles validation of booking data and related tour availability.
    """
    class Meta:
        """
        Meta class for BookingCreateSerializer.
        
        Defines the model and fields required for creating a booking.
        """
        model = Booking
        fields = ['tour', 'tour_date', 'participants', 'special_requests']
    
    def validate(self, data):
        """
        Validate booking data against business rules.
        
        Checks that:
        - Tour exists and is active
        - Tour date exists, belongs to tour, and is available
        - There are enough spots available for requested participants
        
        Args:
            data: The validated field values
            
        Returns:
            dict: The validated data
            
        Raises:
            ValidationError: If validation fails
        """
        tour = data.get('tour')
        tour_date = data.get('tour_date')
        participants = data.get('participants', 1)
        
        # Check tour is active
        if not tour.is_active:
            raise serializers.ValidationError({"tour": "This tour is not available for booking."})
        
        # Check tour_date belongs to tour
        if tour_date.tour != tour:
            raise serializers.ValidationError({"tour_date": "This date does not belong to the selected tour."})
        
        # Check tour date is available
        if not tour_date.is_available:
            raise serializers.ValidationError({"tour_date": "This tour date is not available."})
        
        # Check if enough spots
        if tour_date.max_participants:
            available_spots = tour_date.max_participants - tour_date.current_participants
            if participants > available_spots:
                raise serializers.ValidationError({
                    "participants": f"Not enough spots available. Only {available_spots} spots left."
                })
        
        # Calculate total price
        data['total_price'] = tour.price * participants
        
        return data
    
    def create(self, validated_data):
        """
        Create a new booking and update tour date participant count.
        
        Args:
            validated_data: The validated data
            
        Returns:
            Booking: The created booking instance
        """
        # Create booking
        booking = Booking.objects.create(**validated_data)
        
        # Update tour date participant count
        tour_date = validated_data['tour_date']
        tour_date.current_participants += validated_data['participants']
        tour_date.save()
        
        return booking


class TourDateSerializer(serializers.ModelSerializer):
    """
    Serializer for TourDate model for booking process.
    
    Includes availability information for the booking process.
    """
    available_spots = serializers.SerializerMethodField()
    
    def get_available_spots(self, obj):
        """
        Calculate available spots for the tour date.
        
        Args:
            obj: The TourDate instance
            
        Returns:
            int: Number of available spots or None if unlimited
        """
        if obj.max_participants:
            return max(0, obj.max_participants - obj.current_participants)
        return None  # Unlimited
    
    class Meta:
        """
        Meta class for TourDateSerializer.
        
        Defines the model and fields to include in serialized representation.
        """
        model = TourDate
        fields = [
            'id', 'start_date', 'end_date', 'price',
            'is_available', 'max_participants', 'current_participants',
            'available_spots', 'is_full'
        ]
