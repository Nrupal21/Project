"""
Menu app admin configuration.
Customizes Django admin interface for Category and MenuItem models.
"""
from django.contrib import admin
from .models import Category, MenuItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Category model.
    Provides list display, filters, and search capabilities.
    """
    list_display = ['name', 'is_active', 'display_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'display_order']
    ordering = ['display_order', 'name']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    """
    Admin interface for MenuItem model.
    Provides comprehensive management of menu items with filters and search.
    """
    list_display = [
        'name', 
        'category', 
        'price', 
        'dietary_type',
        'is_available', 
        'preparation_time'
    ]
    list_filter = ['category', 'dietary_type', 'is_available', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'is_available']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'description', 'image')
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'is_available', 'preparation_time')
        }),
        ('Dietary Information', {
            'fields': ('dietary_type',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
