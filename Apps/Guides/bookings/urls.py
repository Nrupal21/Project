"""
URL patterns for the bookings app.

This module defines all URL patterns related to booking functionality,
including booking creation, management, payment processing, and API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for API endpoints
router = DefaultRouter()
router.register(r'api/bookings', views.BookingViewSet, basename='booking-api')
router.register(r'api/payments', views.PaymentViewSet, basename='payment-api')

# App namespace for URL reversing
app_name = 'bookings'

# URL patterns for the bookings app
urlpatterns = [
    # API routes
    path('', include(router.urls)),
    
    # Booking management views
    path('', views.booking_list, name='booking_list'),
    path('<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('create/', views.create_booking, name='create_booking'),
    path('create/tour/<int:tour_id>/', views.create_booking, name='create_booking_for_tour'),
    path('create/tour/<int:tour_id>/date/<int:tour_date_id>/', 
         views.create_booking, name='create_booking_for_tour_date'),
    
    # Payment processing
    path('<int:booking_id>/payment/', views.process_payment, name='payment'),
    
    # Booking cancellation
    path('<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
]
