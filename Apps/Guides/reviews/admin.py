"""
Django Admin configuration for the reviews app.

This module registers the review-related models with the Django admin interface,
configuring their display, search, filtering, and action options.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Review, ReviewImage, ReviewComment, ReviewHelpful


class ReviewImageInline(admin.TabularInline):
    """
    Inline admin interface for ReviewImage model.
    
    Allows managing review images directly from the Review admin page.
    """
    model = ReviewImage
    extra = 1
    fields = ('image', 'caption', 'is_primary', 'created_at')
    readonly_fields = ('created_at',)
    classes = ('collapse',)
    verbose_name = _('Image')
    verbose_name_plural = _('Images')


class ReviewCommentInline(admin.TabularInline):
    """
    Inline admin interface for ReviewComment model.
    
    Displays comments related to a review directly on the Review admin page.
    """
    model = ReviewComment
    extra = 0
    fields = ('user', 'content', 'is_official_response', 'is_approved', 'created_at')
    readonly_fields = ('created_at',)
    classes = ('collapse',)
    verbose_name = _('Comment')
    verbose_name_plural = _('Comments')


class ReviewHelpfulInline(admin.TabularInline):
    """
    Inline admin interface for ReviewHelpful model.
    
    Shows helpful votes directly on the Review admin page.
    """
    model = ReviewHelpful
    extra = 0
    fields = ('user', 'vote_type', 'created_at')
    readonly_fields = ('created_at',)
    classes = ('collapse',)
    verbose_name = _('Helpful Vote')
    verbose_name_plural = _('Helpful Votes')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for managing Review model.
    
    Configures the display, search, filtering, and actions for reviews.
    """
    list_display = ('title', 'user', 'content_type', 'rating', 'status', 'created_at', 'helpful_count')
    list_filter = ('status', 'rating', 'created_at', 'content_type')
    search_fields = ('title', 'content', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'helpful_count_display')
    fieldsets = (
        (_('Review Information'), {
            'fields': ('user', 'content_type', 'object_id', 'title', 'content', 'rating')
        }),
        (_('Moderation'), {
            'fields': ('status', 'featured', 'helpful_count_display')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [ReviewImageInline, ReviewCommentInline, ReviewHelpfulInline]
    actions = ['approve_reviews', 'reject_reviews', 'feature_reviews']
    date_hierarchy = 'created_at'
    
    def helpful_count_display(self, obj):
        """Display the count of helpful votes in the admin."""
        return obj.helpful_count
    helpful_count_display.short_description = _('Helpful Votes')
    
    def approve_reviews(self, request, queryset):
        """Admin action to approve selected reviews."""
        updated = queryset.update(status='approved')
        self.message_user(request, f"{updated} reviews were approved.")
    approve_reviews.short_description = _("Approve selected reviews")
    
    def reject_reviews(self, request, queryset):
        """Admin action to reject selected reviews."""
        updated = queryset.update(status='rejected')
        self.message_user(request, f"{updated} reviews were rejected.")
    reject_reviews.short_description = _("Reject selected reviews")
    
    def feature_reviews(self, request, queryset):
        """Admin action to feature selected reviews."""
        updated = queryset.update(featured=True)
        self.message_user(request, f"{updated} reviews were featured.")
    feature_reviews.short_description = _("Feature selected reviews")


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    """
    Admin interface for managing ReviewImage model.
    
    Configures the display and filtering of review images.
    """
    list_display = ('thumbnail_preview', 'review', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('review__title', 'caption')
    readonly_fields = ('thumbnail_preview', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('review', 'image', 'thumbnail_preview', 'caption', 'is_primary')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def thumbnail_preview(self, obj):
        """Display a thumbnail preview of the image in the admin."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return ""
    thumbnail_preview.short_description = _('Preview')


@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    """
    Admin interface for managing ReviewComment model.
    
    Configures the display, search, and filtering of review comments.
    """
    list_display = ('truncated_content', 'review', 'user', 'is_official_response', 'is_approved', 'created_at')
    list_filter = ('is_official_response', 'is_approved', 'created_at')
    search_fields = ('content', 'review__title', 'user__username')
    list_editable = ('is_approved', 'is_official_response')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_comments', 'unapprove_comments', 'mark_as_official']
    
    def truncated_content(self, obj):
        """Display a truncated version of the comment content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    truncated_content.short_description = _('Content')
    
    def approve_comments(self, request, queryset):
        """Admin action to approve selected comments."""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} comments were approved.")
    approve_comments.short_description = _("Approve selected comments")
    
    def unapprove_comments(self, request, queryset):
        """Admin action to unapprove selected comments."""
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} comments were unapproved.")
    unapprove_comments.short_description = _("Unapprove selected comments")
    
    def mark_as_official(self, request, queryset):
        """Admin action to mark selected comments as official responses."""
        updated = queryset.update(is_official_response=True)
        self.message_user(request, f"{updated} comments were marked as official responses.")
    mark_as_official.short_description = _("Mark as official response")


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    """
    Admin interface for managing ReviewHelpful model.
    
    Configures the display and filtering of helpful votes.
    """
    list_display = ('review', 'user', 'vote_type', 'created_at')
    list_filter = ('vote_type', 'created_at')
    search_fields = ('review__title', 'user__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
