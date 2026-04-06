"""
Admin configuration for the itineraries application.

This file defines how itinerary-related models appear in the Django admin interface,
including custom inline classes, admin actions, and field configurations.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Itinerary, ItineraryDay, Activity


class ActivityInline(admin.TabularInline):
    """
    Inline admin interface for Activity model.
    
    Allows for editing activities directly within the ItineraryDay admin page.
    """
    model = Activity
    extra = 1  # Number of empty forms to display
    fields = ('title', 'start_time', 'end_time', 'location', 'cost')


class ItineraryDayInline(admin.TabularInline):
    """
    Inline admin interface for ItineraryDay model.
    
    Allows for editing days directly within the Itinerary admin page.
    """
    model = ItineraryDay
    extra = 1
    fields = ('day_number', 'date', 'destination', 'notes')
    show_change_link = True  # Add a link to the change form


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for Itinerary model.
    
    Customizes the display, filtering, and editing of itineraries in the Django admin.
    """
    list_display = ('title', 'user', 'start_date', 'end_date', 'is_public', 'created_at')
    list_filter = ('is_public', 'start_date', 'created_at')
    search_fields = ('title', 'description', 'user__username', 'user__email')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'user', 'tour')
        }),
        (_('Dates'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Settings'), {
            'fields': ('is_public',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [ItineraryDayInline]
    
    def get_queryset(self, request):
        """
        Override the default queryset to optimize database queries.
        
        Adds select_related to avoid additional database queries when
        displaying related fields like user and tour.
        
        Args:
            request: The HTTP request object
            
        Returns:
            QuerySet: Optimized queryset for the admin list view
        """
        return super().get_queryset(request).select_related('user', 'tour')


@admin.register(ItineraryDay)
class ItineraryDayAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for ItineraryDay model.
    
    Customizes the display, filtering, and editing of itinerary days in the Django admin.
    """
    list_display = ('__str__', 'day_number', 'date', 'destination')
    list_filter = ('itinerary', 'destination')
    search_fields = ('itinerary__title', 'notes', 'destination__name')
    raw_id_fields = ('itinerary', 'destination')
    fieldsets = (
        (None, {
            'fields': ('itinerary', 'day_number', 'date', 'destination')
        }),
        (_('Details'), {
            'fields': ('accommodation_details', 'notes')
        }),
    )
    inlines = [ActivityInline]


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for Activity model.
    
    Customizes the display, filtering, and editing of activities in the Django admin.
    """
    list_display = ('title', 'get_itinerary_title', 'get_day_number', 'start_time', 'end_time', 'location')
    list_filter = ('day__itinerary', 'start_time')
    search_fields = ('title', 'description', 'location', 'booking_reference')
    raw_id_fields = ('day',)
    fieldsets = (
        (None, {
            'fields': ('day', 'title', 'description')
        }),
        (_('Schedule'), {
            'fields': ('start_time', 'end_time')
        }),
        (_('Location & Cost'), {
            'fields': ('location', 'cost')
        }),
        (_('Booking'), {
            'fields': ('booking_reference',)
        }),
    )
    
    def get_itinerary_title(self, obj):
        """
        Get the title of the parent itinerary.
        
        This is a custom admin display method to show the parent itinerary
        in the list view.
        
        Args:
            obj: The Activity object
            
        Returns:
            str: The title of the parent itinerary
        """
        return obj.day.itinerary.title
    get_itinerary_title.short_description = _("Itinerary")
    
    def get_day_number(self, obj):
        """
        Get the day number of the parent itinerary day.
        
        This is a custom admin display method to show the day number
        in the list view.
        
        Args:
            obj: The Activity object
            
        Returns:
            int: The day number of the parent itinerary day
        """
        return obj.day.day_number
    get_day_number.short_description = _("Day")
