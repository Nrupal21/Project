"""
Models for the destinations app.

This module contains models for managing destinations, regions, seasons, and related data.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# Removed GeoDjango import as it's not used and requires GDAL library

# Create your models here.
# This file contains models for geographic data such as regions, destinations,
# attractions, and seasons. These models form the foundation for the travel
# platform's destination browsing and tour location functionality.

class Region(models.Model):
    """
    Model representing a geographic region containing multiple destinations.
    
    Attributes:
        name (str): The name of the region.
        slug (str): URL-friendly version of the name.
        description (str): Detailed description of the region.
        image (ImageField): Representative image of the region.
        created_at (datetime): When the region was created.
        updated_at (datetime): When the region was last updated.
    """
    # Region name (e.g., "Europe", "Southeast Asia", "North America")
    name = models.CharField(
        max_length=100,
        verbose_name=_('name'),
        help_text=_('Name of the region')
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        help_text=_('Short code for the region (e.g., EU, NA, SEA)')
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether the region is active and visible to users')
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text=_('Display order (lower numbers shown first)')
    )
    slug = models.SlugField(max_length=100, unique=True, help_text="URL-friendly version of the name")
    # Detailed description of the region's characteristics, history, culture, etc.
    description = models.TextField(
        blank=True,
        verbose_name=_('description'),
        help_text=_('Description of the region')
    )
    image = models.ImageField(upload_to='regions/', null=True, blank=True, help_text="Representative image of the region")
    # Timestamp for when the region was first created in the database
    # Useful for auditing and sorting by newest regions
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('created at'),
        help_text=_('When this record was created')
    )
    updated_at = models.DateTimeField(auto_now=True, help_text="When the region was last updated")
    
    class Meta:
        """Metadata options for the Region model."""
        # Database table name
        db_table = 'destinations_region'
        # Human-readable names for Django admin
        verbose_name = _('region')
        verbose_name_plural = _('regions')
        # Default ordering when querying regions
        ordering = ['order', 'name']
        # Database indexes to speed up common queries
        indexes = [
            # Index for looking up regions by code
            models.Index(fields=['code'], name='region_code_idx'),
            # Index for filtering active/inactive regions
            models.Index(fields=['is_active'], name='region_active_idx'),
            # Index for ordering regions by display order
            models.Index(fields=['order'], name='region_order_idx')
        ]
    
    def __str__(self):
        """String representation of the Region model."""
        return self.name

class Destination(models.Model):
    """
    Model representing a travel destination.
    
    This model is the core of the destinations app, representing cities, towns,
    or specific locations that travelers can visit. Destinations belong to regions
    and can have multiple attractions, images, and seasonal information associated with them.
    
    Attributes:
        name (str): The name of the destination.
        slug (str): URL-friendly version of the name for SEO-friendly URLs.
        region (ForeignKey): The region this destination belongs to (e.g., Europe, Asia).
        description (str): Detailed description of the destination for full information pages.
        short_description (str): Brief description for listings and preview cards.
        latitude (float): Latitude coordinate for map placement and proximity searches.
        longitude (float): Longitude coordinate for map placement and proximity searches.
        address (str): Physical address of the destination's central point.
        city (str): City where the destination is located (may be same as name).
        country (str): Country where the destination is located.
        postal_code (str): Postal or ZIP code of the destination.
        is_featured (bool): Whether to highlight this destination in featured sections.
        is_active (bool): Whether the destination is currently available for booking/viewing.
        created_at (datetime): When the destination record was created.
        updated_at (datetime): When the destination record was last updated.
    """
    name = models.CharField(max_length=200, help_text="Name of the destination")
    slug = models.SlugField(max_length=200, unique=True, help_text="URL-friendly version of the name")
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='destinations', help_text="Region this destination belongs to")
    description = models.TextField(help_text="Detailed description of the destination")
    short_description = models.CharField(max_length=255, blank=True, 
                                        help_text="Brief description for listings and previews")
    
    # Location information - used for maps, geospatial queries, and address display
    # Coordinates enable map integration and distance-based searches
    latitude = models.FloatField(null=True, blank=True, help_text="Latitude coordinate of the destination")
    longitude = models.FloatField(null=True, blank=True, help_text="Longitude coordinate of the destination")
    # Address components for contact information and directions
    address = models.TextField(blank=True, help_text="Physical address of the destination")
    city = models.CharField(max_length=100, blank=True, help_text="City where the destination is located")
    country = models.CharField(max_length=100, help_text="Country where the destination is located")
    postal_code = models.CharField(max_length=20, blank=True, 
                               help_text="Postal or ZIP code of the destination")
    
    # Status flags - control visibility and prominence of destinations
    # Featured destinations appear on the homepage and in highlighted sections
    is_featured = models.BooleanField(default=False, help_text="Whether this is a featured destination")
    # Inactive destinations won't appear in public searches or listings
    is_active = models.BooleanField(default=True, help_text="Whether this destination is currently active")
    
    # Timestamps - for sorting, filtering, and auditing
    # Auto-populated when record is first created
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the destination was created")
    # Auto-updated whenever the record is saved
    updated_at = models.DateTimeField(auto_now=True, help_text="When the destination was last updated")
    
    class Meta:
        """Metadata options for the Destination model.
        
        Configures database behavior, default ordering, and indexes
        for efficient querying in the database.
        """
        # Default to alphabetical ordering when querying destinations
        ordering = ['name']
        # Define indexes to speed up common query patterns
        indexes = [
            # Makes name-based searches faster (autocomplete, search)
            models.Index(fields=['name']),
            # Improves performance of featured destination queries (homepage)
            models.Index(fields=['is_featured']),
            # Speeds up filtering of active/inactive destinations
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        """String representation of the Destination model.
        
        Returns:
            str: The destination name, used in admin interface and debugging
        """
        return self.name
    
    @property
    def full_address(self):
        """Returns the full address as a formatted string.
        
        Combines all non-empty address components into a properly formatted
        address string, skipping any empty components.
        
        Returns:
            str: Comma-separated address string with all available components
        """
        # Combine only the parts that have values, skipping empty fields
        address_parts = []
        if self.address:
            address_parts.append(self.address)
        if self.city:
            address_parts.append(self.city)
        if self.country:
            address_parts.append(self.country)
        if self.postal_code:
            address_parts.append(self.postal_code)
            
        # Join with commas for readable address format
        return ", ".join(address_parts)

class DestinationImage(models.Model):
    """
    Model representing images associated with a destination.
    
    Attributes:
        destination (ForeignKey): The destination this image belongs to.
        image (ImageField): The image file.
        caption (str): Optional caption for the image.
        is_primary (bool): Whether this is the primary image for the destination.
        order (int): Display order for the image.
        created_at (datetime): When the image was uploaded.
    """
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='images',
                                   help_text="The destination this image belongs to")
    image = models.ImageField(upload_to='destinations/', help_text="The image file")
    caption = models.CharField(max_length=255, blank=True, help_text="Optional caption for the image")
    is_primary = models.BooleanField(default=False, help_text="Whether this is the primary image for the destination")
    order = models.PositiveIntegerField(default=0, help_text="Display order for the image")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the image was uploaded")
    
    class Meta:
        """Metadata options for the DestinationImage model."""
        ordering = ['order', 'created_at']
        verbose_name = 'Destination Image'
        verbose_name_plural = 'Destination Images'
    
    def __str__(self):
        """String representation of the DestinationImage model."""
        return f"Image for {self.destination.name}"

class Season(models.Model):
    """
    Model representing a seasonal period at a destination.
    
    Attributes:
        name (str): The name of the season.
        destination (ForeignKey): The destination this season applies to.
        start_month (int): The starting month (1-12).
        end_month (int): The ending month (1-12).
        description (str): Description of what to expect during this season.
        average_temperature (str): Average temperature range during this season.
        is_peak_season (bool): Whether this is a peak travel season.
    """
    name = models.CharField(max_length=50, help_text="Name of the season (e.g., Summer, Monsoon)")
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='seasons',
                                   help_text="The destination this season applies to")
    start_month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Starting month (1-12)"
    )
    end_month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Ending month (1-12)"
    )
    description = models.TextField(help_text="Description of what to expect during this season")
    average_temperature = models.CharField(max_length=50, blank=True, 
                                          help_text="Average temperature range during this season")
    is_peak_season = models.BooleanField(default=False, 
                                       help_text="Whether this is a peak travel season")
    
    class Meta:
        """Metadata options for the Season model."""
        ordering = ['start_month']
        unique_together = ['destination', 'name']
    
    def __str__(self):
        """String representation of the Season model."""
        return f"{self.name} at {self.destination.name}"
    
    def get_month_name(self, month_number):
        """
        Returns the name of the month for the given month number.
        
        Args:
            month_number (int): The month number (1-12).
            
        Returns:
            str: The name of the month.
        """
        from datetime import datetime
        return datetime(2000, month_number, 1).strftime('%B')
    
    @property
    def season_range(self):
        """Returns a formatted string representing the season date range."""
        start_month = self.get_month_name(self.start_month)
        end_month = self.get_month_name(self.end_month)
        return f"{start_month} - {end_month}"

class Attraction(models.Model):
    """
    Model representing a point of interest or attraction at a destination.
    
    Attributes:
        name (str): The name of the attraction.
        destination (ForeignKey): The destination this attraction belongs to.
        description (str): Detailed description of the attraction.
        category (str): Category of the attraction.
        address (str): Physical address of the attraction.
        opening_hours (str): Opening hours information.
        entry_fee (str): Information about entry fees.
        website (URL): Official website of the attraction.
        contact_phone (str): Contact phone number.
        contact_email (str): Contact email address.
        is_featured (bool): Whether this is a featured attraction.
        created_at (datetime): When the attraction was added.
        updated_at (datetime): When the attraction was last updated.
    """
    ATTRACTION_CATEGORIES = [
        ('landmark', 'Landmark'),
        ('museum', 'Museum'),
        ('park', 'Park'),
        ('beach', 'Beach'),
        ('mountain', 'Mountain'),
        ('historical', 'Historical Site'),
        ('religious', 'Religious Site'),
        ('shopping', 'Shopping'),
        ('entertainment', 'Entertainment'),
        ('nature', 'Nature'),
        ('adventure', 'Adventure'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200, help_text="Name of the attraction")
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='attractions',
                                   help_text="The destination this attraction belongs to")
    description = models.TextField(help_text="Detailed description of the attraction")
    category = models.CharField(max_length=50, choices=ATTRACTION_CATEGORIES, 
                              default='other', help_text="Category of the attraction")
    
    # Location and contact information
    address = models.TextField(blank=True, help_text="Physical address of the attraction")
    latitude = models.FloatField(null=True, blank=True, help_text="Latitude coordinate")
    longitude = models.FloatField(null=True, blank=True, help_text="Longitude coordinate")
    opening_hours = models.TextField(blank=True, help_text="Opening hours information")
    entry_fee = models.CharField(max_length=255, blank=True, help_text="Information about entry fees")
    website = models.URLField(blank=True, help_text="Official website of the attraction")
    contact_phone = models.CharField(max_length=50, blank=True, help_text="Contact phone number")
    contact_email = models.EmailField(blank=True, help_text="Contact email address")
    
    # Status
    is_featured = models.BooleanField(default=False, help_text="Whether this is a featured attraction")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the attraction was added")
    updated_at = models.DateTimeField(auto_now=True, help_text="When the attraction was last updated")
    
    class Meta:
        """Metadata options for the Attraction model."""
        ordering = ['name']
        verbose_name = 'Attraction'
        verbose_name_plural = 'Attractions'
    
    def __str__(self):
        """String representation of the Attraction model."""
        return f"{self.name} at {self.destination.name}"

class AttractionImage(models.Model):
    """
    Model representing images associated with an attraction.
    
    Attributes:
        attraction (ForeignKey): The attraction this image belongs to.
        image (ImageField): The image file.
        caption (str): Optional caption for the image.
        is_primary (bool): Whether this is the primary image for the attraction.
        order (int): Display order for the image.
        created_at (datetime): When the image was uploaded.
    """
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE, related_name='images',
                                 help_text="The attraction this image belongs to")
    image = models.ImageField(upload_to='attractions/', help_text="The image file")
    caption = models.CharField(max_length=255, blank=True, help_text="Optional caption for the image")
    is_primary = models.BooleanField(default=False, 
                                   help_text="Whether this is the primary image for the attraction")
    order = models.PositiveIntegerField(default=0, help_text="Display order for the image")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the image was uploaded")
    
    class Meta:
        """Metadata options for the AttractionImage model."""
        ordering = ['order', 'created_at']
        verbose_name = 'Attraction Image'
        verbose_name_plural = 'Attraction Images'
    
    def __str__(self):
        """String representation of the AttractionImage model."""
        return f"Image for {self.attraction.name}"
