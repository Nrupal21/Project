"""
URL configuration for OTP authentication.

This module maps URL patterns to OTP-related views.
"""
from django.urls import path
from . import views_otp

app_name = 'otp'

urlpatterns = [
    path('request-otp/', views_otp.request_otp, name='request_otp'),
    path('verify-otp/', views_otp.verify_otp, name='verify_otp'),
]
