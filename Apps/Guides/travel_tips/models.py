"""
Models for the travel_tips app.

This module defines the database models for managing travel tips, their categories, and gallery images.
Each model includes comprehensive documentation and follows Django best practices.
"""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model

# Get the user model to use for the author field
User = get_user_model()


class TravelTipCategory(models.Model):
    """
    Represents a category for organizing travel tips.
    
    Categories help users browse tips by topic, such as 'Packing', 'Budget Travel', etc.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the category (e.g., 'Packing', 'Budget Travel')"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        help_text="URL-friendly version of the category name"
    )
    description = models.TextField(
        blank=True,
        help_text="Brief description of the category"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Name of the icon to represent this category (from your icon library)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Travel Tip Category"
        verbose_name_plural = "Travel Tip Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Automatically generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return the URL for this category's detail view."""
        return reverse('travel_tips:category_detail', kwargs={'slug': self.slug})


class TravelTip(models.Model):
    """
    Represents a single travel tip or guide.
    
    Each tip contains helpful information for travelers, organized by category.
    Tips can be written by staff members or experienced travelers.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(
        max_length=200,
        help_text="Title of the travel tip"
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        help_text="URL-friendly version of the title"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='travel_tips',
        help_text="Author who created this tip"
    )
    category = models.ForeignKey(
        'TravelTipCategory',
        on_delete=models.SET_NULL,
        null=True,
        related_name='travel_tips',
        help_text="Category this tip belongs to"
    )
    content = models.TextField(
        help_text="Main content of the travel tip (supports Markdown)"
    )
    excerpt = models.TextField(
        blank=True,
        help_text="Brief summary of the tip (if empty, first 200 chars of content will be used)"
    )
    featured_image = models.ImageField(
        upload_to='travel_tips/images/%Y/%m/',
        blank=True,
        null=True,
        help_text="Featured image for this tip"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Publication status of the tip"
    )
    view_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this tip has been viewed"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether this tip should be featured on the homepage"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this tip was published (null if draft)"
    )
    
    class Meta:
        verbose_name = "Travel Tip"
        verbose_name_plural = "Travel Tips"
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['view_count']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """
        Custom save method to handle slug generation and excerpt.
        """
        if not self.slug:
            self.slug = slugify(self.title)
            
        # If excerpt is empty, use first 200 chars of content
        if not self.excerpt and self.content:
            self.excerpt = self.content[:200] + ('...' if len(self.content) > 200 else '')
            
        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return the URL for this tip's detail view."""
        return reverse('travel_tips:detail', kwargs={'slug': self.slug})
    
    def increment_view_count(self):
        """Increment the view count for this tip."""
        self.view_count = models.F('view_count') + 1
        self.save(update_fields=['view_count'])


class TravelTipComment(models.Model):
    """
    Represents a comment on a travel tip.
    
    Allows users to share their experiences, ask questions, or provide feedback.
    """
    tip = models.ForeignKey(
        TravelTip,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="The travel tip this comment is about"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='travel_tip_comments',
        help_text="User who wrote the comment"
    )
    content = models.TextField(
        help_text="The comment text"
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Whether this comment has been approved by a moderator"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Travel Tip Comment"
        verbose_name_plural = "Travel Tip Comments"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.author} on {self.tip}"


class TravelTipBookmark(models.Model):
    """
    Represents a user's bookmark/save of a travel tip.
    
    Allows users to save tips for later reference.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_tips',
        help_text="User who saved the tip"
    )
    tip = models.ForeignKey(
        TravelTip,
        on_delete=models.CASCADE,
        related_name='saved_by',
        help_text="The saved travel tip"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Travel Tip Bookmark"
        verbose_name_plural = "Travel Tip Bookmarks"
        unique_together = ['user', 'tip']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} saved {self.tip}"


class TravelGalleryImage(models.Model):
    """
    Represents an image in the travel gallery.
    
    This model stores images for the travel gallery section, allowing for a
    dynamic display of beautiful travel destinations and experiences.
    """
    title = models.CharField(
        max_length=200,
        help_text="Title of the gallery image"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what the image shows or the location depicted"
    )
    image_url = models.URLField(
        help_text="URL to the image (external hosting or CDN)"
    )
    location = models.CharField(
        max_length=200,
        help_text="Location shown in the image (e.g., 'Bali, Indonesia')"
    )
    coordinates = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional GPS coordinates for the location (e.g., '8.3405, 115.0920')"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether this image should be featured prominently in the gallery"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in which this image should appear in the gallery (lower numbers first)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Travel Gallery Image"
        verbose_name_plural = "Travel Gallery Images"
        ordering = ['display_order', '-created_at']
        indexes = [
            models.Index(fields=['is_featured']),
            models.Index(fields=['display_order']),
        ]
    
    def __str__(self):
        """
        Returns a string representation of this gallery image.
        
        Returns:
            str: The title and location of the image
        """
        return f"{self.title} - {self.location}"
        
    def get_absolute_url(self):
        """
        Return the URL for this gallery image's detail view.
        
        Returns:
            str: URL for the detail view of this image
        """
        return reverse('travel_tips:gallery_detail', kwargs={'pk': self.pk})
