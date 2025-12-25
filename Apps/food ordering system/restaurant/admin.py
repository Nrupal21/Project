"""
Restaurant app admin configuration.
Registers Restaurant and PendingRestaurant models with custom admin interface.
"""
from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from .models import Restaurant, PendingRestaurant, ManagerLoginLog, RestaurantTable


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    """
    Admin interface for Restaurant model.
    
    Provides comprehensive management of restaurants including:
    - List display with key information
    - Search functionality
    - Filtering options
    - Field organization in forms
    """
    # List display configuration
    list_display = (
        'name', 
        'owner',
        'rating', 
        'approval_status_badge',
        'is_active', 
        'phone', 
        'minimum_order', 
        'delivery_fee',
        'opening_time',
        'closing_time'
    )
    
    # List filters
    list_filter = ('is_active', 'is_approved', 'approval_status', 'rating', 'created_at')
    
    # Search fields
    search_fields = ('name', 'description', 'address', 'phone', 'email', 'owner__username')
    
    # Ordering
    ordering = ('-created_at', '-rating', 'name')
    
    # Fields grouping in form
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'owner', 'image', 'is_approved', 'approval_status')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'address')
        }),
        ('Business Hours', {
            'fields': ('opening_time', 'closing_time', 'is_active')
        }),
        ('Pricing', {
            'fields': ('minimum_order', 'delivery_fee', 'rating')
        }),
        ('Approval Information', {
            'fields': ('rejection_reason',),
            'classes': ('collapse',)
        }),
    )
    
    # Number of items per page
    list_per_page = 20
    
    def approval_status_badge(self, obj):
        """
        Display approval status as a colored badge.
        
        Args:
            obj: Restaurant instance
            
        Returns:
            str: HTML badge with appropriate color
        """
        if obj.approval_status == 'approved':
            return format_html(
                '<span style="background-color: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">✓ Approved</span>'
            )
        elif obj.approval_status == 'pending':
            return format_html(
                '<span style="background-color: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">⏳ Pending</span>'
            )
        elif obj.approval_status == 'rejected':
            return format_html(
                '<span style="background-color: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">✗ Rejected</span>'
            )
        return '-'
    approval_status_badge.short_description = 'Status'
    approval_status_badge.admin_order_field = 'approval_status'


