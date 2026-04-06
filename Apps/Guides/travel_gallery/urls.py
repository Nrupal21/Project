"""
URL configuration for the travel_gallery app.

This module defines URL patterns for viewing travel gallery images.
Each URL pattern includes comprehensive documentation and follows Django best practices.
"""

from django.urls import path
from . import views

app_name = 'travel_gallery'

urlpatterns = [
    # Gallery list view - shows all gallery images with filtering options
    path('', views.GalleryImageListView.as_view(), name='list'),
    
    # Gallery detail view - shows a single gallery image in full detail
    path('<int:pk>/', views.GalleryImageDetailView.as_view(), name='detail'),
    
    # Gallery grid view - shows a grid of featured images for inclusion on other pages
    path('grid/', views.gallery_grid_view, name='grid'),
]
