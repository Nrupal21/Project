"""
Admin configuration for the rewards app.

This module registers the reward-related models with the Django admin site and
customizes their display and editing interfaces to make reward management easier.

The admin interfaces defined here provide administrators with powerful tools to:
1. Manage reward tiers and their associated benefits
2. Track and modify user point balances
3. Process and monitor point redemption requests
4. View analytics on point distribution and usage

Each model admin class includes custom actions, filters, and display methods
to streamline common administrative tasks and provide insights into the
rewards system's operation. The interfaces follow Django admin best practices
for usability and performance optimization.

The color scheme for visual elements follows the TravelGuide platform's
indigo/violet palette for consistency with the frontend user interface.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import RewardTier, RewardPoints, RewardRedemption


@admin.register(RewardTier)
class RewardTierAdmin(admin.ModelAdmin):
    """
    Admin interface for reward tiers.
    
    Provides a clean interface for creating and managing reward tiers with
    appropriate filters and search capabilities.
    
    Reward tiers are a fundamental component of the loyalty program, representing
    different membership levels (e.g., Bronze, Silver, Gold, Platinum) with
    increasing benefits as users accumulate more points. This admin interface
    allows administrators to define the point thresholds, multipliers, and
    visual styling for each tier.
    
    The interface is designed to make it easy to visualize the tier hierarchy
    and ensure there are no gaps or overlaps in the point ranges between tiers.
    """
    # Fields to display in the list view, providing a comprehensive overview of each tier
    list_display = ('name', 'min_points', 'max_points', 'multiplier', 'display_color', 'created_at')
    
    # Filter options in the right sidebar
    list_filter = ('created_at',)
    
    # Fields that can be searched
    search_fields = ('name',)
    
    # Fields that cannot be modified after creation
    readonly_fields = ('created_at', 'updated_at')
    
    def display_color(self, obj):
        """
        Display the tier color as a colored square in the admin list.
        
        This method renders a visual representation of the tier's color as a small
        colored square in the admin list view. This makes it easy for administrators
        to quickly identify tiers and ensure the color scheme follows a logical
        progression (e.g., bronze to gold).
        
        The method handles both hex color codes (e.g., '#6366f1') and Tailwind CSS
        class names (e.g., 'indigo-500'), defaulting to the platform's standard
        indigo color if a Tailwind class is used.
        
        Args:
            obj: The RewardTier instance being displayed
            
        Returns:
            str: HTML with colored square representing the tier color
        """
        # Get the color value from the tier object
        color = obj.color
        
        # Handle Tailwind class names which aren't valid CSS colors
        if not color.startswith('#'):
            # For Tailwind class names like 'indigo-500' or 'violet-600',
            # we use a default indigo color that matches our platform's color scheme
            # This ensures consistent display in the admin interface
            color = '#6366f1'  # Default indigo-500 color if using Tailwind class
            
        # Use Django's format_html to safely render HTML in the admin
        # Creates a small colored square with rounded corners
        return format_html(
            '<div style="background-color: {}; width: 20px; height: 20px; border-radius: 4px;"></div>',
            color
        )
    # Set a user-friendly column header for this method in the admin list view
    display_color.short_description = 'Color'


@admin.register(RewardPoints)
class RewardPointsAdmin(admin.ModelAdmin):
    """
    Admin interface for reward points entries.
    
    Provides comprehensive filtering and search capabilities for managing
    user reward points, with custom methods to show point balances.
    
    This admin interface is crucial for monitoring and managing the flow of points
    throughout the rewards system. It allows administrators to:
    - Track point earning activities across different categories
    - Monitor point expiration and validity
    - Audit point transactions for specific users
    - Analyze point distribution patterns over time
    
    The interface is optimized for performance with related object prefetching
    to handle potentially large numbers of point transactions efficiently.
    
    The indigo/violet color scheme is maintained in any visual elements to ensure
    consistency with the TravelGuide platform's design language.
    """
    # Fields to display in the list view, providing a comprehensive overview of each point transaction
    list_display = ('user', 'activity', 'points', 'description', 'created_at', 'expiration_date', 'is_expired')
    
    # Filter options in the right sidebar for quick data segmentation
    # Activity type and expiration status are key filters for point management
    list_filter = ('activity', 'is_expired', 'created_at')
    
    # Fields that can be searched to quickly find specific transactions
    # Includes related user fields for convenience
    search_fields = ('user__username', 'user__email', 'description')
    
    # Fields that cannot be modified after creation to maintain audit integrity
    readonly_fields = ('created_at',)
    
    # Date-based navigation hierarchy for easier browsing of historical data
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        """
        Optimize the queryset by prefetching related user objects.
        
        This method overrides the default queryset to improve performance by using
        select_related to fetch user data in the same database query as the reward points.
        This optimization is particularly important for the rewards system, which may
        contain thousands or millions of point transactions across many users.
        
        Without this optimization, the admin list view would make a separate database
        query for each user associated with each displayed reward point entry, potentially
        causing significant performance issues with large datasets.
        
        Args:
            request: The HTTP request object from the admin site
            
        Returns:
            QuerySet: Optimized queryset with prefetched related user objects
        """
        # Get the base queryset from the parent class
        qs = super().get_queryset(request)
        
        # Optimize by fetching related user objects in the same query
        # This reduces database queries from O(n) to O(1) for user data
        return qs.select_related('user')
    
    def user_point_balance(self, obj):
        """
        Calculate and display the current point balance for the user.
        
        This method provides a convenient way to see a user's current valid point balance
        directly in the admin interface, without having to navigate to a separate view.
        It uses the RewardPoints model's get_user_point_balance method, which handles
        all the logic for calculating valid (non-expired, non-redeemed) points.
        
        This is particularly useful when reviewing individual point transactions
        and understanding their impact on the user's overall balance.
        
        Args:
            obj: The RewardPoints instance being displayed
            
        Returns:
            int: Total valid (non-expired, non-redeemed) points for the user
        """
        # Call the model's method to get the current point balance
        # This ensures consistent balance calculation throughout the application
        return RewardPoints.get_user_point_balance(obj.user)
    
    # Set a user-friendly column header for this method in the admin list view
    user_point_balance.short_description = 'Current Balance'


@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    """
    Admin interface for reward redemptions.
    
    Provides tools for managing and processing user point redemptions with
    status tracking and filtering capabilities.
    
    This admin interface is critical for the operational aspects of the rewards system,
    allowing administrators to process and manage redemption requests from users.
    It supports the complete redemption lifecycle:
    
    1. Reviewing pending redemption requests
    2. Marking requests as in-processing
    3. Completing fulfilled redemptions
    4. Cancelling and refunding points when necessary
    
    The interface includes bulk actions to efficiently process multiple redemptions
    at once, which is particularly useful during high-volume periods or promotions.
    
    Performance optimization is implemented through database query reduction,
    which is essential for systems with many redemption transactions.
    
    The visual styling maintains the indigo/violet color scheme of the TravelGuide
    platform for consistency with the frontend user experience.
    """
    # Fields to display in the list view, showing the complete redemption information
    list_display = ('user', 'points_used', 'redemption_type', 'redemption_value', 'status', 'created_at', 'processed_at')
    
    # Filter options in the right sidebar for quick data segmentation
    # Status is the most important filter for workflow management
    list_filter = ('status', 'redemption_type', 'created_at')
    
    # Fields that can be searched to quickly find specific redemptions
    search_fields = ('user__username', 'user__email', 'code')
    
    # Fields that cannot be modified after creation to maintain audit integrity
    readonly_fields = ('created_at', 'id')
    
    # Bulk actions available for efficient redemption processing
    actions = ['mark_as_completed', 'mark_as_processing', 'cancel_redemptions']
    
    # Date-based navigation hierarchy for easier browsing of historical data
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        """
        Optimize the queryset by prefetching related user objects.
        
        This method overrides the default queryset to improve performance by using
        select_related to fetch user data in the same database query as the redemption records.
        This optimization is particularly important for the redemption admin interface,
        which may need to display many redemption records with associated user information.
        
        Without this optimization, the admin list view would make a separate database
        query for each user associated with each displayed redemption, potentially
        causing significant performance issues with large datasets.
        
        Args:
            request: The HTTP request object from the admin site
            
        Returns:
            QuerySet: Optimized queryset with prefetched related user objects
        """
        # Get the base queryset from the parent class
        qs = super().get_queryset(request)
        
        # Optimize by fetching related user objects in the same query
        # This reduces database queries from O(n) to O(1) for user data
        return qs.select_related('user')
    
    def mark_as_completed(self, request, queryset):
        """
        Mark selected redemptions as completed.
        
        This admin action allows administrators to mark multiple redemption requests
        as completed after they have been fulfilled. This is typically done after
        the actual reward (discount code, travel credit, etc.) has been provided
        to the user through the appropriate channel.
        
        The method uses the redemption model's mark_as_processed method, which:
        1. Updates the status to COMPLETED
        2. Sets the processed_at timestamp
        3. Records the processing notes
        4. Handles any additional business logic required on completion
        
        Only redemptions that can be successfully processed will be counted in the
        success message. This prevents issues where some redemptions might be in
        an invalid state for completion.
        
        Args:
            request: The HTTP request from the admin site
            queryset: QuerySet of selected RewardRedemption objects to mark as completed
        """
        # Counter for successfully updated redemptions
        updated = 0
        
        # Process each selected redemption individually
        # This allows for proper handling of any validation or business rules
        for redemption in queryset:
            # The mark_as_processed method returns True if successful, False otherwise
            # It handles all the necessary status updates and validation
            if redemption.mark_as_processed('Processed by admin'):
                updated += 1
        
        # Display a success message to the admin user with the count of updated items
        # This provides immediate feedback on the action's results
        self.message_user(
            request,
            f"{updated} redemption(s) marked as completed."
        )
    
    # Set a user-friendly description for this action in the admin dropdown
    mark_as_completed.short_description = "Mark selected redemptions as completed"
    
    def mark_as_processing(self, request, queryset):
        """
        Mark selected redemptions as processing.
        
        This admin action allows administrators to mark multiple redemption requests
        as being processed. This intermediate status is useful for indicating that
        the redemption request has been acknowledged and is being worked on, but
        has not yet been completed.
        
        The processing status is particularly useful for:
        1. Indicating to users that their request is being handled
        2. Tracking workflow progress in the admin interface
        3. Filtering redemptions that need attention vs. those already in progress
        
        Unlike the mark_as_completed action, this method only updates redemptions
        that are currently in the PENDING status to avoid changing redemptions that
        are already completed or cancelled. This prevents accidental status changes
        to redemptions that should not be modified.
        
        Args:
            request: The HTTP request from the admin site
            queryset: QuerySet of selected RewardRedemption objects to mark as processing
        """
        # Update only redemptions that are currently in PENDING status
        # This is a bulk update operation for efficiency, rather than processing
        # each redemption individually as in mark_as_completed
        count = queryset.filter(status=RewardRedemption.Status.PENDING).update(
            status=RewardRedemption.Status.PROCESSING
        )
        
        # Display a success message to the admin user with the count of updated items
        # This provides immediate feedback on the action's results
        self.message_user(
            request, 
            f"{count} redemption(s) marked as processing."
        )
    
    # Set a user-friendly description for this action in the admin dropdown
    mark_as_processing.short_description = "Mark selected redemptions as processing"
    
    def cancel_redemptions(self, request, queryset):
        """
        Cancel selected redemptions and refund points.
        
        This admin action allows administrators to cancel redemption requests and
        automatically refund the points back to the user's balance. This is useful in
        several scenarios:
        
        1. When a redemption cannot be fulfilled (e.g., out of stock items)
        2. When a user requests cancellation of their redemption
        3. When a redemption was created in error or is deemed invalid
        4. When processing takes too long and the admin wants to reset the request
        
        The method uses the redemption model's cancel_redemption method, which:
        1. Updates the status to CANCELLED
        2. Creates a new RewardPoints entry to refund the points
        3. Records the cancellation reason
        4. Handles any additional business logic required on cancellation
        
        This action requires individual processing of each redemption to ensure
        proper point refunding and transaction recording. Only redemptions that
        can be successfully cancelled will be counted in the success message.
        
        Args:
            request: The HTTP request from the admin site
            queryset: QuerySet of selected RewardRedemption objects to cancel
        """
        # Counter for successfully cancelled redemptions
        cancelled = 0
        
        # Process each selected redemption individually
        # This is necessary because point refunding requires specific logic
        # that must be applied to each redemption separately
        for redemption in queryset:
            # The cancel_redemption method returns True if successful, False otherwise
            # It handles all the necessary status updates, point refunds, and validation
            if redemption.cancel_redemption('Cancelled by admin'):
                cancelled += 1
        
        # Display a success message to the admin user with the count of cancelled items
        # This provides immediate feedback on the action's results
        self.message_user(
            request,
            f"{cancelled} redemption(s) cancelled and points refunded."
        )
    
    # Set a user-friendly description for this action in the admin dropdown
    # The description clearly indicates that points will be refunded as part of this action
    cancel_redemptions.short_description = "Cancel redemptions and refund points"
