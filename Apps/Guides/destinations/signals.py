"""
Signal handlers for the destinations app.

This module contains signal handlers for the destinations application.
"""
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Destination, Region, Attraction, Season, DestinationImage, AttractionImage

@receiver(pre_save, sender=Region)
def set_region_slug(sender, instance, **kwargs):
    """
    Automatically set the slug for a Region if not provided.
    
    Args:
        sender: The model class that sent the signal.
        instance: The actual instance being saved.
        **kwargs: Additional keyword arguments.
    """
    if not instance.slug:
        instance.slug = slugify(instance.name)

@receiver(pre_save, sender=Destination)
def set_destination_slug(sender, instance, **kwargs):
    """
    Automatically set the slug for a Destination if not provided.
    
    Args:
        sender: The model class that sent the signal.
        instance: The actual instance being saved.
        **kwargs: Additional keyword arguments.
    """
    if not instance.slug:
        base_slug = slugify(instance.name)
        instance.slug = base_slug
        
        # If a destination with this slug already exists, append a number
        counter = 1
        while Destination.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{base_slug}-{counter}"
            counter += 1

@receiver(pre_save, sender=Attraction)
@receiver(pre_save, sender=Season)
def update_timestamps(sender, instance, **kwargs):
    """
    Update timestamps when saving models.
    
    Args:
        sender: The model class that sent the signal.
        instance: The actual instance being saved.
        **kwargs: Additional keyword arguments.
    """
    # This is handled automatically by Django's auto_now and auto_now_add
    pass

@receiver(pre_delete, sender=DestinationImage)
def delete_destination_image_file(sender, instance, **kwargs):
    """
    Delete image files when a DestinationImage is deleted.
    
    Args:
        sender: The model class that sent the signal.
        instance: The actual instance being deleted.
        **kwargs: Additional keyword arguments.
    """
    if instance.image:
        # Delete the image file from storage
        instance.image.delete(save=False)

@receiver(pre_delete, sender=AttractionImage)
def delete_attraction_image_file(sender, instance, **kwargs):
    """
    Delete image files when an AttractionImage is deleted.
    
    Args:
        sender: The model class that sent the signal.
        instance: The actual instance being deleted.
        **kwargs: Additional keyword arguments.
    """
    if instance.image:
        # Delete the image file from storage
        instance.image.delete(save=False)
