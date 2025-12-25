"""
Customer app admin configuration.
Contains admin interface for UserProfile, RestaurantReview, MenuItemReview, and related models.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserProfile, RestaurantReview, MenuItemReview, ReviewResponse, ReviewFlag, Wishlist, LoyaltyTransaction
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile model.
    
    Provides comprehensive management of user profiles including:
    - Personal information (full name, phone number)
    - User role management with visual indicators
    - Address details for delivery
    - Profile settings and preferences
    - Search and filtering capabilities
    """
    
    list_display = [
        'user', 'full_name', 'role_display', 'phone_number', 'city', 
        'has_delivery_address', 'points_balance', 'created_at'
    ]
    
    list_filter = [
        'role', 'city', 'created_at', 'updated_at'
    ]
    
    search_fields = [
        'user__username', 'user__email', 'full_name', 
        'phone_number', 'address', 'city'
    ]
    
    readonly_fields = [
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name', 'role', 'phone_number'),
            'description': 'Basic user profile information and role assignment'
        }),
        ('Address Information', {
            'fields': ('address', 'city', 'postal_code'),
            'description': 'Delivery address details',
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('dietary_preferences', 'profile_picture'),
            'description': 'User preferences and profile image',
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'description': 'Automatic timestamps',
            'classes': ('collapse',)
        }),
    )
    
    def has_delivery_address(self, obj):
        """
        Display whether user has complete delivery address.
        
        Args:
            obj (UserProfile): UserProfile instance
            
        Returns:
            str: Checkmark or cross icon
        """
        if obj.has_delivery_address():
            return '✅ Yes'
        return '❌ No'
    has_delivery_address.short_description = 'Delivery Address'
    has_delivery_address.admin_order_field = 'city'
    
    def role_display(self, obj):
        """
        Display user role with color-coded badge for easy identification.
        
        Args:
            obj (UserProfile): UserProfile instance
            
        Returns:
            str: HTML formatted role badge with appropriate color
        """
        role_colors = {
            'customer': '#10b981',      # Green
            'restaurant_owner': '#f59e0b',  # Orange/Amber
            'manager': '#8b5cf6',       # Purple
            'admin': '#ef4444',         # Red
        }
        
        role_icons = {
            'customer': '👤',
            'restaurant_owner': '🍽️',
            'manager': '👔',
            'admin': '👑',
        }
        
        color = role_colors.get(obj.role, '#6b7280')
        icon = role_icons.get(obj.role, '👤')
        role_display = obj.get_role_display() if hasattr(obj, 'get_role_display') else obj.role.title()
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">{} {}</span>',
            color, icon, role_display
        )
    role_display.short_description = 'Role'
    role_display.admin_order_field = 'role'
    
    def get_queryset(self, request):
        """
        Optimize queries with select_related for better performance.
        
        Args:
            request: HttpRequest object
            
        Returns:
            QuerySet: Optimized queryset with user data preloaded
        """
        return super().get_queryset(request).select_related('user')


