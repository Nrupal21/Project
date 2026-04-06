"""Travel Gallery App

This app manages and displays travel gallery images with locations and metadata.
It provides models, views, and templates for a beautiful gallery display.

The app includes:
- GalleryImage model for storing image data and metadata
- Views for displaying gallery images in various formats
- Admin interface for managing gallery content
"""

# Explicitly set the default app config to ensure proper app registration
# This helps Django identify and load the app correctly
default_app_config = 'travel_gallery.apps.TravelGalleryConfig'