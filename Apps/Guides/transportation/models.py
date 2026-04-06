"""
Models for the transportation app.

This module defines models for transportation options available at destinations,
including various modes of transport, routes, schedules, and providers.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse

from destinations.models import Destination


class TransportationType(models.Model):
    """
    Represents a type or mode of transportation.
    
    Examples include: Bus, Train, Ferry, Taxi, Ride-sharing, etc.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    icon = models.ImageField(upload_to='transportation/icons/', null=True, blank=True)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True, help_text="Whether this is public transportation")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        """
        Return a string representation of the transport type.
        
        Returns:
            str: The name of the transport type
        """
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Override save method to automatically generate slug.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    class Meta:
        """
        Meta class for TransportationType.
        
        Defines ordering and verbose names.
        """
        ordering = ['name']
        verbose_name = "Transportation Type"
        verbose_name_plural = "Transportation Types"


class TransportationProvider(models.Model):
    """
    Represents a company or organization providing transportation services.
    
    Links to transportation types they offer and stores contact details.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    transportation_types = models.ManyToManyField(
        TransportationType,
        related_name='providers'
    )
    logo = models.ImageField(upload_to='transportation/logos/', null=True, blank=True)
    website = models.URLField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    description = models.TextField(blank=True)
    is_partner = models.BooleanField(default=False, help_text="Whether this provider is our business partner")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        """
        Return a string representation of the provider.
        
        Returns:
            str: The name of the provider
        """
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Override save method to automatically generate slug.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """
        Get the URL for this provider's detail view.
        
        Returns:
            str: URL for the provider's detail page
        """
        return reverse('transportation:provider_detail', kwargs={'slug': self.slug})
    
    class Meta:
        """
        Meta class for TransportationProvider.
        
        Defines ordering and verbose names.
        """
        ordering = ['name']
        verbose_name = "Transportation Provider"
        verbose_name_plural = "Transportation Providers"


class Route(models.Model):
    """
    Represents a transportation route between destinations.
    
    A route can be served by multiple transportation providers on a schedule.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    origin = models.ForeignKey(
        Destination, 
        on_delete=models.CASCADE,
        related_name='routes_as_origin'
    )
    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name='routes_as_destination'
    )
    transportation_types = models.ManyToManyField(
        TransportationType,
        related_name='routes'
    )
    providers = models.ManyToManyField(
        TransportationProvider,
        related_name='routes'
    )
    distance_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Distance in kilometers"
    )
    typical_duration = models.DurationField(
        null=True,
        blank=True,
        help_text="Typical journey duration"
    )
    description = models.TextField(blank=True)
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Return a string representation of the route.
        
        Returns:
            str: A string describing the route from origin to destination
        """
        return f"{self.origin} to {self.destination}"
    
    def save(self, *args, **kwargs):
        """
        Override save method to automatically generate slug.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        if not self.slug:
            self.slug = slugify(f"{self.origin}-to-{self.destination}")
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """
        Get the URL for this route's detail view.
        
        Returns:
            str: URL for the route's detail page
        """
        return reverse('transportation:route_detail', kwargs={'slug': self.slug})
    
    class Meta:
        """
        Meta class for Route.
        
        Defines ordering and unique constraints.
        """
        ordering = ['origin', 'destination']
        unique_together = ('origin', 'destination')
        verbose_name = "Route"
        verbose_name_plural = "Routes"


class Schedule(models.Model):
    """
    Represents a scheduled service on a route by a specific provider.
    
    Contains details about departure and arrival times, frequency,
    pricing, and availability.
    """
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    provider = models.ForeignKey(
        TransportationProvider,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    transportation_type = models.ForeignKey(
        TransportationType,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    days_of_week = models.CharField(
        max_length=7,
        help_text="Days when this service runs. Format: MTWTFSS where each letter represents a day "
                  "(Monday to Sunday). Replace with '-' for days when the service doesn't run."
    )
    is_daily = models.BooleanField(default=False)
    price_economy = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Standard/Economy price in USD"
    )
    price_business = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Business/Premium price in USD"
    )
    has_wifi = models.BooleanField(default=False)
    has_power_outlets = models.BooleanField(default=False)
    has_meal_service = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    booking_url = models.URLField(blank=True, help_text="URL for booking this service")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Return a string representation of the schedule.
        
        Returns:
            str: A string describing the schedule with route, provider, and time
        """
        return f"{self.route} - {self.provider} ({self.departure_time})"
    
    def is_running_on(self, day_index):
        """
        Check if the service runs on a specific day of the week.
        
        Args:
            day_index: Integer from 0 (Monday) to 6 (Sunday)
            
        Returns:
            bool: True if service runs on the specified day
        """
        if self.is_daily:
            return True
        if 0 <= day_index <= 6:
            return self.days_of_week[day_index] != '-'
        return False
    
    class Meta:
        """
        Meta class for Schedule.
        
        Defines ordering and verbose names.
        """
        ordering = ['route', 'departure_time']
        verbose_name = "Schedule"
        verbose_name_plural = "Schedules"


class TransportationOption(models.Model):
    """
    Represents transportation options available at a specific destination.
    
    Links destinations with available transportation types and provides
    local information like availability and pricing.
    """
    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name='transportation_options'
    )
    transport_type = models.ForeignKey(
        TransportationType,
        on_delete=models.CASCADE,
        related_name='destination_options'
    )
    providers = models.ManyToManyField(
        TransportationProvider,
        related_name='destination_options',
        blank=True
    )
    availability = models.CharField(
        max_length=50,
        choices=[
            ('VERY_LIMITED', 'Very Limited'),
            ('LIMITED', 'Limited'),
            ('MODERATE', 'Moderate'),
            ('GOOD', 'Good'),
            ('EXCELLENT', 'Excellent')
        ],
        default='MODERATE'
    )
    avg_price_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        help_text="Average price level from 1 (very cheap) to 5 (very expensive)"
    )
    local_tips = models.TextField(blank=True, help_text="Local tips for using this transport option")
    is_recommended = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        """
        Return a string representation of the transportation option.
        
        Returns:
            str: A string describing the transportation option at destination
        """
        return f"{self.transport_type} at {self.destination}"
    
    class Meta:
        """
        Meta class for TransportationOption.
        
        Defines ordering and unique constraints.
        """
        ordering = ['destination', 'transport_type']
        unique_together = ('destination', 'transport_type')
        verbose_name = "Transportation Option"
        verbose_name_plural = "Transportation Options"


class TransportationImage(models.Model):
    """
    Represents images related to transportation.
    
    Can be associated with different transportation entities like
    types, providers, or specific routes.
    """
    # The image itself
    image = models.ImageField(upload_to='transportation/images/')
    alt_text = models.CharField(max_length=255)
    caption = models.CharField(max_length=255, blank=True)
    
    # Generic relation - can be linked to different transportation models
    content_type_options = models.Q(
        app_label='transportation', 
        model__in=['transportationtype', 'transportationprovider', 'route', 'schedule']
    )
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        limit_choices_to=content_type_options
    )
    object_id = models.PositiveIntegerField()
    
    # Additional metadata
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        """
        Return a string representation of the transportation image.
        
        Returns:
            str: A string describing the image and its related entity
        """
        return f"Image for {self.content_type.model} {self.object_id}"
    
    class Meta:
        """
        Meta class for TransportationImage.
        
        Defines ordering and verbose names.
        """
        ordering = ['-is_primary', 'created_at']
        verbose_name = "Transportation Image"
        verbose_name_plural = "Transportation Images"
