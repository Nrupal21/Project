"""
Admin configuration for security app models.

This module registers security models with Django's admin site and
customizes their appearance, filtering capabilities, and search functionality
for better management by administrators.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import SecurityLog, FailedLoginAttempt, TwoFactorAuth, SecurityScan, BackupRecord


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    """
    Admin interface for security log entries.
    
    Provides detailed view of security events with advanced filtering
    and search capabilities for security monitoring and auditing.
    """
    list_display = ('timestamp', 'level_colored', 'event_type', 'user_link', 'ip_address', 'short_description')
    list_filter = ('level', 'event_type', 'timestamp')
    search_fields = ('user__username', 'ip_address', 'description')
    readonly_fields = ('id', 'timestamp', 'user', 'ip_address', 'user_agent', 'event_type', 'level', 
                       'description', 'additional_data')
    date_hierarchy = 'timestamp'
    fieldsets = (
        ('Event Information', {
            'fields': ('id', 'timestamp', 'event_type', 'level', 'description')
        }),
        ('User Information', {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        ('Additional Data', {
            'fields': ('additional_data',),
            'classes': ('collapse',)
        }),
    )
    
    def short_description(self, obj):
        """
        Display a shortened version of the description.
        
        Returns:
            str: Truncated description with ellipsis if needed
        """
        if len(obj.description) > 100:
            return obj.description[:97] + '...'
        return obj.description
    short_description.short_description = 'Description'
    
    def level_colored(self, obj):
        """
        Display the log level with appropriate color coding.
        
        Returns:
            str: HTML formatted log level with color
        """
        colors = {
            'INFO': 'green',
            'WARNING': 'orange',
            'ERROR': 'red',
            'CRITICAL': 'purple'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.level, 'black'),
            obj.level
        )
    level_colored.short_description = 'Level'
    
    def user_link(self, obj):
        """
        Create a clickable link to the user's admin page.
        
        Returns:
            str: HTML link to user admin page or 'Anonymous'
        """
        if obj.user:
            # Use the app_label and model_name from the custom user model
            url = reverse(f'admin:{obj.user._meta.app_label}_{obj.user._meta.model_name}_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return 'Anonymous'
    user_link.short_description = 'User'
    
    def has_add_permission(self, request):
        """
        Prevent adding log entries manually.
        
        Returns:
            bool: False to disable adding logs through admin
        """
        return False
    
    def has_change_permission(self, request, obj=None):
        """
        Prevent modifying log entries.
        
        Returns:
            bool: False to disable editing logs
        """
        return False


@admin.register(FailedLoginAttempt)
class FailedLoginAttemptAdmin(admin.ModelAdmin):
    """
    Admin interface for failed login attempts.
    
    Provides monitoring of suspicious login activity and tools to
    manage account lockouts for security administration.
    """
    list_display = ('username', 'ip_address', 'timestamp', 'attempt_count', 'lock_status', 'time_remaining')
    list_filter = ('is_locked', 'timestamp')
    search_fields = ('username', 'ip_address')
    readonly_fields = ('timestamp', 'username', 'ip_address', 'user_agent', 'attempt_count')
    date_hierarchy = 'timestamp'
    actions = ['unlock_accounts']
    
    def lock_status(self, obj):
        """
        Display lock status with color coding.
        
        Returns:
            str: HTML formatted lock status
        """
        if obj.is_locked:
            if obj.lock_expiry and obj.lock_expiry > timezone.now():
                return format_html('<span style="color: red; font-weight: bold;">Locked</span>')
            else:
                return format_html('<span style="color: orange;">Expired</span>')
        return format_html('<span style="color: green;">Unlocked</span>')
    lock_status.short_description = 'Status'
    
    def time_remaining(self, obj):
        """
        Calculate and display time remaining for locked accounts.
        
        Returns:
            str: Minutes remaining until unlock or empty string
        """
        if not obj.is_locked or not obj.lock_expiry:
            return ""
            
        if obj.lock_expiry < timezone.now():
            return "Expired"
            
        delta = obj.lock_expiry - timezone.now()
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} remaining"
    time_remaining.short_description = 'Lock Time Remaining'
    
    def unlock_accounts(self, request, queryset):
        """
        Admin action to unlock selected accounts.
        
        Args:
            request: The HTTP request
            queryset: Selected failed login attempt objects
        """
        count = queryset.update(is_locked=False, lock_expiry=None)
        self.message_user(
            request,
            f"{count} account{'s' if count != 1 else ''} has been unlocked."
        )
    unlock_accounts.short_description = "Unlock selected accounts"


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    """
    Admin interface for two-factor authentication settings.
    
    Provides tools to manage 2FA settings, generate backup codes,
    and monitor users' security configurations.
    """
    list_display = ('user', 'method', 'is_enabled', 'last_verified', 'created_at')
    list_filter = ('is_enabled', 'method', 'created_at')
    search_fields = ('user__username', 'user__email')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at', 'last_verified')
    actions = ['reset_2fa']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_enabled')
        }),
        ('Authentication Method', {
            'fields': ('method', 'secret_key', 'phone_number')
        }),
        ('Backup Codes', {
            'fields': ('backup_codes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('last_verified', 'created_at', 'updated_at')
        }),
    )
    
    def reset_2fa(self, request, queryset):
        """
        Admin action to reset 2FA for selected users.
        
        Disables 2FA and clears all associated data for the selected users.
        
        Args:
            request: The HTTP request
            queryset: Selected TwoFactorAuth objects
        """
        count = queryset.update(
            is_enabled=False,
            secret_key="",
            backup_codes=[],
        )
        self.message_user(
            request,
            f"Two-factor authentication has been reset for {count} user{'s' if count != 1 else ''}."
        )
    reset_2fa.short_description = "Reset two-factor authentication for selected users"


@admin.register(SecurityScan)
class SecurityScanAdmin(admin.ModelAdmin):
    """
    Admin interface for security vulnerability scans.
    
    Provides tools to schedule and monitor security scans, view results,
    and manage identified vulnerabilities.
    """
    list_display = ('scan_type', 'status', 'start_time', 'end_time', 'scan_duration', 'vulnerability_count')
    list_filter = ('status', 'scan_type', 'created_at')
    search_fields = ('scan_tool', 'result_summary', 'target_url')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'
    actions = ['mark_completed', 'mark_failed']
    
    def scan_duration(self, obj):
        """
        Calculate and display the duration of the scan.
        
        Returns:
            str: Formatted scan duration or status message
        """
        if obj.status == SecurityScan.STATUS_COMPLETED and obj.start_time and obj.end_time:
            duration = obj.end_time - obj.start_time
            seconds = duration.total_seconds()
            if seconds < 60:
                return f"{seconds:.1f} seconds"
            minutes = seconds / 60
            if minutes < 60:
                return f"{minutes:.1f} minutes"
            hours = minutes / 60
            return f"{hours:.1f} hours"
        elif obj.status == SecurityScan.STATUS_IN_PROGRESS and obj.start_time:
            return "In progress"
        elif obj.status == SecurityScan.STATUS_SCHEDULED:
            return "Not started"
        else:
            return "N/A"
    scan_duration.short_description = 'Duration'
    
    def vulnerability_count(self, obj):
        """
        Display the number of vulnerabilities found.
        
        Returns:
            str: Count of vulnerabilities with color coding
        """
        if not obj.vulnerabilities_found or obj.status != SecurityScan.STATUS_COMPLETED:
            return "-"
            
        count = len(obj.vulnerabilities_found)
        color = "green"
        if count > 0:
            color = "red" if count > 3 else "orange"
            
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, count)
    vulnerability_count.short_description = "Vulnerabilities"
    
    def mark_completed(self, request, queryset):
        """
        Mark selected scans as completed.
        
        Args:
            request: The HTTP request
            queryset: Selected SecurityScan objects
        """
        for scan in queryset.filter(status=SecurityScan.STATUS_IN_PROGRESS):
            scan.status = SecurityScan.STATUS_COMPLETED
            scan.end_time = timezone.now()
            scan.save()
            
        self.message_user(request, "Selected scans have been marked as completed.")
    mark_completed.short_description = "Mark selected scans as completed"
    
    def mark_failed(self, request, queryset):
        """
        Mark selected scans as failed.
        
        Args:
            request: The HTTP request
            queryset: Selected SecurityScan objects
        """
        for scan in queryset.filter(status=SecurityScan.STATUS_IN_PROGRESS):
            scan.status = SecurityScan.STATUS_FAILED
            scan.end_time = timezone.now()
            scan.save()
            
        self.message_user(request, "Selected scans have been marked as failed.")
    mark_failed.short_description = "Mark selected scans as failed"


@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for backup records.
    
    Provides tools to manage website backups, monitor backup status,
    and track backup verification results.
    """
    list_display = ('backup_type', 'status', 'start_time', 'size_display', 'storage_location', 'retention_info')
    list_filter = ('status', 'backup_type', 'is_automated', 'created_at')
    search_fields = ('storage_location', 'storage_path', 'initiated_by__username')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'
    actions = ['mark_verified', 'mark_failed']
    
    def size_display(self, obj):
        """
        Format file size in human-readable format.
        
        Returns:
            str: Formatted file size (KB, MB, GB)
        """
        if not obj.size_bytes:
            return "-"
            
        # Convert bytes to appropriate unit
        size_kb = obj.size_bytes / 1024
        if size_kb < 1024:
            return f"{size_kb:.1f} KB"
        size_mb = size_kb / 1024
        if size_mb < 1024:
            return f"{size_mb:.1f} MB"
        size_gb = size_mb / 1024
        return f"{size_gb:.2f} GB"
    size_display.short_description = "Size"
    
    def retention_info(self, obj):
        """
        Display backup retention status with expiration info.
        
        Returns:
            str: Days left before expiration, with color coding
        """
        if not obj.created_at:
            return "-"
            
        expiry_date = obj.created_at + timezone.timedelta(days=obj.retention_days)
        days_left = (expiry_date - timezone.now()).days
        
        if days_left < 0:
            return format_html('<span style="color: red;">Expired</span>')
        elif days_left <= 7:
            return format_html('<span style="color: orange;">{} days left</span>', days_left)
        else:
            return format_html('{} days left', days_left)
    retention_info.short_description = "Retention"
    
    def mark_verified(self, request, queryset):
        """
        Mark selected backups as verified.
        
        Args:
            request: The HTTP request
            queryset: Selected BackupRecord objects
        """
        count = queryset.filter(status=BackupRecord.STATUS_COMPLETED).update(
            status=BackupRecord.STATUS_VERIFIED,
            verification_result="Verified by admin at " + timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        self.message_user(request, f"{count} backup(s) marked as verified.")
    mark_verified.short_description = "Mark selected backups as verified"
    
    def mark_failed(self, request, queryset):
        """
        Mark selected backups as failed.
        
        Args:
            request: The HTTP request
            queryset: Selected BackupRecord objects
        """
        count = queryset.filter(
            status__in=[BackupRecord.STATUS_SCHEDULED, BackupRecord.STATUS_IN_PROGRESS]
        ).update(
            status=BackupRecord.STATUS_FAILED,
            error_message="Marked as failed by admin at " + timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            end_time=timezone.now()
        )
        self.message_user(request, f"{count} backup(s) marked as failed.")
    mark_failed.short_description = "Mark selected backups as failed"
