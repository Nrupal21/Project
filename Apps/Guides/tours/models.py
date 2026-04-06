"""
Models for the tours app.

This module defines all database models related to tours,
including tour packages, categories, itineraries, and related entities.
"""

from django.db import models
from django.utils.text import slugify
from django.conf import settings
from destinations.models import Destination, Attraction
from core.managers import TourManager, BaseOptimizedManager
from core.utils import DataValidationUtils

# Get the custom user model
User = settings.AUTH_USER_MODEL

class TourCategory(models.Model):
    """
    Represents a category or type of tour package.
    
    Categories help organize tours by type such as adventure,
    cultural, culinary, etc.
    
    This model uses BaseOptimizedManager for consistent query patterns
    and integrates with core utilities for data validation.
    """
    
    # Custom manager with base optimizations
    objects = BaseOptimizedManager()
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Return a string representation of the tour category.
        
        Returns:
            str: The name of the category
        """
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure slug is created from name if not provided.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    class Meta:
        """
        Meta options for the TourCategory model.
        
        Defines ordering, verbose name, and plural name.
        """
        ordering = ['name']
        verbose_name = 'Tour Category'
        verbose_name_plural = 'Tour Categories'


class Tour(models.Model):
    """
    Represents a tour package offered to customers.
    
    A tour includes information about duration, price, included destinations,
    itinerary, and other details relevant for travelers.
    
    This model uses the enhanced TourManager for optimized queries and
    integrates with core utilities for data validation and consistency.
    """
    
    # Custom manager with enhanced functionality
    objects = TourManager()
    # Basic information
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    category = models.ForeignKey(TourCategory, on_delete=models.SET_NULL, 
                                null=True, related_name='tours')
    
    # Tour details
    short_description = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    duration_days = models.PositiveIntegerField()
    group_size_min = models.PositiveIntegerField(default=1)
    group_size_max = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, 
                                        null=True, blank=True)
    
    # Tour locations
    destinations = models.ManyToManyField(Destination, related_name='tours')
    start_location = models.CharField(max_length=200, blank=True, null=True)
    end_location = models.CharField(max_length=200, blank=True, null=True)
    
    # Tour attributes
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    difficulty_level = models.CharField(max_length=50, blank=True, null=True)
    languages = models.CharField(max_length=200, blank=True, null=True)
    
    # Inclusions/exclusions as JSON fields
    inclusions = models.JSONField(default=dict, blank=True, null=True)
    exclusions = models.JSONField(default=dict, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Return a string representation of the tour.
        
        Returns:
            str: The name of the tour
        """
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure slug is created from name if not provided.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    class Meta:
        """
        Meta options for the Tour model.
        
        Defines ordering and verbose names.
        """
        ordering = ['name']
        verbose_name = 'Tour'
        verbose_name_plural = 'Tours'


class TourImage(models.Model):
    """
    Stores images associated with a tour.
    
    Each tour can have multiple images, with one designated as primary.
    The primary image is used as the main visual representation of the tour
    in lists and cards.
    """
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='tours/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        """
        Return a string representation of the tour image.
        
        Returns:
            str: A descriptive string for the image
        """
        return f"Image for {self.tour.name}"
    
    class Meta:
        """
        Meta options for the TourImage model.
        
        Defines ordering and verbose names.
        """
        ordering = ['-is_primary', 'created_at']
        verbose_name = 'Tour Image'
        verbose_name_plural = 'Tour Images'


class TourDate(models.Model):
    """
    Represents scheduled dates for a tour.
    
    Each tour can have multiple scheduled dates with different
    availability and pricing.
    """
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='dates')
    start_date = models.DateField()
    end_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    current_participants = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        """
        Return a string representation of the tour date.
        
        Returns:
            str: A descriptive string including the tour name and date range
        """
        return f"{self.tour.name} - {self.start_date} to {self.end_date}"
    
    @property
    def is_full(self):
        """
        Check if the tour date is fully booked.
        
        Returns:
            bool: True if the tour is fully booked, False otherwise
        """
        if not self.max_participants:
            return False
        return self.current_participants >= self.max_participants
    
    class Meta:
        """
        Meta options for the TourDate model.
        
        Defines ordering and verbose names.
        """
        ordering = ['start_date']
        verbose_name = 'Tour Date'
        verbose_name_plural = 'Tour Dates'


class TourItinerary(models.Model):
    """
    Represents a day-by-day itinerary for a tour.
    
    Each tour has multiple itinerary items, one for each day of the tour,
    detailing activities, accommodations, and other information.
    """
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='itinerary_items')
    day = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    attractions = models.ManyToManyField(Attraction, blank=True, related_name='tour_days')
    accommodation = models.CharField(max_length=200, blank=True, null=True)
    meals = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Return a string representation of the tour itinerary item.
        
        Returns:
            str: A descriptive string including the tour name and day number
        """
        return f"{self.tour.name} - Day {self.day}: {self.title}"
    
    class Meta:
        """
        Meta options for the TourItinerary model.
        
        Defines ordering, unique constraints, and verbose names.
        """
        ordering = ['tour', 'day']
        unique_together = ['tour', 'day']
        verbose_name = 'Tour Itinerary Item'
        verbose_name_plural = 'Tour Itinerary Items'


class TourReview(models.Model):
    """
    Stores customer reviews and ratings for tours.
    
    Each review includes a rating, comment, and author information.
    """
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()  # 1-5 stars
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)
    
    def __str__(self):
        """
        Return a string representation of the tour review.
        
        Returns:
            str: A descriptive string including the tour name and rating
        """
        return f"{self.tour.name} - {self.rating} stars"
    
    class Meta:
        """
        Meta options for the TourReview model.
        
        Defines ordering, unique constraints, and verbose names.
        """
        ordering = ['-created_at']
        unique_together = ['tour', 'user']
        verbose_name = 'Tour Review'
        verbose_name_plural = 'Tour Reviews'