@admin.register(PendingRestaurant)
class PendingRestaurantAdmin(admin.ModelAdmin):
    """
    Admin interface for PendingRestaurant model.
    
    Provides management of restaurant applications including:
    - Approval and rejection actions
    - Application status tracking
    - Detailed application information
    """
    # List display configuration
    list_display = (
        'restaurant_name',
        'user',
        'status_badge',
        'phone',
        'cuisine_type_display',
        'created_at',
        'processed_at'
    )
    
    # List filters
    list_filter = ('status', 'cuisine_type', 'created_at', 'processed_at')
    
    # Search fields
    search_fields = (
        'restaurant_name', 
        'description', 
        'address', 
        'phone', 
        'email',
        'user__username',
        'user__email'
    )
    
    # Ordering
    ordering = ('-created_at',)
    
    # Fields grouping in form
    fieldsets = (
        ('Application Information', {
            'fields': ('user', 'restaurant_name', 'description', 'status')
        }),
        ('Contact Details', {
            'fields': ('phone', 'email', 'address')
        }),
        ('Restaurant Details', {
            'fields': ('cuisine_type', 'image', 'opening_time', 'closing_time')
        }),
        ('Pricing', {
            'fields': ('minimum_order', 'delivery_fee')
        }),
        ('Processing Information', {
            'fields': ('processed_by', 'processed_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = ('user', 'restaurant_name', 'description', 'phone', 'email', 
                      'address', 'cuisine_type', 'image', 'opening_time', 'closing_time',
                      'minimum_order', 'delivery_fee', 'created_at', 'processed_at')
    
    # Number of items per page
    list_per_page = 20
    
    # Custom admin actions
    actions = ['approve_applications', 'reject_applications']
    
    def status_badge(self, obj):
        """
        Display application status as a colored badge.
        
        Args:
            obj: PendingRestaurant instance
            
        Returns:
            str: HTML badge with appropriate color
        """
        if obj.status == 'approved':
            return format_html(
                '<span style="background-color: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">✓ Approved</span>'
            )
        elif obj.status == 'pending':
            return format_html(
                '<span style="background-color: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">⏳ Pending</span>'
            )
        elif obj.status == 'rejected':
            return format_html(
                '<span style="background-color: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">✗ Rejected</span>'
            )
        return '-'
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def cuisine_type_display(self, obj):
        """
        Display cuisine type in a readable format.
        
        Args:
            obj: PendingRestaurant instance
            
        Returns:
            str: Formatted cuisine type name
        """
        return obj.get_cuisine_type_display()
    cuisine_type_display.short_description = 'Cuisine Type'
    cuisine_type_display.admin_order_field = 'cuisine_type'
    
    def approve_applications(self, request, queryset):
        """
        Admin action to approve selected applications.
        
        Args:
            request: Django HTTP request object
            queryset: Selected PendingRestaurant objects
        """
        count = 0
        for application in queryset.filter(status='pending'):
            try:
                application.approve_application(request.user)
                count += 1
            except Exception as e:
                messages.error(request, f'Error approving {application.restaurant_name}: {str(e)}')
        
        if count > 0:
            messages.success(
                request, 
                f'Successfully approved {count} restaurant application(s). '
                'The users have been assigned to the Restaurant Owner group.'
            )
    
    approve_applications.short_description = 'Approve selected applications'
    
    def reject_applications(self, request, queryset):
        """
        Admin action to reject selected applications.
        
        Args:
            request: Django HTTP request object
            queryset: Selected PendingRestaurant objects
        """
        # For bulk rejection, we'll use a generic reason
        # In a real implementation, you might want to collect individual reasons
        count = 0
        for application in queryset.filter(status='pending'):
            try:
                application.reject_application(
                    request.user, 
                    'Application rejected by administrator during bulk action.'
                )
                count += 1
            except Exception as e:
                messages.error(request, f'Error rejecting {application.restaurant_name}: {str(e)}')
        
        if count > 0:
            messages.success(
                request, 
                f'Successfully rejected {count} restaurant application(s).'
            )
    
    reject_applications.short_description = 'Reject selected applications'
    
    def get_queryset(self, request):
        """
        Optimize queryset with related objects.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            QuerySet: Optimized queryset with related objects
        """
        return super().get_queryset(request).select_related('user', 'processed_by')
    
    def has_add_permission(self, request):
        """
        Disable adding new pending restaurants through admin.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            bool: False to prevent manual creation
        """
        return False
    
    def has_change_permission(self, request, obj=None):
        """
        Only allow changing status-related fields.
        
        Args:
            request: Django HTTP request object
            obj: PendingRestaurant instance
            
        Returns:
            bool: True for status changes, False otherwise
        """
        if obj is None:
            return True
        return obj.status == 'pending'


@admin.register(ManagerLoginLog)
class ManagerLoginLogAdmin(admin.ModelAdmin):
    """
    Admin interface for ManagerLoginLog model.
    
    Provides comprehensive monitoring of manager authentication including:
    - Login/logout tracking
    - Session duration analysis
    - IP address monitoring
    - Active session management
    """
    # List display configuration
    list_display = (
        'user',
        'login_time',
        'logout_time',
        'session_duration_display',
        'ip_address',
        'is_active_session_badge',
    )
    
    # List filters
    list_filter = ('is_active_session', 'login_time', 'logout_time')
    
    # Search fields
    search_fields = ('user__username', 'user__email', 'ip_address')
    
    # Ordering
    ordering = ('-login_time',)
    
    # Fields grouping in form
    fieldsets = (
        ('Authentication Information', {
            'fields': ('user', 'login_time', 'logout_time', 'is_active_session')
        }),
        ('Session Details', {
            'fields': ('ip_address', 'user_agent', 'session_duration')
        }),
    )
    
    # Read-only fields
    readonly_fields = ('user', 'login_time', 'ip_address', 'user_agent', 'session_duration')
    
    # Number of items per page
    list_per_page = 25
    
    def session_duration_display(self, obj):
        """
        Display session duration in a readable format.
        
        Args:
            obj: ManagerLoginLog instance
            
        Returns:
            str: Formatted session duration
        """
        if obj.session_duration:
            if obj.session_duration < 60:
                return f"{obj.session_duration} min"
            else:
                hours = obj.session_duration // 60
                minutes = obj.session_duration % 60
                return f"{hours}h {minutes}m"
        elif obj.is_active_session:
            return "Live"
        return "-"
    session_duration_display.short_description = 'Duration'
    session_duration_display.admin_order_field = 'session_duration'
    
    def is_active_session_badge(self, obj):
        """
        Display active session status as a colored badge.
        
        Args:
            obj: ManagerLoginLog instance
            
        Returns:
            str: HTML badge with appropriate color
        """
        if obj.is_active_session:
            return format_html(
                '<span style="background-color: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">● Active</span>'
            )
        return format_html(
            '<span style="background-color: #f3f4f6; color: #6b7280; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">○ Ended</span>'
        )
    is_active_session_badge.short_description = 'Session Status'
    is_active_session_badge.admin_order_field = 'is_active_session'
    
    def get_queryset(self, request):
        """
        Optimize queryset with related objects.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            QuerySet: Optimized queryset with related objects
        """
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        """
        Disable manual creation of login logs through admin.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            bool: False to prevent manual creation
        """
        return False
    
    def has_change_permission(self, request, obj=None):
        """
        Disable editing of login logs through admin.
        
        Args:
            request: Django HTTP request object
            obj: ManagerLoginLog instance
            
        Returns:
            bool: False to prevent manual editing
        """
        return False


@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    """
    Admin interface for RestaurantTable model.
    
    Provides management of restaurant tables and QR codes including:
    - Table creation and management
    - QR code generation and download
    - Table status tracking
    - Capacity management
    """
    # List display configuration
    list_display = (
        'table_number',
        'restaurant',
        'capacity',
        'is_active_badge',
        'location_description',
        'qr_code_preview',
        'download_qr_link',
        'created_at',
    )
    
    # List filters
    list_filter = ('is_active', 'restaurant', 'capacity', 'created_at')
    
    # Search fields
    search_fields = (
        'table_number',
        'restaurant__name',
        'location_description',
        'qr_code_uuid'
    )
    
    # Ordering
    ordering = ('restaurant', 'table_number')
    
    # Fields grouping in form
    fieldsets = (
        ('Table Information', {
            'fields': ('restaurant', 'table_number', 'capacity', 'is_active')
        }),
        ('Location', {
            'fields': ('location_description',)
        }),
        ('QR Code Information', {
            'fields': ('qr_code_uuid', 'qr_code'),
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = ('qr_code_uuid',)
    
    # Number of items per page
    list_per_page = 25
    
    # Custom admin actions
    actions = ['regenerate_qr_codes', 'activate_tables', 'deactivate_tables']
    
    def is_active_badge(self, obj):
        """
        Display table active status as a colored badge.
        
        Args:
            obj: RestaurantTable instance
            
        Returns:
            str: HTML badge with appropriate color
        """
        if obj.is_active:
            return format_html(
                '<span style="background-color: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">✓ Active</span>'
            )
        return format_html(
            '<span style="background-color: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">✗ Inactive</span>'
        )
    is_active_badge.short_description = 'Status'
    is_active_badge.admin_order_field = 'is_active'
    
    def qr_code_preview(self, obj):
        """
        Display QR code as a thumbnail preview.
        
        Args:
            obj: RestaurantTable instance
            
        Returns:
            str: HTML img tag with QR code or placeholder
        """
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="50" height="50" style="border: 1px solid #ddd; border-radius: 4px;" />',
                obj.qr_code.url
            )
        return format_html('<span style="color: #9ca3af;">No QR Code</span>')
    qr_code_preview.short_description = 'QR Code'
    
    def download_qr_link(self, obj):
        """
        Display download link for QR code.
        
        Args:
            obj: RestaurantTable instance
            
        Returns:
            str: HTML link to download QR code
        """
        if obj.qr_code:
            return format_html(
                '<a href="{}" download="table_{}_{}.png" style="color: #2563eb; text-decoration: none; font-weight: 500;">📥 Download</a>',
                obj.qr_code.url,
                obj.restaurant.id,
                obj.table_number
            )
        return format_html('<span style="color: #9ca3af;">-</span>')
    download_qr_link.short_description = 'Actions'
    
    def regenerate_qr_codes(self, request, queryset):
        """
        Admin action to regenerate QR codes for selected tables.
        
        Args:
            request: Django HTTP request object
            queryset: Selected RestaurantTable objects
        """
        count = 0
        failed = 0
        for table in queryset:
            try:
                if table.regenerate_qr_code():
                    count += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                messages.error(request, f'Error regenerating QR code for {table}: {str(e)}')
        
        if count > 0:
            messages.success(request, f'Successfully regenerated {count} QR code(s).')
        if failed > 0:
            messages.warning(request, f'Failed to regenerate {failed} QR code(s).')
    
    regenerate_qr_codes.short_description = 'Regenerate QR codes for selected tables'
    
    def activate_tables(self, request, queryset):
        """
        Admin action to activate selected tables.
        
        Args:
            request: Django HTTP request object
            queryset: Selected RestaurantTable objects
        """
        count = queryset.update(is_active=True)
        messages.success(request, f'Successfully activated {count} table(s).')
    
    activate_tables.short_description = 'Activate selected tables'
    
    def deactivate_tables(self, request, queryset):
        """
        Admin action to deactivate selected tables.
        
        Args:
            request: Django HTTP request object
            queryset: Selected RestaurantTable objects
        """
        count = queryset.update(is_active=False)
        messages.success(request, f'Successfully deactivated {count} table(s).')
    
    deactivate_tables.short_description = 'Deactivate selected tables'
    
    def get_queryset(self, request):
        """
        Optimize queryset with related objects.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            QuerySet: Optimized queryset with related objects
        """
        return super().get_queryset(request).select_related('restaurant')
