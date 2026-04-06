"""
Review models for the TravelGuide application.

This module defines all database models related to the reviews system,
including reviews, review images, review comments, and helpful votes.
Models support relationships with Django's ContentType framework to
allow reviews on different types of content.
"""

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


# Rating choices for reviews
RATING_CHOICES = [
    (1, '★☆☆☆☆'),
    (2, '★★☆☆☆'),
    (3, '★★★☆☆'),
    (4, '★★★★☆'),
    (5, '★★★★★'),
]

# Status choices for review moderation
STATUS_CHOICES = [
    ('pending', _('Pending')),
    ('approved', _('Approved')),
    ('rejected', _('Rejected')),
]

class Review(models.Model):
    """
    Review model for storing user reviews of various content types.
    
    This model uses Django's ContentType framework to allow reviews on any type
    of content (destinations, attractions, tours, etc.). Reviews include ratings,
    text content, and moderation status.
    
    Attributes:
        user (ForeignKey): User who created the review
        content_type (ForeignKey): Type of object being reviewed (destination, tour, etc.)
        object_id (PositiveIntegerField): ID of the specific object being reviewed
        content_object (GenericForeignKey): The object being reviewed
        title (CharField): Title of the review
        content (TextField): Main content/text of the review
        rating (IntegerField): Rating from 1 to 5 stars
        created_at (DateTimeField): When the review was created
        updated_at (DateTimeField): When the review was last updated
        status (CharField): Moderation status (pending, approved, rejected)
        featured (BooleanField): Whether this is a featured review to highlight
        helpful_votes (ManyToManyField): Users who found this review helpful
    """
    # Meta class is defined at the bottom
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('User')
    )
    
    # ContentType relationships for generic relations
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        verbose_name=_('Content Type')
    )
    object_id = models.PositiveIntegerField(verbose_name=_('Object ID'))
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Review content
    title = models.CharField(
        max_length=255, 
        verbose_name=_('Title')
    )
    content = models.TextField(verbose_name=_('Content'))
    rating = models.IntegerField(
        choices=RATING_CHOICES, 
        verbose_name=_('Rating')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    # Moderation fields
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    featured = models.BooleanField(
        default=False,
        verbose_name=_('Featured')
    )
    
    # Users who found this review helpful
    helpful_votes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ReviewHelpful',
        related_name='helpful_reviews',
        verbose_name=_('Helpful Votes'),
        help_text=_('Users who marked this review as helpful')
    )
    
    class Meta:
        """Meta options for the Review model."""
        app_label = 'reviews'
        ordering = ['-created_at']
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')
        unique_together = ['user', 'content_type', 'object_id']
    
    def __str__(self):
        """
        String representation of the Review.
        
        Returns:
            str: Review title and rating
        """
        return f"{self.title} ({self.get_rating_display()})"
    
    def get_absolute_url(self):
        """
        Get URL for this review's detail page.
        
        Returns:
            str: URL to review detail page
        """
        return reverse('reviews:review_detail', kwargs={'review_id': self.id})
    
    @property
    def helpful_count(self):
        """
        Count of users who found this review helpful.
        
        Returns:
            int: Number of helpful votes
        """
        return self.helpful_votes.count()
    
    @property
    def comments_count(self):
        """
        Count of comments on this review.
        
        Returns:
            int: Number of comments
        """
        return self.comments.count()


