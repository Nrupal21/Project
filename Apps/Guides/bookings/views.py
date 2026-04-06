"""
Views for the bookings app.

This module defines view functions and classes for handling
booking-related HTTP requests, including creating, updating,
viewing, and canceling bookings.
"""

import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Booking, Payment
from .serializers import BookingSerializer, PaymentSerializer, BookingCreateSerializer
from .utils import send_booking_confirmation_email, send_booking_update_email, notify_guides_about_booking
from tours.models import Tour, TourDate


@login_required
def booking_list(request):
    """
    Display all bookings for the current user.
    
    Renders a page showing a list of the user's bookings
    with options to view details, update, or cancel them.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered template with booking data
    """
    # Get all bookings for the current user
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    # Count bookings by status
    upcoming_count = bookings.filter(
        status__in=['confirmed', 'pending'], 
        tour_date__start_date__gte=timezone.now().date()
    ).count()
    
    past_count = bookings.filter(
        status='completed'
    ).count()
    
    canceled_count = bookings.filter(status='canceled').count()
    
    context = {
        'bookings': bookings,
        'upcoming_count': upcoming_count,
        'past_count': past_count,
        'canceled_count': canceled_count,
    }
    
    return render(request, 'bookings/booking_list.html', context)


@login_required
def booking_detail(request, booking_id):
    """
    Display detailed information for a specific booking.
    
    Shows all details of the booking including tour information,
    payment status, and options to modify or cancel.
    
    Args:
        request: The HTTP request object
        booking_id: ID of the booking to display
        
    Returns:
        HttpResponse: Rendered template with booking details
    """
    # Get the booking for the current user
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Get payment information if available
    payments = booking.payments.all().order_by('-created_at')
    
    context = {
        'booking': booking,
        'payments': payments,
        'can_cancel': booking.can_cancel(),
    }
    
    return render(request, 'bookings/booking_detail.html', context)


@login_required
def create_booking(request, tour_id=None, tour_date_id=None):
    """
    Handle the creation of a new booking.
    
    Displays a form for creating a booking and processes
    the form submission.
    
    Args:
        request: The HTTP request object
        tour_id: Optional ID of the tour to book
        tour_date_id: Optional ID of the specific tour date to book
        
    Returns:
        HttpResponse: Rendered form template or redirect after submission
    """
    # If tour_id is provided, pre-select the tour
    tour = None
    tour_date = None
    available_dates = []
    
    if tour_id:
        tour = get_object_or_404(Tour, id=tour_id, is_active=True)
        # Get available dates for this tour
        available_dates = TourDate.objects.filter(
            tour=tour,
            is_available=True,
            start_date__gt=timezone.now().date()
        ).exclude(
            Q(max_participants__isnull=False) & 
            Q(current_participants__gte=models.F('max_participants'))
        )
    
    # If both tour_id and tour_date_id are provided, pre-select both
    if tour_date_id and tour:
        tour_date = get_object_or_404(
            TourDate, 
            id=tour_date_id, 
            tour=tour,
            is_available=True
        )
    
    if request.method == 'POST':
        # Process form submission
        try:
            # Get form data
            selected_tour_id = request.POST.get('tour_id') or tour_id
            selected_tour_date_id = request.POST.get('tour_date_id') or tour_date_id
            participants = int(request.POST.get('participants', 1))
            special_requests = request.POST.get('special_requests', '')
            
            # Validate form data
            if not selected_tour_id or not selected_tour_date_id:
                messages.error(request, "Please select a tour and date.")
                return redirect(request.path)
            
            # Get tour and date objects
            selected_tour = get_object_or_404(Tour, id=selected_tour_id, is_active=True)
            selected_date = get_object_or_404(
                TourDate, 
                id=selected_tour_date_id,
                tour=selected_tour,
                is_available=True
            )
            
            # Check if the tour date has enough space
            if selected_date.max_participants:
                available_spots = selected_date.max_participants - selected_date.current_participants
                if participants > available_spots:
                    messages.error(
                        request, 
                        f"Not enough spots available. Only {available_spots} spots left."
                    )
                    return redirect(request.path)
            
            # Create the booking
            booking = Booking.objects.create(
                user=request.user,
                tour=selected_tour,
                tour_date=selected_date,
                participants=participants,
                special_requests=special_requests,
                status='pending',
                total_price=selected_tour.price * participants
            )
            
            # Update tour date participants count
            selected_date.current_participants += participants
            selected_date.save()
            
            # Redirect to payment
            messages.success(request, "Booking created successfully. Please complete payment.")
            return redirect('bookings:payment', booking_id=booking.id)
            
        except Exception as e:
            messages.error(request, f"Error creating booking: {str(e)}")
            return redirect(request.path)
    
    # For GET requests, render the form
    context = {
        'tour': tour,
        'tour_date': tour_date,
        'available_dates': available_dates,
    }
    
    return render(request, 'bookings/create_booking.html', context)


