"""
Admin configuration for the tours app.

This module registers the tour models with the Django admin interface.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    TourCategory, Tour, TourImage, TourItinerary, TourInclusion, TourReview
)


class TourImageInline(admin.TabularInline):
    """Inline admin for TourImage model."""
    model = TourImage
    extra = 1
    fields = ('image', 'caption', 'is_primary', 'order')
    readonly_fields = ('created_at',)


class TourItineraryInline(admin.TabularInline):
    """Inline admin for TourItinerary model."""
    model = TourItinerary
    extra = 1
    fields = ('day_number', 'title', 'description', 'meals', 'accommodation')
    ordering = ('day_number',)


class TourInclusionInline(admin.TabularInline):
    """Inline admin for TourInclusion model."""
    model = TourInclusion
    extra = 1
    fields = ('name', 'description', 'is_included')


@admin.register(TourCategory)
class TourCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for TourCategory model."""
    list_display = ('name', 'slug', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    """Admin configuration for Tour model."""
    list_display = ('title', 'destination', 'category', 'price', 'is_featured', 'is_active')
    list_filter = ('is_featured', 'is_active', 'category', 'difficulty')
    search_fields = ('title', 'description', 'destination__name')
    list_editable = ('is_featured', 'is_active', 'price')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'duration_display')
    inlines = [TourImageInline, TourItineraryInline, TourInclusionInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'destination', 'category', 'short_description', 'description')
        }),
        ('Pricing & Duration', {
            'fields': ('price', 'discount_price', 'duration_days', 'duration_nights', 'duration_display')
        }),
        ('Tour Details', {
            'fields': ('max_group_size', 'difficulty')
        }),
        ('Status & Metadata', {
            'fields': ('is_featured', 'is_active', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset to reduce database queries."""
        return super().get_queryset(request).select_related('destination', 'category')


@admin.register(TourImage)
class TourImageAdmin(admin.ModelAdmin):
    """Admin configuration for TourImage model."""
    list_display = ('__str__', 'tour', 'is_primary', 'order', 'created_at')
    list_filter = ('is_primary',)
    list_editable = ('is_primary', 'order')
    search_fields = ('tour__title', 'caption')
    readonly_fields = ('created_at',)


@admin.register(TourItinerary)
class TourItineraryAdmin(admin.ModelAdmin):
    """Admin configuration for TourItinerary model."""
    list_display = ('__str__', 'tour', 'day_number')
    list_filter = ('tour',)
    search_fields = ('tour__title', 'title', 'description')
    ordering = ('tour', 'day_number')


@admin.register(TourInclusion)
class TourInclusionAdmin(admin.ModelAdmin):
    """Admin configuration for TourInclusion model."""
    list_display = ('name', 'tour', 'is_included')
    list_filter = ('is_included', 'tour')
    search_fields = ('name', 'description', 'tour__title')
    list_editable = ('is_included',)


@admin.register(TourReview)
class TourReviewAdmin(admin.ModelAdmin):
    """Admin configuration for TourReview model."""
    list_display = ('tour', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating', 'created_at')
    search_fields = ('tour__title', 'user__username', 'comment')
    list_editable = ('is_approved',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        """Optimize queryset to reduce database queries."""
        return super().get_queryset(request).select_related('tour', 'user')
