from django.apps import AppConfig


class TravelGalleryConfig(AppConfig):
    """
    Travel Gallery App Configuration
    
    This class configures the Travel Gallery app which manages and displays
    travel-related images in a gallery format. The app handles image storage, 
    categorization, display and related metadata like location coordinates.
    
    Attributes:
        default_auto_field (str): The default auto field type for models
        name (str): The name of the app used by Django to identify it
        verbose_name (str): Human-readable name for the app
        label (str): Unique identifier for the app used by Django
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'travel_gallery'
    verbose_name = 'Travel Gallery'
    label = 'travel_gallery'
