"""
Signals for the reviews app.

This module defines signal handlers for the review-related models to handle
various events like saving, deleting, or updating reviews and related objects.
"""

from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import Review, ReviewImage, ReviewComment, ReviewHelpful


@receiver(post_save, sender=Review)
def handle_review_save(sender, instance, created, **kwargs):
    """
    Handle post-save signals for Review model.
    
    This function is called after a Review is saved. It performs the following actions:
    - Updates the review count on the related content object
    - Recalculates the average rating for the content object
    - Sends notifications to relevant users
    
    Args:
        sender: The model class (Review)
        instance: The actual instance being saved
        created (bool): Whether this is a new record or an update
        **kwargs: Additional arguments
    """
    if instance.content_object and hasattr(instance.content_object, 'update_rating'):
        instance.content_object.update_rating()
    
    # If this is a new review or status changed to approved, notify content owner
    if created or instance.tracker.has_changed('status'):
        if instance.status == 'approved' and hasattr(instance.content_object, 'user'):
            content_owner = instance.content_object.user
            if content_owner != instance.user:
                # TODO: Implement notification system
                pass


@receiver(pre_delete, sender=ReviewImage)
def delete_review_image_file(sender, instance, **kwargs):
    """
    Delete the image file when a ReviewImage is deleted.
    
    This ensures that when a ReviewImage is deleted from the database,
    its associated image file is also removed from the storage.
    
    Args:
        sender: The model class (ReviewImage)
        instance: The actual instance being deleted
        **kwargs: Additional arguments
    """
    if instance.image:
        # Delete the image file from storage
        storage = instance.image.storage
        if storage.exists(instance.image.name):
            storage.delete(instance.image.name)
    
    # If this was the primary image, set a new primary if available
    if instance.is_primary:
        review = instance.review
        other_images = review.images.exclude(id=instance.id)
        if other_images.exists():
            new_primary = other_images.first()
            new_primary.is_primary = True
            new_primary.save(update_fields=['is_primary'])


@receiver(post_save, sender=ReviewComment)
def handle_comment_notification(sender, instance, created, **kwargs):
    """
    Handle notifications for new comments on reviews.
    
    This function sends notifications to the review author when someone
    comments on their review, unless it's the author themselves.
    
    Args:
        sender: The model class (ReviewComment)
        instance: The actual comment instance
        created (bool): Whether this is a new comment
        **kwargs: Additional arguments
    """
    if created and instance.user != instance.review.user:
        # TODO: Implement notification system
        pass


@receiver(m2m_changed, sender=Review.helpful_votes.through)
def handle_helpful_vote(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Handle when a user marks a review as helpful.
    
    This function is triggered when the many-to-many relationship for
    helpful votes is changed. It updates the review's helpful count.
    
    Args:
        sender: The intermediate model class
        instance: The Review instance
        action (str): The type of action (pre_add, post_add, pre_remove, post_remove)
        reverse (bool): Whether the relation is reversed
        model: The User model class
        pk_set: Set of primary keys being added/removed
        **kwargs: Additional arguments
    """
    if action in ['post_add', 'post_remove']:
        # Update the helpful count on the review
        if not reverse:
            instance.save(update_fields=['helpful_count'])
        else:
            # Handle the reverse relation (from User.helpful_reviews)
            for review_id in pk_set:
                try:
                    review = Review.objects.get(pk=review_id)
                    review.save(update_fields=['helpful_count'])
                except Review.DoesNotExist:
                    pass


@receiver(post_save, sender=ReviewHelpful)
def handle_review_helpful_save(sender, instance, created, **kwargs):
    """
    Update the review's helpful count when a ReviewHelpful is saved.
    
    This ensures the denormalized helpful_count field stays in sync with
    the actual number of helpful votes.
    
    Args:
        sender: The model class (ReviewHelpful)
        instance: The actual instance being saved
        created (bool): Whether this is a new record
        **kwargs: Additional arguments
    """
    if created:
        review = instance.review
        review.helpful_count = review.helpful_votes.count()
        review.save(update_fields=['helpful_count'])


@receiver(pre_delete, sender=ReviewHelpful)
def handle_review_helpful_delete(sender, instance, **kwargs):
    """
    Update the review's helpful count when a ReviewHelpful is deleted.
    
    Args:
        sender: The model class (ReviewHelpful)
        instance: The actual instance being deleted
        **kwargs: Additional arguments
    """
    review = instance.review
    review.helpful_count = review.helpful_votes.count() - 1  # This vote is about to be deleted
    review.save(update_fields=['helpful_count'])


def connect_signals():
    """Connect all signal handlers."""
    # Signals are connected using the @receiver decorator
    pass
