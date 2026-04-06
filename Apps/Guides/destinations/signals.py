"""
Signals for the destinations app.
"""
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Region, Destination, Attraction

@receiver(pre_save, sender=Region)
def region_pre_save(sender, instance, **kwargs):
    """Ensure slug is set for Region."""
    if not instance.slug:
        instance.slug = slugify(instance.name)

@receiver(pre_save, sender=Destination)
def destination_pre_save(sender, instance, **kwargs):
    """Ensure slug is set for Destination."""
    if not instance.slug:
        instance.slug = slugify(instance.name)
    
    # Ensure only one primary image per destination
    if instance.pk:
        if instance.images.filter(is_primary=True).exists():
            instance.images.filter(is_primary=True).update(is_primary=False)

@receiver(pre_save, sender=Attraction)
def attraction_pre_save(sender, instance, **kwargs):
    """Ensure slug is set for Attraction."""
    if not instance.slug:
        instance.slug = slugify(instance.name)
