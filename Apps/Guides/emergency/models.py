"""
Models for the emergency app.

This module defines models for emergency services, contacts,
and safety information related to destinations, helping travelers
access critical resources and information during emergencies.
"""

from django.db import models
from django.utils.text import slugify
from django.urls import reverse

from destinations.models import Destination, Region


class EmergencyServiceType(models.Model):
    """
    Represents a type of emergency service.
    
    Examples include police, ambulance, fire department, embassy,
    consulate, hospital, etc. Used to categorize emergency services.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    icon = models.ImageField(upload_to='emergency/icons/', null=True, blank=True)
    description = models.TextField(blank=True)
    priority_level = models.PositiveSmallIntegerField(
        default=1,
        help_text="Higher numbers indicate higher priority in listings"
    )
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        """
        Return a string representation of the emergency service type.
        
        Returns:
            str: The name of the emergency service type
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
        Meta class for EmergencyServiceType.
        
        Defines ordering and verbose names.
        """
        ordering = ['-priority_level', 'name']
        verbose_name = "Emergency Service Type"
        verbose_name_plural = "Emergency Service Types"


class EmergencyService(models.Model):
    """
    Represents an emergency service provider.
    
    Contains contact information and details about emergency services
    such as hospitals, police stations, embassies, etc.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    service_type = models.ForeignKey(
        EmergencyServiceType,
        on_delete=models.CASCADE,
        related_name='services'
    )
    
    # Location information
    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name='emergency_services',
        null=True,
        blank=True,
        help_text="Specific destination where this service is located"
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='emergency_services',
        null=True,
        blank=True,
        help_text="Region where this service operates (if not destination-specific)"
    )
    address = models.TextField()
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6,
        null=True,
        blank=True
    )
    
    # Contact information
    phone_number = models.CharField(max_length=50)
    alt_phone_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Alternative phone number"
    )
    emergency_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Emergency-only direct number"
    )
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Hours and availability
    hours_of_operation = models.TextField(
        blank=True,
        help_text="Operating hours or availability information"
    )
    is_24_hours = models.BooleanField(
        default=False,
        help_text="Whether this service is available 24 hours a day"
    )
    
    # Additional information
    description = models.TextField(blank=True)
    notes = models.TextField(
        blank=True,
        help_text="Additional notes, such as languages spoken, services offered, etc."
    )
    
    # Service attributes
    serves_foreign_travelers = models.BooleanField(
        default=True,
        help_text="Whether this service is suitable for foreign travelers"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether this service's information has been verified"
    )
    verification_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Image and metadata
    image = models.ImageField(upload_to='emergency/services/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Return a string representation of the emergency service.
        
        Returns:
            str: The name of the emergency service
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
        Get the URL for this service's detail view.
        
        Returns:
            str: URL for the service's detail page
        """
        return reverse('emergency:service_detail', kwargs={'slug': self.slug})
    
    def get_location_display(self):
        """
        Get a human-readable representation of the service's location.
        
        Returns:
            str: Name of the destination or region
        """
        if self.destination:
            return str(self.destination)
        elif self.region:
            return str(self.region)
        return "Unknown location"
    
    class Meta:
        """
        Meta class for EmergencyService.
        
        Defines ordering and verbose names.
        """
        ordering = ['service_type__priority_level', 'name']
        verbose_name = "Emergency Service"
        verbose_name_plural = "Emergency Services"


class EmergencyContact(models.Model):
    """
    Represents a general emergency contact number or hotline.
    
    Contains country or region-specific emergency numbers like 911, 112, etc.,
    that are not tied to a specific service provider.
    """
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=20)
    
    # Location scope
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='emergency_contacts',
        null=True,
        blank=True
    )
    country = models.CharField(
        max_length=100,
        help_text="Country name where this emergency number is valid"
    )
    
    # Type and purpose
    service_type = models.ForeignKey(
        EmergencyServiceType,
        on_delete=models.SET_NULL,
        related_name='contacts',
        null=True,
        blank=True
    )
    description = models.TextField(blank=True)
    
    # Usage information
    dialing_instructions = models.TextField(
        blank=True,
        help_text="Instructions for dialing this number from abroad"
    )
    is_toll_free = models.BooleanField(default=True)
    languages = models.CharField(
        max_length=200,
        blank=True,
        help_text="Languages supported by this service"
    )
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        """
        Return a string representation of the emergency contact.
        
        Returns:
            str: The name and number of the emergency contact
        """
        return f"{self.name} ({self.number})"
    
    class Meta:
        """
        Meta class for EmergencyContact.
        
        Defines ordering and verbose names.
        """
        ordering = ['country', 'name']
        verbose_name = "Emergency Contact"
        verbose_name_plural = "Emergency Contacts"
        unique_together = ('number', 'country')


class SafetyInformation(models.Model):
    """
    Represents safety information for a destination or region.
    
    Contains safety tips, warnings, and general advice for travelers
    about health, crime, natural hazards, etc.
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    
    # Location scope
    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name='safety_information',
        null=True,
        blank=True
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='safety_information',
        null=True,
        blank=True
    )
    
    # Categories
    CATEGORY_CHOICES = [
        ('GENERAL', 'General Safety'),
        ('HEALTH', 'Health & Medical'),
        ('CRIME', 'Crime & Security'),
        ('NATURAL', 'Natural Hazards'),
        ('TRANSPORTATION', 'Transportation Safety'),
        ('POLITICAL', 'Political Situation'),
        ('WOMEN', 'Women\'s Safety'),
        ('LGBTQ', 'LGBTQ+ Safety'),
        ('FAMILY', 'Family & Children Safety'),
        ('OTHER', 'Other Safety Concerns')
    ]
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='GENERAL'
    )
    
    # Risk assessment
    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low Risk'),
        ('MODERATE', 'Moderate Risk'),
        ('HIGH', 'High Risk'),
        ('EXTREME', 'Extreme Risk'),
        ('VARIABLE', 'Variable Risk'),
        ('UNKNOWN', 'Risk Level Unknown')
    ]
    risk_level = models.CharField(
        max_length=10,
        choices=RISK_LEVEL_CHOICES,
        default='LOW'
    )
    
    # Content
    summary = models.TextField(
        help_text="Brief summary of the safety information"
    )
    content = models.TextField(
        help_text="Detailed safety information, tips, and advice"
    )
    
    # Source and verification
    source = models.CharField(
        max_length=255,
        blank=True,
        help_text="Source of this safety information"
    )
    source_url = models.URLField(
        blank=True,
        help_text="URL of the source"
    )
    last_verified = models.DateField(
        null=True,
        blank=True,
        help_text="Date when this information was last verified"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether this information should be featured prominently"
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when this information should be considered outdated"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Return a string representation of the safety information.
        
        Returns:
            str: The title of the safety information
        """
        location = self.destination or self.region or "General"
        return f"{self.title} - {location}"
    
    def save(self, *args, **kwargs):
        """
        Override save method to automatically generate slug.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        if not self.slug:
            location_name = str(self.destination or self.region or "")
            slug_base = f"{self.title}-{location_name}" if location_name else self.title
            self.slug = slugify(slug_base)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """
        Get the URL for this safety information's detail view.
        
        Returns:
            str: URL for the safety information's detail page
        """
        return reverse('emergency:safety_detail', kwargs={'slug': self.slug})
    
    def get_location_display(self):
        """
        Get a human-readable representation of the safety information's location scope.
        
        Returns:
            str: Name of the destination or region, or 'General'
        """
        if self.destination:
            return str(self.destination)
        elif self.region:
            return str(self.region)
        return "General"
    
    class Meta:
        """
        Meta class for SafetyInformation.
        
        Defines ordering and verbose names.
        """
        ordering = ['-is_featured', '-updated_at']
        verbose_name = "Safety Information"
        verbose_name_plural = "Safety Information"


class EmergencyGuide(models.Model):
    """
    Represents a comprehensive emergency guide.
    
    Contains detailed guidance on handling various emergency
    situations, with step-by-step instructions.
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    
    # Location scope
    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name='emergency_guides',
        null=True,
        blank=True
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='emergency_guides',
        null=True,
        blank=True
    )
    
    # Emergency type
    EMERGENCY_TYPE_CHOICES = [
        ('MEDICAL', 'Medical Emergency'),
        ('NATURAL', 'Natural Disaster'),
        ('THEFT', 'Theft or Robbery'),
        ('LOST', 'Lost Documents/Belongings'),
        ('POLITICAL', 'Political Unrest'),
        ('TRANSPORT', 'Transportation Emergency'),
        ('ARREST', 'Legal Issues/Arrest'),
        ('GENERAL', 'General Emergency Guidelines'),
        ('OTHER', 'Other Emergency')
    ]
    emergency_type = models.CharField(
        max_length=20,
        choices=EMERGENCY_TYPE_CHOICES,
        default='GENERAL'
    )
    
    # Content
    summary = models.TextField(help_text="Brief summary of the guide")
    before_emergency = models.TextField(
        blank=True,
        help_text="Preventative measures and preparation"
    )
    during_emergency = models.TextField(
        help_text="Steps to take during the emergency"
    )
    after_emergency = models.TextField(
        blank=True,
        help_text="Follow-up actions after the emergency"
    )
    
    # Related resources
    related_services = models.ManyToManyField(
        EmergencyService,
        related_name='related_guides',
        blank=True
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Return a string representation of the emergency guide.
        
        Returns:
            str: The title of the emergency guide
        """
        return self.title
    
    def save(self, *args, **kwargs):
        """
        Override save method to automatically generate slug.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """
        Get the URL for this guide's detail view.
        
        Returns:
            str: URL for the guide's detail page
        """
        return reverse('emergency:guide_detail', kwargs={'slug': self.slug})
    
    class Meta:
        """
        Meta class for EmergencyGuide.
        
        Defines ordering and verbose names.
        """
        ordering = ['-is_featured', 'emergency_type', 'title']
        verbose_name = "Emergency Guide"
        verbose_name_plural = "Emergency Guides"