@admin.register(RestaurantReview)
class RestaurantReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for RestaurantReview model.
    
    Provides comprehensive management of customer reviews including:
    - Review moderation with flagging and hiding capabilities
    - Rating analysis across multiple categories
    - Verified purchase indicators
    - Search and filtering capabilities
    """
    
    list_display = [
        'user', 'restaurant', 'rating_display', 'is_verified_purchase',
        'is_flagged', 'is_hidden', 'created_at'
    ]
    
    list_filter = [
        'is_flagged', 'is_hidden', 'is_verified_purchase', 'rating',
        'created_at', 'food_quality', 'service_quality', 'delivery_speed', 'value_for_money'
    ]
    
    search_fields = [
        'user__username', 'user__email', 'restaurant__name',
        'title', 'comment'
    ]
    
    readonly_fields = [
        'created_at', 'updated_at', 'is_verified_purchase', 'get_average_rating'
    ]
    
    list_editable = ['is_flagged', 'is_hidden']
    
    fieldsets = (
        ('Review Information', {
            'fields': ('user', 'restaurant', 'order', 'is_verified_purchase'),
            'description': 'Basic review information and associations'
        }),
        ('Ratings', {
            'fields': ('rating', 'food_quality', 'service_quality', 'delivery_speed', 'value_for_money'),
            'description': 'Customer ratings across different categories'
        }),
        ('Review Content', {
            'fields': ('title', 'comment'),
            'description': 'Review text content'
        }),
        ('Moderation', {
            'fields': ('is_flagged', 'is_hidden', 'flag_reason'),
            'description': 'Review moderation status'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'get_average_rating'),
            'description': 'Automatic timestamps and calculated fields',
            'classes': ('collapse',)
        }),
    )
    
    def rating_display(self, obj):
        """
        Display rating with stars visualization.
        
        Args:
            obj (RestaurantReview): RestaurantReview instance
            
        Returns:
            str: HTML formatted rating with stars
        """
        stars = '⭐' * obj.rating
        return format_html(
            '<span style="color: #f59e0b; font-size: 14px;">{}</span> <span style="color: #6b7280;">({}/5)</span>',
            stars, obj.rating
        )
    rating_display.short_description = 'Rating'
    rating_display.admin_order_field = 'rating'
    
    def get_average_rating(self, obj):
        """
        Display average rating across all categories.
        
        Args:
            obj (RestaurantReview): RestaurantReview instance
            
        Returns:
            str: Average rating formatted
        """
        ratings = [obj.rating]
        if obj.food_quality:
            ratings.append(obj.food_quality)
        if obj.service_quality:
            ratings.append(obj.service_quality)
        if obj.delivery_speed:
            ratings.append(obj.delivery_speed)
        if obj.value_for_money:
            ratings.append(obj.value_for_money)
        
        avg = sum(ratings) / len(ratings) if ratings else 0
        return f'{avg:.2f} / 5.00'
    get_average_rating.short_description = 'Average Rating'
    
    def get_queryset(self, request):
        """
        Optimize queries with select_related for better performance.
        
        Args:
            request: HttpRequest object
            
        Returns:
            QuerySet: Optimized queryset with related data preloaded
        """
        return super().get_queryset(request).select_related('user', 'restaurant', 'order')


@admin.register(MenuItemReview)
class MenuItemReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for MenuItemReview model.
    
    Provides management of menu item reviews including:
    - Review moderation with flagging capabilities
    - Detailed rating analysis (taste, presentation, portion size)
    - Search and filtering capabilities
    """
    
    list_display = [
        'user', 'menu_item', 'rating_display', 'is_flagged', 'is_hidden', 'created_at'
    ]
    
    list_filter = [
        'is_flagged', 'is_hidden', 'rating',
        'created_at', 'taste', 'presentation', 'portion_size'
    ]
    
    search_fields = [
        'user__username', 'user__email', 'menu_item__name',
        'menu_item__restaurant__name', 'comment'
    ]
    
    readonly_fields = [
        'created_at', 'updated_at'
    ]
    
    list_editable = ['is_flagged', 'is_hidden']
    
    fieldsets = (
        ('Review Information', {
            'fields': ('user', 'menu_item', 'order'),
            'description': 'Basic review information and associations'
        }),
        ('Ratings', {
            'fields': ('rating', 'taste', 'presentation', 'portion_size'),
            'description': 'Customer ratings across different categories'
        }),
        ('Review Content', {
            'fields': ('comment',),
            'description': 'Review text content'
        }),
        ('Moderation', {
            'fields': ('is_flagged', 'is_hidden', 'flag_reason'),
            'description': 'Review moderation status'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'description': 'Automatic timestamps',
            'classes': ('collapse',)
        }),
    )
    
    def rating_display(self, obj):
        """
        Display rating with stars visualization.
        
        Args:
            obj (MenuItemReview): MenuItemReview instance
            
        Returns:
            str: HTML formatted rating with stars
        """
        stars = '⭐' * obj.rating
        return format_html(
            '<span style="color: #f59e0b; font-size: 14px;">{}</span> <span style="color: #6b7280;">({}/5)</span>',
            stars, obj.rating
        )
    rating_display.short_description = 'Rating'
    rating_display.admin_order_field = 'rating'
    
    def get_queryset(self, request):
        """
        Optimize queries with select_related for better performance.
        
        Args:
            request: HttpRequest object
            
        Returns:
            QuerySet: Optimized queryset with related data preloaded
        """
        return super().get_queryset(request).select_related(
            'user', 'menu_item', 'order', 'menu_item__restaurant'
        )


