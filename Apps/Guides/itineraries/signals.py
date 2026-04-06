"""
Signal handlers for the itineraries app.

This module contains signal handlers for automatically creating related objects
and maintaining data integrity when itinerary objects are created or modified.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta

from .models import Itinerary, ItineraryDay


@receiver(post_save, sender=Itinerary)
def create_itinerary_days(sender, instance, created, **kwargs):
    """
    Signal handler to automatically create day objects when an itinerary is created.
    
    This function is triggered after an Itinerary object is saved. If the itinerary
    is newly created, it automatically generates an ItineraryDay object for each day
    within the itinerary's date range.
    
    Args:
        sender: The model class that sent the signal (Itinerary)
        instance: The actual instance of the Itinerary that was saved
        created: Boolean flag indicating if this is a new instance (True) or an update (False)
        **kwargs: Additional keyword arguments
    
    Returns:
        None
    """
    # Only create days for newly created itineraries
    if created:
        # Calculate the number of days in the itinerary (inclusive of start and end dates)
        current_date = instance.start_date
        day_number = 1
        
        # Loop through each day in the range and create an ItineraryDay object
        while current_date <= instance.end_date:
            ItineraryDay.objects.create(
                itinerary=instance,
                day_number=day_number,
                date=current_date
            )
            
            # Move to the next day
            current_date += timedelta(days=1)
            day_number += 1


@receiver(post_save, sender=Itinerary)
def update_itinerary_days_on_date_change(sender, instance, created, **kwargs):
    """
    Signal handler to update itinerary days when dates change.
    
    When an itinerary's start or end date is modified, this function ensures
    that the corresponding day objects are adjusted accordingly. It adds missing
    days and removes extra days if needed.
    
    Args:
        sender: The model class that sent the signal (Itinerary)
        instance: The actual instance of the Itinerary that was saved
        created: Boolean flag indicating if this is a new instance
        **kwargs: Additional keyword arguments
    
    Returns:
        None
    """
    # Skip for new itineraries (already handled by create_itinerary_days)
    if created:
        return
        
    # Get existing days
    existing_days = ItineraryDay.objects.filter(itinerary=instance).order_by('day_number')
    
    # If no days exist (unusual case), create them from scratch
    if not existing_days.exists():
        create_itinerary_days(sender, instance, True, **kwargs)
        return
    
    # Calculate expected date range
    expected_dates = []
    current_date = instance.start_date
    while current_date <= instance.end_date:
        expected_dates.append(current_date)
        current_date += timedelta(days=1)
    
    # Get existing dates
    existing_dates = [day.date for day in existing_days]
    
    # Add missing days
    day_number = len(existing_days) + 1
    for date in expected_dates:
        if date not in existing_dates:
            ItineraryDay.objects.create(
                itinerary=instance,
                day_number=day_number,
                date=date
            )
            day_number += 1
    
    # Remove extra days outside the new date range
    for day in existing_days:
        if day.date < instance.start_date or day.date > instance.end_date:
            day.delete()
    
    # Renumber days to ensure they're sequential
    remaining_days = ItineraryDay.objects.filter(itinerary=instance).order_by('date')
    for i, day in enumerate(remaining_days, 1):
        if day.day_number != i:
            day.day_number = i
            day.save(update_fields=['day_number'])