@login_required
def process_payment(request, booking_id):
    """
    Process payment for a booking.
    
    Handles payment form submission and updates booking status.
    
    Args:
        request: The HTTP request object
        booking_id: ID of the booking to process payment for
        
    Returns:
        HttpResponse: Rendered payment form or redirect after submission
    """
    # Get the booking
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Check if booking is already paid
    if booking.is_paid:
        messages.info(request, "This booking has already been paid for.")
        return redirect('bookings:booking_detail', booking_id=booking.id)
    
    if request.method == 'POST':
        # Process payment form
        payment_method = request.POST.get('payment_method')
        amount = float(request.POST.get('amount', booking.total_price))
        
        # In a real application, payment gateway integration would go here
        # For this demo, we'll just create a payment record and update the booking
        
        # Create payment record
        payment = Payment.objects.create(
            booking=booking,
            amount=amount,
            payment_method=payment_method,
            status='completed'
        )
        
        # Update booking status
        booking.status = 'confirmed'
        booking.is_paid = True
        booking.save()
        
        # Send booking confirmation email
        try:
            email_sent = send_booking_confirmation_email(booking)
            if email_sent:
                logger.info(f"Booking confirmation email sent successfully for booking {booking.id}")
            else:
                logger.warning(f"Failed to send booking confirmation email for booking {booking.id}")
                
            # Notify guides about the booking
            notify_guides_about_booking(booking)
        except Exception as e:
            logger.error(f"Error sending booking confirmation email: {str(e)}", exc_info=True)
            # Don't block the flow if email sending fails
        
        messages.success(request, "Payment processed successfully. Your booking is confirmed!")
        return redirect('bookings:booking_detail', booking_id=booking.id)
    
    # For GET requests, render payment form
    context = {
        'booking': booking,
    }
    
    return render(request, 'bookings/payment.html', context)


