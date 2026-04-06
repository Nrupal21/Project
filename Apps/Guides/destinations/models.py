"""
Models for the destinations app.

This module defines all database models related to travel destinations,
including regions, destinations, attractions, and related entities.

The model hierarchy follows a geographical organization:
- Region: Represents larger geographical areas (countries, states, etc.)
- Destination: Specific cities or locations within regions
- Attraction: Points of interest within destinations

Additional models support these main entities:
- DestinationImage: Manages photos for destinations
- Season: Defines optimal visiting periods for destinations

These models form the foundation of the travel guide system,
providing structured data for the web interface and API endpoints.

The Destination model includes an approval workflow where destinations
created by local guides must be reviewed and approved by managers or admins
before becoming publicly visible. Upon approval, the local guide who created
the destination receives reward points.

This file also includes the PendingDestination model which serves as a staging area
for destinations uploaded by local guides. When a pending destination is approved,
it gets transferred to the main Destination table.
"""

from django.db import models
from django.urls import reverse
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify
from core.managers import DestinationManager, LocationBasedManager, ApprovalWorkflowManager
from core.utils import DataValidationUtils

# Import Review if the reviews app is available, otherwise use a placeholder
try:
    from reviews.models import Review
except ImportError:
    # Create a placeholder for Review if it's not available
    Review = None