@admin.register(ReviewResponse)
class ReviewResponseAdmin(admin.ModelAdmin):
    """
    Admin interface for ReviewResponse model.
    
    Provides management of restaurant owner responses including:
    - Response approval and visibility control
    - Response content management
    - Search and filtering capabilities
    """
    
    list_display = [
        'responder', 'review_type', 'is_public', 'created_at'
    ]
    
    list_filter = [
        'is_public', 'created_at'
    ]
    
    search_fields = [
        'responder__username', 'responder__email', 'response'
    ]
    
    readonly_fields = [
        'created_at', 'updated_at'
    ]
    
    list_editable = ['is_public']
    
    fieldsets = (
        ('Response Information', {
            'fields': ('responder', 'restaurant_review', 'menu_item_review'),
            'description': 'Response details and associated review'
        }),
        ('Response Content', {
            'fields': ('response', 'is_public'),
            'description': 'Response text and visibility settings'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'description': 'Automatic timestamps',
            'classes': ('collapse',)
        }),
    )
    
    def review_type(self, obj):
        """
        Display the type of review being responded to.
        
        Args:
            obj (ReviewResponse): ReviewResponse instance
            
        Returns:
            str: Type of review with link
        """
        if obj.restaurant_review:
            return format_html(
                '<a href="/admin/customer/restaurantreview/{}/change/">Restaurant Review</a>',
                obj.restaurant_review.id
            )
        elif obj.menu_item_review:
            return format_html(
                '<a href="/admin/customer/menuitemreview/{}/change/">Menu Item Review</a>',
                obj.menu_item_review.id
            )
        return 'Unknown'
    review_type.short_description = 'Review Type'
    
    def get_queryset(self, request):
        """
        Optimize queries with select_related for better performance.
        
        Args:
            request: HttpRequest object
            
        Returns:
            QuerySet: Optimized queryset with related data preloaded
        """
        return super().get_queryset(request).select_related(
            'responder', 'restaurant_review', 'menu_item_review'
        )


