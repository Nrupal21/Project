from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import TravelTipCategory, TravelTip, TravelTipComment, TravelTipBookmark, TravelGalleryImage

# Register your models here.

@admin.register(TravelTipCategory)
class TravelTipCategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for TravelTipCategory model.
    
    Provides a user-friendly interface for managing travel tip categories.
    """
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    date_hierarchy = 'created_at'


@admin.register(TravelTip)
class TravelTipAdmin(admin.ModelAdmin):
    """
    Admin configuration for TravelTip model.
    
    Provides a comprehensive interface for managing travel tips with filtering,
    searching, and quick-edit options.
    """
    list_display = ('title', 'author', 'category', 'status', 'is_featured', 'published_at', 'view_count')
    list_filter = ('status', 'is_featured', 'category')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    readonly_fields = ('view_count', 'created_at', 'updated_at')
    list_editable = ('is_featured', 'status')
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'author', 'category', 'content', 'excerpt', 'featured_image')
        }),
        ('Publication', {
            'fields': ('status', 'is_featured', 'published_at')
        }),
        ('Statistics', {
            'fields': ('view_count', 'created_at', 'updated_at')
        }),
    )


@admin.register(TravelTipComment)
class TravelTipCommentAdmin(admin.ModelAdmin):
    """
    Admin configuration for TravelTipComment model.
    
    Allows administrators to manage and moderate user comments on travel tips.
    """
    list_display = ('__str__', 'author', 'is_approved', 'created_at')
    list_filter = ('is_approved',)
    search_fields = ('content', 'author__username', 'author__email')
    list_editable = ('is_approved',)
    date_hierarchy = 'created_at'


@admin.register(TravelTipBookmark)
class TravelTipBookmarkAdmin(admin.ModelAdmin):
    """
    Admin configuration for TravelTipBookmark model.
    
    Displays user bookmarks of travel tips for administrative tracking.
    """
    list_display = ('user', 'tip', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'tip__title')
    date_hierarchy = 'created_at'


@admin.register(TravelGalleryImage)
class TravelGalleryImageAdmin(admin.ModelAdmin):
    """
    Admin configuration for TravelGalleryImage model.
    
    Provides an interface for managing travel gallery images with preview functionality,
    sorting options, and filtering capabilities.
    """
    list_display = ('title', 'location', 'image_preview', 'is_featured', 'display_order', 'created_at')
    list_filter = ('is_featured', 'created_at', 'location')
    search_fields = ('title', 'description', 'location')
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    list_editable = ('is_featured', 'display_order')
    fieldsets = (
        ('Image Information', {
            'fields': ('title', 'description', 'image_url', 'image_preview')
        }),
        ('Location Details', {
            'fields': ('location', 'coordinates')
        }),
        ('Display Options', {
            'fields': ('is_featured', 'display_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def image_preview(self, obj):
        """
        Generates an HTML image preview for the admin interface.
        
        Args:
            obj: The TravelGalleryImage instance
            
        Returns:
            str: HTML for displaying a thumbnail preview of the image
        """
        if obj.image_url:
            return mark_safe(f'<img src="{obj.image_url}" width="100" height="75" style="object-fit: cover;" />')
        return 'No Image'
    
    image_preview.short_description = 'Preview'
