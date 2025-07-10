"""
Admin configuration for the destinations app.

This module registers the models from the destinations app with the Django admin interface.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Region, Destination, DestinationImage,
    Season, Attraction, AttractionImage
)

# Inline admin classes for related models
class DestinationImageInline(admin.StackedInline):
    """
    Inline admin for managing destination images.
    
    Allows adding and editing images directly from the destination admin page.
    """
    model = DestinationImage
    extra = 1
    readonly_fields = ['preview_image']
    
    def preview_image(self, obj):
        """
        Display a preview of the image in the admin.
        
        Args:
            obj: The DestinationImage instance
            
        Returns:
            str: HTML for the image preview
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "No image"
    preview_image.short_description = 'Preview'

class SeasonInline(admin.StackedInline):
    """
    Inline admin for managing seasons.
    
    Allows adding and editing seasons directly from the destination admin page.
    """
    model = Season
    extra = 1

class AttractionImageInline(admin.StackedInline):
    """
    Inline admin for managing attraction images.
    
    Allows adding and editing images directly from the attraction admin page.
    """
    model = AttractionImage
    extra = 1
    readonly_fields = ['preview_image']
    
    def preview_image(self, obj):
        """
        Display a preview of the image in the admin.
        
        Args:
            obj: The AttractionImage instance
            
        Returns:
            str: HTML for the image preview
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "No image"
    preview_image.short_description = 'Preview'

# Main admin classes
@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    """Admin interface for the Region model."""
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    """Admin interface for the Destination model."""
    list_display = ('name', 'city', 'country', 'is_featured', 'is_active', 'created_at')
    list_filter = ('is_featured', 'is_active', 'region', 'created_at')
    search_fields = ('name', 'city', 'country', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    inlines = [DestinationImageInline, SeasonInline]
    actions = ['quick_add_destination']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'region', 'description', 'short_description')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude', 'address', 'city', 'country', 'postal_code')
        }),
        ('Status', {
            'fields': ('is_featured', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def quick_add_view(self, request):
        """View for the quick add form."""
        from django.shortcuts import render
        from django import forms
        from django.contrib import messages
        from django.utils.text import slugify
        
        class QuickDestinationForm(forms.Form):
            """Simple form for quick destination addition."""
            name = forms.CharField(max_length=200, required=True)
            region = forms.ModelChoiceField(
                queryset=Region.objects.all(),
                required=True,
                help_text="Select the region for this destination"
            )
            short_description = forms.CharField(
                widget=forms.Textarea(attrs={'rows': 3}),
                required=False,
                help_text="A brief description (optional)"
            )
            
            def clean_name(self):
                name = self.cleaned_data.get('name')
                if Destination.objects.filter(name__iexact=name).exists():
                    raise forms.ValidationError("A destination with this name already exists.")
                return name
        
        if request.method == 'POST':
            form = QuickDestinationForm(request.POST)
            if form.is_valid():
                destination = Destination(
                    name=form.cleaned_data['name'],
                    slug=slugify(form.cleaned_data['name']),
                    region=form.cleaned_data['region'],
                    short_description=form.cleaned_data.get('short_description', '')
                )
                destination.save()
                self.message_user(
                    request,
                    f'Successfully added destination: {destination.name}',
                    messages.SUCCESS
                )
                # Redirect to the change form for the new destination
                from django.http import HttpResponseRedirect
                from django.urls import reverse
                return HttpResponseRedirect(
                    reverse('admin:destinations_destination_change', args=[destination.id])
                )
        else:
            form = QuickDestinationForm()
        
        return render(
            request,
            'admin/destinations/quick_add_destination.html',
            {
                'title': 'Quick Add Destination',
                'form': form,
                'opts': self.model._meta,
                'media': self.media,
            }
        )
    
    def quick_add_destination(self, request, queryset):
        """Admin action that redirects to the quick add view."""
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(
            reverse('admin:quick_add_destination')
        )
    quick_add_destination.short_description = "Quick add new destination"
    
    def get_urls(self):
        """
        Add custom URLs for the quick add action.
        """
        from django.urls import path
        
        urls = super().get_urls()
        custom_urls = [
            path(
                'quick-add/',
                self.admin_site.admin_view(self.quick_add_view),
                name='quick_add_destination',
            ),
        ]
        return custom_urls + urls

@admin.register(Attraction)
class AttractionAdmin(admin.ModelAdmin):
    """Admin interface for the Attraction model."""
    list_display = ('name', 'destination', 'category', 'is_featured', 'created_at')
    list_filter = ('category', 'is_featured', 'destination', 'created_at')
    search_fields = ('name', 'description', 'address', 'city', 'country')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AttractionImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'destination', 'category', 'description')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude', 'address', 'opening_hours', 'entry_fee')
        }),
        ('Contact Information', {
            'fields': ('website', 'contact_phone', 'contact_email')
        }),
        ('Status', {
            'fields': ('is_featured',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    """
    Admin interface for the Season model.
    """
    list_display = ('name', 'destination', 'season_range', 'is_peak_season')
    list_filter = ('is_peak_season', 'destination')
    search_fields = ('name', 'description', 'destination__name')
    
    def season_range(self, obj):
        """
        Display the season range in a more readable format.
        
        Args:
            obj: The Season instance
            
        Returns:
            str: Formatted season range
        """
        return f"{obj.get_month_name(obj.start_month)} - {obj.get_month_name(obj.end_month)}"
    season_range.short_description = 'Season Range'

# Register models that don't need custom admin classes
admin.site.register(DestinationImage)
admin.site.register(AttractionImage)
