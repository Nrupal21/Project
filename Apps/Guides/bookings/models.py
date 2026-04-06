"""
Models for the bookings app.

This module defines all database models related to tour and service bookings,
including booking records, payments, and related entities.
"""

from django.db import models
from django.contrib.auth import get_user_model
from tours.models import Tour, TourDate
import uuid

# Get the custom user model
User = get_user_model()


class Booking(models.Model):
    """
    Represents a tour booking made by a user.
    
    This model stores information about tour bookings including
    reference number, tour selection, date, participants, and status.
    """
    # Booking status choices
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'cancelled'
    STATUS_COMPLETED = 'completed'
    STATUS_REFUNDED = 'refunded'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_PAID, 'Paid'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]
    
    # Booking references and relations
    reference_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='bookings')
    tour = models.ForeignKey(Tour, on_delete=models.PROTECT, related_name='bookings')
    tour_date = models.ForeignKey(TourDate, on_delete=models.PROTECT, related_name='bookings')
    
    # Booking details
    participants = models.PositiveIntegerField(default=1)
    special_requests = models.TextField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Traveler information
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    traveler_names = models.JSONField(default=list)
    
    # Booking status and dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Return a string representation of the booking.
        
        Returns:
            str: Reference number and tour name
        """
        return f"Booking #{self.reference_number} - {self.tour.name}"
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure reference number is created if not provided.
        
        Generates a unique booking reference number when creating a new booking.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        if not self.reference_number:
            # Generate a unique reference number based on uuid
            self.reference_number = f"BK-{uuid.uuid4().hex[:8].upper()}"
        
        super().save(*args, **kwargs)
    
    def cancel(self):
        """
        Cancel the booking and update related records.
        
        Updates the booking status to cancelled and decrements
        the tour date's participant count.
        """
        if self.status not in [self.STATUS_CANCELLED, self.STATUS_REFUNDED]:
            # Update booking status
            self.status = self.STATUS_CANCELLED
            
            # Update tour date participants count if booking was confirmed
            if self.is_paid:
                self.tour_date.current_participants -= self.participants
                self.tour_date.save()
            
            self.save()
    
    class Meta:
        """
        Meta options for the Booking model.
        
        Defines ordering and verbose names.
        """
        ordering = ['-created_at']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'


class Payment(models.Model):
    """
    Represents a payment for a booking.
    
    This model stores payment information including amount,
    payment method, transaction details, and status.
    """
    # Payment status choices
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]
    
    # Payment method choices
    METHOD_CREDIT_CARD = 'credit_card'
    METHOD_PAYPAL = 'paypal'
    METHOD_BANK_TRANSFER = 'bank_transfer'
    METHOD_OTHER = 'other'
    
    METHOD_CHOICES = [
        (METHOD_CREDIT_CARD, 'Credit Card'),
        (METHOD_PAYPAL, 'PayPal'),
        (METHOD_BANK_TRANSFER, 'Bank Transfer'),
        (METHOD_OTHER, 'Other'),
    ]
    
    # Payment references and relations
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name='payments')
    transaction_id = models.CharField(max_length=100, unique=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    
    # Payment status and dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_data = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Return a string representation of the payment.
        
        Returns:
            str: Transaction ID and amount
        """
        return f"Payment {self.transaction_id} - {self.amount} {self.currency}"
    
    def process_payment(self):
        """
        Process the payment and update related booking.
        
        Updates the payment status to completed and marks
        the related booking as paid if successful.
        
        Returns:
            bool: True if payment was processed successfully, False otherwise
        """
        # This is a simplified implementation
        # In a real app, you would integrate with a payment gateway
        
        # Mark payment as completed
        self.status = self.STATUS_COMPLETED
        self.save()
        
        # Update booking status
        booking = self.booking
        booking.is_paid = True
        booking.status = Booking.STATUS_PAID
        booking.save()
        
        # Update tour date participant count
        tour_date = booking.tour_date
        tour_date.current_participants += booking.participants
        tour_date.save()
        
        return True
    
    def refund(self):
        """
        Process a refund for this payment.
        
        Updates the payment status to refunded and updates
        the related booking status accordingly.
        
        Returns:
            bool: True if refund was processed successfully, False otherwise
        """
        # This is a simplified implementation
        # In a real app, you would integrate with a payment gateway
        
        # Mark payment as refunded
        self.status = self.STATUS_REFUNDED
        self.save()
        
        # Update booking status
        booking = self.booking
        booking.status = Booking.STATUS_REFUNDED
        booking.save()
        
        # Update tour date participant count
        tour_date = booking.tour_date
        tour_date.current_participants -= booking.participants
        tour_date.save()
        
        return True
    
    class Meta:
        """
        Meta options for the Payment model.
        
        Defines ordering and verbose names.
        """
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