class ReviewImage(models.Model):
    """
    Image associated with a review.
    
    This model allows users to upload multiple images to accompany their reviews,
    providing visual context and supporting evidence for their feedback.
    
    Attributes:
        review (ForeignKey): The review this image is associated with
        image (ImageField): The uploaded image file with automatic path generation
        caption (CharField): Optional descriptive text for the image
        is_primary (BooleanField): Whether this is the primary image for the review
        created_at (DateTimeField): Timestamp of when the image was uploaded
        updated_at (DateTimeField): Timestamp of when the image was last modified
    """
    review = models.ForeignKey(
        Review, 
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Review'),
        help_text=_('The review this image belongs to')
    )
    
    image = models.ImageField(
        upload_to='reviews/%Y/%m/',
        verbose_name=_('Image'),
        help_text=_('Upload an image to include with your review')
    )
    
    caption = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name=_('Caption'),
        help_text=_('Optional description for this image')
    )
    
    is_primary = models.BooleanField(
        default=False,
        verbose_name=_('Primary Image'),
        help_text=_('Set as the main image for this review')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        """Meta options for the ReviewImage model."""
        app_label = 'reviews'
        ordering = ['created_at']
        verbose_name = _('Review Image')
        verbose_name_plural = _('Review Images')
    
    def __str__(self):
        """
        String representation of the ReviewImage.
        
        Returns:
            str: Caption or default description with review ID
        """
        return self.caption if self.caption else f"Image for review #{self.review_id}"


class ReviewComment(models.Model):
    """
    Comment on a review.
    
    This model enables users to engage in discussions by adding comments to reviews.
    It supports both regular user comments and official staff responses.
    
    Attributes:
        review (ForeignKey): The review being commented on
        user (ForeignKey): User who created the comment
        parent (ForeignKey): Parent comment for threaded replies (optional)
        content (TextField): The comment text content
        is_official_response (BooleanField): Marks official business responses
        is_approved (BooleanField): Whether the comment passes moderation
        created_at (DateTimeField): When the comment was created
        updated_at (DateTimeField): When the comment was last modified
    """
    review = models.ForeignKey(
        Review, 
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('Review'),
        help_text=_('The review this comment belongs to')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_comments',
        verbose_name=_('User'),
        help_text=_('The user who created this comment')
    )
    
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name=_('Parent Comment'),
        help_text=_('Parent comment if this is a reply')
    )
    
    content = models.TextField(
        verbose_name=_('Content'),
        help_text=_('Enter your comment here')
    )
    
    is_official_response = models.BooleanField(
        default=False,
        verbose_name=_('Official Response'),
        help_text=_('Check if this is an official response from staff')
    )
    
    is_approved = models.BooleanField(
        default=True,
        verbose_name=_('Approved'),
        help_text=_('Whether this comment has been approved by moderators')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        """Meta options for the ReviewComment model."""
        app_label = 'reviews'
        ordering = ['created_at']
        verbose_name = _('Review Comment')
        verbose_name_plural = _('Review Comments')
    
    def __str__(self):
        """
        String representation of the ReviewComment.
        
        Returns:
            str: Comment excerpt with user information
        """
        return f"Comment by {self.user.username}: {self.content[:30]}..."


class ReviewHelpful(models.Model):
    """
    Tracks users who found a review helpful.
    
    This model serves as a through table for the many-to-many relationship
    between Review and User models, recording each 'helpful' vote cast by users.
    It prevents duplicate votes and maintains an audit trail of user interactions.
    
    Attributes:
        review (ForeignKey): The review that received the helpful vote
        user (ForeignKey): User who marked the review as helpful
        vote_type (CharField): Type of vote (helpful/not helpful)
        ip_address (GenericIPAddressField): IP for vote validation
        user_agent (TextField): Browser/device info for analytics
        created_at (DateTimeField): When the vote was cast
    """
    VOTE_TYPES = [
        ('helpful', _('Helpful')),
        ('not_helpful', _('Not Helpful')),
    ]
    
    review = models.ForeignKey(
        Review, 
        on_delete=models.CASCADE,
        related_name='helpful_records',
        verbose_name=_('Review'),
        help_text=_('The review that was voted on')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='helpful_votes',
        verbose_name=_('User'),
        help_text=_('User who cast the vote')
    )
    
    vote_type = models.CharField(
        max_length=20,
        choices=VOTE_TYPES,
        default='helpful',
        verbose_name=_('Vote Type'),
        help_text=_('Type of vote cast')
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP Address'),
        help_text=_('IP address of the voter')
    )
    
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('User Agent'),
        help_text=_('Browser/device information')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Created At'),
        help_text=_('When this vote was cast')
    )
    
    class Meta:
        """Meta options for the ReviewHelpful model."""
        app_label = 'reviews'
        unique_together = ['review', 'user']
        verbose_name = _('Helpful Vote')
        verbose_name_plural = _('Helpful Votes')
    
    def __str__(self):
        """
        String representation of the ReviewHelpful.
        
        Returns:
            str: Description of the vote with user and review information
        """
        return f"{self.user.username} found review #{self.review_id} helpful"