@login_required
def cancel_booking(request, booking_id):
    """
    Handle booking cancellation.
    
    Processes the cancellation of a booking and updates its status.
    May apply cancellation fees based on timing and policy.
    
    Args:
        request: The HTTP request object
        booking_id: ID of the booking to cancel
        
    Returns:
        HttpResponse: Redirect to booking detail or list
    """
    # Get the booking
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Check if booking can be canceled
    if not booking.can_cancel():
        messages.error(
            request, 
            "This booking cannot be canceled due to the cancellation policy or its current status."
        )
        return redirect('bookings:booking_detail', booking_id=booking.id)
    
    if request.method == 'POST':
        # Process cancellation
        reason = request.POST.get('cancellation_reason', '')
        
        # Update booking status
        booking.status = 'canceled'
        booking.cancellation_reason = reason
        booking.canceled_at = timezone.now()
        booking.save()
        
        # Send cancellation email notification
        try:
            send_booking_update_email(booking, 'canceled')
        except Exception as e:
            logger.error(f"Error sending booking cancellation email: {str(e)}", exc_info=True)
            # Don't block the flow if email sending fails
        
        # Decrease participant count for the tour date
        if booking.tour_date:
            booking.tour_date.current_participants -= booking.participants
            booking.tour_date.save()
        
        # Process refund if applicable (in real app, would integrate with payment gateway)
        refund_amount = booking.calculate_refund()
        if refund_amount > 0:
            # Create a payment record for the refund
            Payment.objects.create(
                booking=booking,
                amount=-refund_amount,  # Negative amount for refund
                payment_method='refund',
                status='completed'
            )
            
            messages.success(
                request, 
                f"Booking canceled successfully. A refund of ${refund_amount:.2f} will be processed."
            )
        else:
            messages.success(
                request, 
                "Booking canceled successfully. No refund is applicable based on the cancellation policy."
            )
        
        return redirect('bookings:booking_list')
    
    # For GET requests, show cancellation confirmation form
    context = {
        'booking': booking,
        'refund_amount': booking.calculate_refund(),
    }
    
    return render(request, 'bookings/cancel_booking.html', context)


# API Views
class BookingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for booking operations.
    
    Provides CRUD operations for bookings with appropriate permissions.
    Only the booking owner or staff can access individual bookings.
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return bookings for the current user unless staff.
        
        Staff users can see all bookings, regular users only see their own.
        
        Returns:
            QuerySet: Filtered queryset of bookings
        """
        user = self.request.user
        if user.is_staff:
            return Booking.objects.all().order_by('-created_at')
        return Booking.objects.filter(user=user).order_by('-created_at')
    
    def get_serializer_class(self):
        """
        Return different serializers based on the action.
        
        Uses BookingCreateSerializer for creation to handle the booking process.
        
        Returns:
            Serializer class: Appropriate serializer for the current action
        """
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer
    
    def perform_create(self, serializer):
        """
        Set the user to the current user when creating a booking.
        
        Args:
            serializer: The validated serializer instance
        """
        booking = serializer.save(user=self.request.user)
        
        # For initial bookings (pending status), send notification
        try:
            send_booking_confirmation_email(booking)
            notify_guides_about_booking(booking)
        except Exception as e:
            logger.error(f"Error sending booking notification: {str(e)}", exc_info=True)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        API endpoint to cancel a booking.
        
        Args:
            request: The request object
            pk: Primary key of the booking
            
        Returns:
            Response: API response with result of cancellation
        """
        booking = self.get_object()
        
        # Check if booking can be canceled
        if not booking.can_cancel():
            return Response(
                {"detail": "This booking cannot be canceled based on its status or the cancellation policy."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get cancellation reason from request data
        reason = request.data.get('cancellation_reason', '')
        
        # Calculate refund amount before changing status
        refund_amount = booking.calculate_refund()
        
        # Update booking status
        booking.status = 'canceled'
        booking.cancellation_reason = reason
        booking.canceled_at = timezone.now()
        booking.save()
        
        # Decrease participant count for the tour date
        if booking.tour_date:
            booking.tour_date.current_participants -= booking.participants
            booking.tour_date.save()
        
        # Process refund if applicable
        if refund_amount > 0:
            # Create a payment record for the refund
            Payment.objects.create(
                booking=booking,
                amount=-refund_amount,  # Negative amount for refund
                payment_method='refund',
                status='completed'
            )
            
            return Response({
                "detail": "Booking canceled successfully.", 
                "refund_amount": refund_amount
            })
        
        return Response({"detail": "Booking canceled successfully. No refund applicable."})


class PaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for payment operations.
    
    Provides CRUD operations for payments with appropriate permissions.
    Regular users can only view their own payments.
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return payments for the current user unless staff.
        
        Staff users can see all payments, regular users only see their own.
        
        Returns:
            QuerySet: Filtered queryset of payments
        """
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all().order_by('-created_at')
        return Payment.objects.filter(booking__user=user).order_by('-created_at')