@admin.register(ReviewFlag)
class ReviewFlagAdmin(admin.ModelAdmin):
    """
    Admin interface for ReviewFlag model.
    
    Provides management of review flags including:
    - Flag resolution and tracking
    - Admin notes and moderation actions
    - Search and filtering capabilities
    """
    
    list_display = [
        'flagged_by', 'review_type', 'reason', 'is_resolved', 'created_at'
    ]
    
    list_filter = [
        'reason', 'is_resolved', 'created_at'
    ]
    
    search_fields = [
        'flagged_by__username', 'flagged_by__email', 
        'description', 'admin_notes'
    ]
    
    readonly_fields = [
        'created_at', 'resolved_at'
    ]
    
    list_editable = ['is_resolved']
    
    fieldsets = (
        ('Flag Information', {
            'fields': ('flagged_by', 'restaurant_review', 'menu_item_review', 'reason'),
            'description': 'Flag details and associated review'
        }),
        ('Flag Details', {
            'fields': ('description',),
            'description': 'Additional information about the flag'
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'admin_notes', 'resolved_at'),
            'description': 'Flag resolution and admin notes'
        }),
        ('System Information', {
            'fields': ('created_at',),
            'description': 'Automatic timestamps',
            'classes': ('collapse',)
        }),
    )
    
    def review_type(self, obj):
        """
        Display the type of review being flagged.
        
        Args:
            obj (ReviewFlag): ReviewFlag instance
            
        Returns:
            str: Type of review with link
        """
        if obj.restaurant_review:
            return format_html(
                '<a href="/admin/customer/restaurantreview/{}/change/">Restaurant Review</a>',
                obj.restaurant_review.id
            )
        elif obj.menu_item_review:
            return format_html(
                '<a href="/admin/customer/menuitemreview/{}/change/">Menu Item Review</a>',
                obj.menu_item_review.id
            )
        return 'Unknown'
    review_type.short_description = 'Review Type'
    
    def save_model(self, request, obj, form, change):
        """
        Auto-set resolved_at when flag is marked as resolved.
        
        Args:
            request: HttpRequest object
            obj: ReviewFlag instance
            form: ModelForm instance
            change: Boolean indicating if this is an edit
        """
        if obj.is_resolved and not obj.resolved_at:
            from django.utils import timezone
            obj.resolved_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """
        Optimize queries with select_related for better performance.
        
        Args:
            request: HttpRequest object
            
        Returns:
            QuerySet: Optimized queryset with related data preloaded
        """
        return super().get_queryset(request).select_related(
            'flagged_by', 'restaurant_review', 'menu_item_review'
        )


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """
    Admin interface for Wishlist model.
    
    Provides management of customer wishlists including:
    - Wishlist monitoring
    - Popular restaurants tracking
    - Customer engagement analysis
    """
    
    list_display = [
        'user', 'restaurant', 'created_at'
    ]
    
    list_filter = [
        'created_at', 'restaurant'
    ]
    
    search_fields = [
        'user__username', 'user__email', 'restaurant__name'
    ]
    
    readonly_fields = [
        'created_at'
    ]
    
    fieldsets = (
        ('Wishlist Information', {
            'fields': ('user', 'restaurant'),
            'description': 'Customer and restaurant association'
        }),
        ('System Information', {
            'fields': ('created_at',),
            'description': 'Automatic timestamp',
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """
        Optimize queries with select_related for better performance.
        
        Args:
            request: HttpRequest object
            
        Returns:
            QuerySet: Optimized queryset with related data preloaded
        """
        return super().get_queryset(request).select_related('user', 'restaurant')
    
    def has_add_permission(self, request):
        """
        Disable manual creation of wishlist items through admin.
        
        Args:
            request: HttpRequest object
            
        Returns:
            bool: False to prevent manual creation
        """
        return False


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    """
    Admin interface for LoyaltyTransaction model.
    
    Provides comprehensive management of loyalty point transactions including:
    - Complete audit trail of all point movements
    - Transaction type filtering and search capabilities
    - User-specific transaction history
    - Expiration tracking and management
    - Manual point adjustments with proper validation
    - Read-only audit mode for earned/redeemed transactions
    """
    
    list_display = [
        'user', 'transaction_type_display', 'points_display', 'balance_after', 
        'order_link', 'description_short', 'expiration_status', 'created_at'
    ]
    
    list_filter = [
        'transaction_type', 'created_at', 'expires_at'
    ]
    
    search_fields = [
        'user__username', 'user__email', 'description', 'order__order_id'
    ]
    
    readonly_fields = [
        'created_at', 'balance_after'
    ]
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('user', 'transaction_type', 'points', 'balance_after'),
            'description': 'Core transaction details and point amounts'
        }),
        ('Related Order', {
            'fields': ('order',),
            'description': 'Associated order (if applicable)'
        }),
        ('Details', {
            'fields': ('description', 'expires_at'),
            'description': 'Transaction description and expiration information'
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'description': 'Automatic timestamp',
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """
        Make certain fields readonly for existing transactions to maintain audit integrity.
        
        Args:
            request: HttpRequest object
            obj: Transaction object being edited
            
        Returns:
            list: Fields that should be readonly
        """
        if obj:  # Editing existing transaction
            readonly = list(self.readonly_fields)
            # Prevent editing of earned/redeemed transactions (audit integrity)
            if obj.transaction_type in ['earned', 'redeemed']:
                readonly.extend(['user', 'transaction_type', 'points', 'order', 'expires_at'])
            return readonly
        return self.readonly_fields
    
    def transaction_type_display(self, obj):
        """
        Display transaction type with color coding.
        
        Args:
            obj: LoyaltyTransaction instance
            
        Returns:
            str: HTML with colored transaction type
        """
        colors = {
            'earned': 'green',
            'redeemed': 'red', 
            'expired': 'orange',
            'manual': 'blue',
            'refunded': 'purple'
        }
        color = colors.get(obj.transaction_type, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_transaction_type_display()
        )
    transaction_type_display.short_description = 'Type'
    
    def points_display(self, obj):
        """
        Display points with appropriate sign and color.
        
        Args:
            obj: LoyaltyTransaction instance
            
        Returns:
            str: HTML with colored points amount
        """
        if obj.points > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">+{}</span>', obj.points
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>', obj.points
            )
    points_display.short_description = 'Points'
    
    def order_link(self, obj):
        """
        Display order as clickable link if available.
        
        Args:
            obj: LoyaltyTransaction instance
            
        Returns:
            str: HTML link to order or empty string
        """
        if obj.order:
            return format_html(
                '<a href="/admin/orders/order/{}/change/">#{}</a>',
                obj.order.id, obj.order.order_id
            )
        return '-'
    order_link.short_description = 'Order'
    
    def description_short(self, obj):
        """
        Display truncated description.
        
        Args:
            obj: LoyaltyTransaction instance
            
        Returns:
            str: Truncated description
        """
        if len(obj.description) > 50:
            return obj.description[:50] + '...'
        return obj.description
    description_short.short_description = 'Description'
    
    def expiration_status(self, obj):
        """
        Display expiration status with color coding.
        
        Args:
            obj: LoyaltyTransaction instance
            
        Returns:
            str: HTML with expiration status
        """
        if obj.transaction_type != 'earned':
            return '-'
        
        status = obj.get_status_display()
        if 'Expired' in status:
            color = 'red'
        elif 'Expires' in status:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    expiration_status.short_description = 'Status'
    
    def get_queryset(self, request):
        """
        Optimize queries with select_related for better performance.
        
        Args:
            request: HttpRequest object
            
        Returns:
            QuerySet: Optimized queryset with related data preloaded
        """
        return super().get_queryset(request).select_related('user', 'order')
    
    def has_delete_permission(self, request, obj=None):
        """
        Restrict deletion of loyalty transactions to maintain audit trail.
        
        Args:
            request: HttpRequest object
            obj: Transaction object being deleted
            
        Returns:
            bool: False to prevent deletion
        """
        return False
