from django.contrib import admin
from django.utils.html import format_html
from .models import Region, Destination, DestinationImage, Season, Attraction

# Register your models here.

class DestinationImageInline(admin.TabularInline):
    """Inline for destination images in the admin."""
    model = DestinationImage
    extra = 1
    fields = ('image', 'caption', 'is_primary')
    readonly_fields = ('preview_image',)
    
    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.image.url)
        return "No image"
    preview_image.short_description = 'Preview'

class SeasonInline(admin.TabularInline):
    """Inline for seasons in the admin."""
    model = Season
    extra = 1
    fields = ('name', 'start_month', 'end_month', 'description', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True

class AttractionInline(admin.TabularInline):
    """Inline for attractions in the admin."""
    model = Attraction
    extra = 1
    fields = ('name', 'category', 'is_featured', 'is_active')
    readonly_fields = ('slug',)

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    """Admin configuration for Region model."""
    list_display = ('name', 'country', 'is_active', 'is_featured', 'created_at')
    list_filter = ('is_active', 'is_featured', 'country')
    search_fields = ('name', 'description', 'country')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'country')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    """Admin configuration for Destination model with approval workflow."""
    list_display = ('name', 'city', 'country', 'region', 'approval_status', 'is_active', 'is_featured', 'created_at')
    list_filter = ('approval_status', 'is_active', 'is_featured', 'region', 'country')
    search_fields = ('name', 'description', 'city', 'country')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'views', 'created_by')
    inlines = [DestinationImageInline, SeasonInline, AttractionInline]
    actions = ['approve_destinations', 'reject_destinations']
    fieldsets = (
        (None, {
            'fields': ('region', 'name', 'slug', 'created_by')
        }),
        ('Location', {
            'fields': ('city', 'country', 'latitude', 'longitude')
        }),
        ('Details', {
            'fields': ('short_description', 'description', 'price', 'rating')
        }),
        ('Approval', {
            'fields': ('approval_status', 'rejection_reason')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Statistics', {
            'fields': ('views',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize database queries for the admin list view."""
        return super().get_queryset(request).select_related('region', 'created_by')
    
    def save_model(self, request, obj, form, change):
        """Set the created_by user when a new destination is created."""
        if not obj.pk:  # Only set created_by if this is a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    @admin.action(description='Approve selected destinations')
    def approve_destinations(self, request, queryset):
        """Approve the selected destinations."""
        updated = queryset.update(approval_status='APPROVED')
        self.message_user(request, f"Successfully approved {updated} {'destination' if updated == 1 else 'destinations'}.")
    
    @admin.action(description='Reject selected destinations')
    def reject_destinations(self, request, queryset):
        """Reject the selected destinations."""
        updated = queryset.update(approval_status='REJECTED')
        self.message_user(request, f"Marked {updated} {'destination' if updated == 1 else 'destinations'} as rejected.")

@admin.register(Attraction)
class AttractionAdmin(admin.ModelAdmin):
    """Admin configuration for Attraction model."""
    list_display = ('name', 'destination', 'category', 'is_featured', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_featured', 'category', 'destination__region')
    search_fields = ('name', 'description', 'address', 'city', 'country')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('destination', 'name', 'slug', 'category')
        }),
        ('Location', {
            'fields': ('address', 'city', 'country', 'latitude', 'longitude')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(DestinationImage)
class DestinationImageAdmin(admin.ModelAdmin):
    """Admin configuration for DestinationImage model."""
    list_display = ('destination', 'is_primary', 'created_at')
    list_filter = ('is_primary',)
    search_fields = ('destination__name', 'caption')
    readonly_fields = ('preview_image', 'created_at')
    list_select_related = ('destination',)
    
    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 200px;" />', obj.image.url)
        return "No image"
    preview_image.short_description = 'Preview'

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    """Admin configuration for Season model."""
    list_display = ('name', 'destination_name', 'start_month', 'end_month', 'is_active', 'created_at')
    list_filter = ('is_active', 'start_month', 'end_month', 'destination')
    search_fields = ('name', 'description', 'destination__name')
    list_select_related = ('destination',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'destination', 'description')
        }),
        ('Season Details', {
            'fields': ('start_month', 'end_month', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def destination_name(self, obj):
        return obj.destination.name if obj.destination else 'N/A'
    destination_name.short_description = 'Destination'

# Models are registered using @admin.register() decorators above
