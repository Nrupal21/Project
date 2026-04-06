"""
URL configuration for the guides app.

This module defines URL patterns for the guides application.
It includes routes for the guide dashboard and other guide-related views.
"""

from django.urls import path
from . import views

app_name = 'guides'

urlpatterns = [
    # Guide dashboard - main dashboard for local guides
    path('dashboard/', views.GuideDashboardView.as_view(), name='dashboard'),
    
    # Add more guide-specific URLs here as needed
]