class Region(models.Model):
    """
    Represents a geographical region that contains multiple destinations.
    
    A region can be a country, state, province, or any other geographical area
    that makes sense for travel planning and organization.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """Return a string representation of the region."""
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to ensure slug is created from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    class Meta:
        """Meta options for the Region model."""
        ordering = ['name']
        verbose_name = 'Region'
        verbose_name_plural = 'Regions'


class Destination(models.Model):
    """
    Represents a travel destination such as a city or specific location.
    
    A destination belongs to a region and can contain multiple attractions.
    It includes geographical information like latitude/longitude for mapping
    and location-based features.
    
    The approval workflow ensures that destinations uploaded by local guides
    undergo review by managers or administrators before becoming visible on the main site.
    Upon approval, the local guide who created the destination receives reward points.
    
    This model uses the enhanced DestinationManager for optimized queries and
    integrates with the core utilities for data validation and consistency.
    """
    
    # Custom manager with enhanced functionality
    objects = DestinationManager()
    # Destination approval status choices
    class ApprovalStatus(models.TextChoices):
        """
        Define possible approval statuses for a destination.
        
        This enumeration defines the various states a destination can be in
        during the review and approval workflow.
        """
        PENDING = 'PENDING', _('Pending Approval')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
    
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='destinations')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    short_description = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Location fields
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Approval workflow fields
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices, 
        default=ApprovalStatus.PENDING,
        help_text=_('Current review status of this destination')
    )
    created_by = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_destinations',
        help_text=_('User who created this destination')
    )
    reviewed_by = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_destinations',
        help_text=_('Manager or admin who reviewed this destination')
    )
    review_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_('When this destination was reviewed')
    )
    rejection_reason = models.TextField(
        null=True, 
        blank=True,
        help_text=_('Reason for rejection, if applicable')
    )
    
    # Meta fields
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """Return a string representation of the destination."""
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to ensure slug is created from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def approve(self, reviewed_by):
        """
        Approve this destination and award points to its creator.
        
        This method changes the approval status to approved, records who
        approved it and when, and awards reward points to the local guide
        who created the destination.
        
        Args:
            reviewed_by: Manager/Admin user who approved the destination
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not reviewed_by.is_manager and not reviewed_by.is_admin:
            return False
            
        if self.approval_status == self.ApprovalStatus.APPROVED:
            return False
            
        try:
            self.approval_status = self.ApprovalStatus.APPROVED
            self.reviewed_by = reviewed_by
            self.review_date = timezone.now()
            self.save(update_fields=['approval_status', 'reviewed_by', 'review_date'])
            
            # Award points to the creator if they exist and are a local guide
            if self.created_by and self.created_by.role == self.created_by.Role.LOCAL_GUIDE:
                # Import here to avoid circular imports
                from rewards.models import RewardPoints, RewardActivity
                
                # Award 50 points for an approved destination
                RewardPoints.add_points(
                    user=self.created_by,
                    activity=RewardActivity.DESTINATION_APPROVAL,
                    points=50,
                    description=f"Destination '{self.name}' approved",
                    reference_type='Destination',
                    reference_id=str(self.id)
                )
            
            return True
        except Exception:
            return False
    
    def reject(self, reviewed_by, reason):
        """
        Reject this destination.
        
        This method changes the approval status to rejected, records
        who rejected it and when, and stores the rejection reason.
        
        Args:
            reviewed_by: Manager/Admin user who rejected the destination
            reason: Reason for rejection
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not reviewed_by.is_manager and not reviewed_by.is_admin:
            return False
            
        if not reason:
            return False
            
        try:
            self.approval_status = self.ApprovalStatus.REJECTED
            self.reviewed_by = reviewed_by
            self.review_date = timezone.now()
            self.rejection_reason = reason
            self.save(update_fields=[
                'approval_status', 'reviewed_by', 'review_date', 'rejection_reason'
            ])
            return True
        except Exception:
            return False
    
    class Meta:
        """Meta options for the Destination model."""
        ordering = ['name']
        verbose_name = 'Destination'
        verbose_name_plural = 'Destinations'


class DestinationImage(models.Model):
    """
    Stores images associated with a destination.
    
    Each destination can have multiple images, with one designated as primary.
    The primary image is used as the main visual representation of the destination
    in lists and cards.
    """
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='destinations/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        """Return a string representation of the destination image."""
        return f"Image for {self.destination.name}"
    
    class Meta:
        """Meta options for the DestinationImage model."""
        ordering = ['-is_primary', 'created_at']
        verbose_name = 'Destination Image'
        verbose_name_plural = 'Destination Images'


class Season(models.Model):
    """
    Represents a season or time period for visiting destinations.
    
    Seasons are used to indicate the best times to visit destinations
    based on weather, crowds, events, etc.
    """
    destination = models.ForeignKey(
        'Destination',
        on_delete=models.CASCADE,
        related_name='seasons',
        null=True,
        blank=True,
        help_text='The destination this season belongs to (optional)'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    start_month = models.PositiveSmallIntegerField(
        help_text='Numeric month (1-12) when the season starts'
    )
    end_month = models.PositiveSmallIntegerField(
        help_text='Numeric month (1-12) when the season ends'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """Return a string representation of the season."""
        if self.destination:
            return f"{self.name} - {self.destination.name}"
        return self.name
    
    class Meta:
        """Meta options for the Season model."""
        ordering = ['start_month']
        verbose_name = 'Season'
        verbose_name_plural = 'Seasons'


class Attraction(models.Model):
    """
    Represents a specific point of interest within a destination.
    
    Attractions are specific places to visit at a destination such as
    landmarks, museums, restaurants, or natural features. Each attraction belongs
    to a specific destination and contains location data for mapping and detailed
    information for visitors.
    
    This model is used by the AttractionViewSet in views.py to provide API endpoints
    for CRUD operations. The AttractionViewSet uses a queryset filter for is_active=True
    to ensure only published attractions are shown by default in the API.
    
    The model integrates with LocationBasedManager for geographical queries and
    uses core utilities for data validation and consistency.
    
    Note on API Registration:
    When registering this model's viewset with the DefaultRouter, either provide a
    class-level queryset attribute in the viewset or specify the basename parameter
    (e.g., basename='attraction') to prevent router registration errors.
    """
    
    # Custom manager with location-based functionality
    objects = LocationBasedManager()
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='attractions')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """Return a string representation of the attraction."""
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to ensure slug is created from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    class Meta:
        """Meta options for the Attraction model."""
        ordering = ['name']
        verbose_name = 'Attraction'
        verbose_name_plural = 'Attractions'


class AttractionImage(models.Model):
    """Stores images associated with an attraction.
    
    Each attraction can have multiple images, with one designated as primary.
    The primary image is used as the main visual representation of the attraction
    in lists and detail views.
    """
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='attractions/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        """Return a string representation of the attraction image."""
        return f"Image for {self.attraction.name}"
    
    class Meta:
        """Meta options for the AttractionImage model."""
        ordering = ['-is_primary', 'created_at']
        verbose_name = 'Attraction Image'
        verbose_name_plural = 'Attraction Images'


class PendingDestination(models.Model):
    """
    Represents a travel destination submitted by a local guide awaiting approval.
    
    This model serves as a staging area for new destinations before they are approved
    and transferred to the main Destination table. It contains all the same fields
    as the Destination model to ensure a smooth transfer of data upon approval.
    
    When a destination is approved, its data is transferred to the Destination table
    and the PendingDestination record is marked as approved. If rejected, the record remains
    with the rejection reason for reference and potential resubmission.
    
    This model uses the ApprovalWorkflowManager for handling approval processes
    and integrates with core utilities for data validation and consistency.
    
    Key workflow:
    1. Local guide submits destination → stored as PendingDestination with PENDING status
    2. Manager/admin reviews the submission in the admin interface
    3. If approved → data transferred to Destination table, guide receives points
    4. If rejected → status updated, guide receives feedback for improvement
    """
    
    # Custom manager with approval workflow functionality
    objects = ApprovalWorkflowManager()
    # Status choices for pending destinations
    class ApprovalStatus(models.TextChoices):
        """
        Define possible approval statuses for a pending destination.
        
        This enumeration defines the various states a pending destination can be in
        during the review and approval workflow.
        """
        PENDING = 'PENDING', _('Pending Approval')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
    
    # Basic information fields - mirrors the structure of Destination model
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='pending_destinations')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    short_description = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Location fields
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Approval workflow fields
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices, 
        default=ApprovalStatus.PENDING,
        help_text=_('Current review status of this pending destination')
    )
    created_by = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='pending_destinations',
        help_text=_('Local guide who submitted this destination')
    )
    reviewed_by = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_pending_destinations',
        help_text=_('Manager or admin who reviewed this destination')
    )
    review_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_('When this destination was reviewed')
    )
    rejection_reason = models.TextField(
        null=True, 
        blank=True,
        help_text=_('Reason for rejection, if applicable')
    )
    
    # Meta fields
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """Return a string representation of the pending destination."""
        return f"{self.name} (Pending)"
    
    def save(self, *args, **kwargs):
        """Override save to ensure slug is created from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def approve_and_transfer(self, reviewed_by):
        """
        Approve this pending destination and transfer it to the main Destination table.
        
        This method performs the following steps:
        1. Changes the approval status to APPROVED
        2. Records the reviewer and review date
        3. Creates a new Destination record with the data from this PendingDestination
        4. Awards points to the local guide who created the destination
        5. Returns the newly created Destination object
        
        Args:
            reviewed_by: Manager/Admin user who approved the destination
            
        Returns:
            Destination: The newly created Destination object, or None if unsuccessful
        """
        # Check if reviewer has permission
        if not reviewed_by.is_manager and not reviewed_by.is_admin:
            return None
            
        # Check if already approved
        if self.approval_status == self.ApprovalStatus.APPROVED:
            return None
            
        try:
            # Update approval status for this pending destination
            self.approval_status = self.ApprovalStatus.APPROVED
            self.reviewed_by = reviewed_by
            self.review_date = timezone.now()
            self.save(update_fields=['approval_status', 'reviewed_by', 'review_date'])
            
            # Create a new Destination from this PendingDestination data
            new_destination = Destination.objects.create(
                region=self.region,
                name=self.name,
                slug=self.slug,
                short_description=self.short_description,
                description=self.description,
                latitude=self.latitude,
                longitude=self.longitude,
                city=self.city,
                country=self.country,
                price=self.price,
                created_by=self.created_by,
                reviewed_by=self.reviewed_by,
                review_date=self.review_date,
                approval_status=Destination.ApprovalStatus.APPROVED,
                is_active=True,
                is_featured=False
            )
            
            # Transfer any images from the pending destination to the new destination
            self._transfer_images(new_destination)
            
            # Award points to the creator if they exist and are a local guide
            if self.created_by and hasattr(self.created_by, 'role') and self.created_by.role == getattr(self.created_by, 'Role', {}).get('LOCAL_GUIDE'):
                # Import here to avoid circular imports
                try:
                    from rewards.models import RewardPoints, RewardActivity
                    
                    # Award 50 points for an approved destination
                    RewardPoints.add_points(
                        user=self.created_by,
                        activity=RewardActivity.DESTINATION_APPROVAL,
                        points=50,
                        description=f"Destination '{self.name}' approved",
                        reference_type='Destination',
                        reference_id=str(new_destination.id)
                    )
                except (ImportError, AttributeError):
                    # Handle case where rewards system is not available
                    pass
            
            return new_destination
            
        except Exception as e:
            # Log the error in a production environment
            print(f"Error approving destination: {e}")
            return None
    
    def _transfer_images(self, destination):
        """
        Transfer all images from this pending destination to the approved destination.
        
        Args:
            destination: The approved Destination object to transfer images to
        """
        # Get all images for this pending destination
        pending_images = PendingDestinationImage.objects.filter(pending_destination=self)
        
        # Create new DestinationImage objects for each pending image
        for pending_image in pending_images:
            DestinationImage.objects.create(
                destination=destination,
                image=pending_image.image,
                caption=pending_image.caption,
                is_primary=pending_image.is_primary
            )
    
    def reject(self, reviewed_by, reason):
        """
        Reject this pending destination.
        
        This method changes the approval status to rejected, records
        who rejected it and when, and stores the rejection reason.
        
        Args:
            reviewed_by: Manager/Admin user who rejected the destination
            reason: Reason for rejection
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if reviewer has permission
        if not reviewed_by.is_manager and not reviewed_by.is_admin:
            return False
            
        # Check if reason is provided
        if not reason:
            return False
            
        try:
            self.approval_status = self.ApprovalStatus.REJECTED
            self.reviewed_by = reviewed_by
            self.review_date = timezone.now()
            self.rejection_reason = reason
            self.save(update_fields=[
                'approval_status', 'reviewed_by', 'review_date', 'rejection_reason'
            ])
            return True
        except Exception:
            return False
    
    class Meta:
        """Meta options for the PendingDestination model."""
        ordering = ['-created_at']
        verbose_name = 'Pending Destination'
        verbose_name_plural = 'Pending Destinations'


class PendingDestinationImage(models.Model):
    """
    Stores images associated with a pending destination.
    
    Each pending destination can have multiple images, with one designated as primary.
    When a pending destination is approved and transferred to the main Destination table,
    these images are also transferred to the DestinationImage table.
    
    The image upload process includes:
    1. Upload to the pending_destinations/ media directory
    2. Association with a specific PendingDestination
    3. Optional designation as the primary image
    4. Transfer to the main DestinationImage model upon approval
    """
    pending_destination = models.ForeignKey(
        PendingDestination, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to='pending_destinations/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        """Return a string representation of the pending destination image."""
        return f"Image for {self.pending_destination.name}"
    
    class Meta:
        """Meta options for the PendingDestinationImage model."""
        ordering = ['-is_primary', 'created_at']
        verbose_name = 'Pending Destination Image'
        verbose_name_plural = 'Pending Destination Images'
