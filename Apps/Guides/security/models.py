"""
Security models for the website.

This module defines database models related to website security features including
security logs, failed login attempts, two-factor authentication records,
security scans, and backup records.
"""

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid
import json
from django.utils import timezone

# Create your models here.

class UserManager(BaseUserManager):
    """
    Custom user manager for handling user creation and management.
    This manager provides methods for creating regular users and superusers.
    """
    
    def create_user(self, email, username, password=None, **extra_fields):
        """
        Creates and saves a regular user with the given email, username and password.
        
        Args:
            email (str): User's email address
            username (str): User's unique username
            password (str): User's password
            **extra_fields: Additional fields for the user
            
        Returns:
            User: The created user object
            
        Raises:
            ValueError: If email or username is not provided
        """
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')
            
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email, username and password.
        
        Args:
            email (str): User's email address
            username (str): User's unique username
            password (str): User's password
            **extra_fields: Additional fields for the user
            
        Returns:
            User: The created superuser object
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
            
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that uses email and username for authentication.
    This model corresponds to the auth_user table in the database.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        """Meta options for the User model.
        
        Uses custom table names to avoid conflicts with Django's built-in User model.
        """
        db_table = 'security_user'
        verbose_name = 'user'
        verbose_name_plural = 'users'
        # Define custom permission table names to avoid conflicts
        permissions = ()
        # Add table names for permissions tables
        swappable = 'AUTH_USER_MODEL'
    
    def __str__(self):
        """
        Returns a string representation of the user.
        
        Returns:
            str: The username of the user
        """
        return self.username
    
    def get_full_name(self):
        """
        Returns the user's full name.
        
        Returns:
            str: The user's full name or username if no name is set
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_short_name(self):
        """
        Returns the user's short name.
        
        Returns:
            str: The user's first name or username if no first name is set
        """
        return self.first_name or self.username


class Role(models.Model):
    """
    Role model for defining user permissions and access levels.
    This model corresponds to the user_role table in the database.
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_role'
        verbose_name = 'role'
        verbose_name_plural = 'roles'
    
    def __str__(self):
        """
        Returns a string representation of the role.
        
        Returns:
            str: The name of the role
        """
        return self.name
    
    def has_permission(self, module, action):
        """
        Checks if the role has a specific permission for a module/action.
        
        Args:
            module (str): The module to check permissions for (e.g., 'destinations')
            action (str): The action to check (e.g., 'create', 'read', 'update', 'delete')
            
        Returns:
            bool: True if the role has the permission, False otherwise
        """
        try:
            # Parse permissions from JSON if stored as string
            perms = self.permissions
            if isinstance(perms, str):
                perms = json.loads(perms)
                
            return perms.get(module, {}).get(action, False)
        except (json.JSONDecodeError, AttributeError):
            return False


class RoleAssignment(models.Model):
    """
    Links users to roles with tracking of who assigned the role.
    This model corresponds to the user_role_assignment table in the database.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='role_assignments_made')
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_role_assignment'
        unique_together = ('user', 'role')
        verbose_name = 'role assignment'
        verbose_name_plural = 'role assignments'
    
    def __str__(self):
        """
        Returns a string representation of the role assignment.
        
        Returns:
            str: A description of the role assignment
        """
        return f"{self.user.username} - {self.role.name}"


class UserPreferences(models.Model):
    """
    User preferences for storing user-specific settings.
    This model corresponds to the accounts_userpreferences table in the database.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='security_preferences')
    language = models.CharField(max_length=10, default='en')
    currency = models.CharField(max_length=10, default='USD')
    timezone = models.CharField(max_length=50, default='UTC')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    marketing_emails = models.BooleanField(default=True)
    newsletter_subscription = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_userpreferences'
        verbose_name = 'user preferences'
        verbose_name_plural = 'user preferences'
    
    def __str__(self):
        """
        Returns a string representation of the user preferences.
        
        Returns:
            str: A description of whose preferences these are
        """
        return f"{self.user.username}'s preferences"


class SecurityLog(models.Model):
    """
    Logs security-related events for the website.
    
    This model records security events such as login attempts, password changes,
    admin actions, and other security-relevant activities for audit purposes.
    It provides a comprehensive audit trail for security monitoring and compliance.
    
    The model uses a structured approach with predefined event types and severity levels
    to ensure consistent logging across the application. Each log entry includes
    contextual information such as user, IP address, timestamp, and additional data
    that might be relevant for security analysis.
    
    Usage examples:
        - Track user authentication events (login/logout)
        - Monitor failed login attempts for potential brute force attacks
        - Log administrative actions for accountability
        - Record security-critical operations like password changes
        - Track two-factor authentication usage
    """
    # Log level choices - defines the severity of the security event
    # These follow standard logging level conventions
    LEVEL_INFO = 'INFO'          # Normal operations, routine events
    LEVEL_WARNING = 'WARNING'    # Potential issues that don't affect operation
    LEVEL_ERROR = 'ERROR'        # Problems that affect functionality
    LEVEL_CRITICAL = 'CRITICAL'  # Severe security incidents requiring immediate attention
    
    LEVEL_CHOICES = [
        (LEVEL_INFO, 'Information'),      # For routine events like successful logins
        (LEVEL_WARNING, 'Warning'),       # For events like multiple failed login attempts
        (LEVEL_ERROR, 'Error'),           # For events like authentication failures
        (LEVEL_CRITICAL, 'Critical'),     # For events like potential breach attempts
    ]
    
    # Event type choices - categorizes the type of security event
    # Authentication events
    EVENT_LOGIN = 'LOGIN'                # User successfully logged in
    EVENT_LOGOUT = 'LOGOUT'              # User logged out
    EVENT_LOGIN_FAIL = 'LOGIN_FAIL'      # Failed login attempt
    EVENT_LOGIN_BLOCKED = 'LOGIN_BLOCKED' # Login blocked due to security policy
    
    # Account management events
    EVENT_PASSWORD_CHANGE = 'PASSWORD_CHANGE'  # User changed their password
    EVENT_PASSWORD_RESET = 'PASSWORD_RESET'    # User requested/completed password reset
    EVENT_USER_CREATED = 'USER_CREATED'        # New user account created
    EVENT_USER_DELETED = 'USER_DELETED'        # User account deleted
    
    # Permission events
    EVENT_PERMISSION_CHANGE = 'PERMISSION_CHANGE'  # User permissions were modified
    EVENT_ADMIN_ACTION = 'ADMIN_ACTION'           # Administrative action performed
    
    # Security feature events
    EVENT_SECURITY_SCAN = 'SECURITY_SCAN'    # Security scan performed
    EVENT_WAF_BLOCK = 'WAF_BLOCK'           # Web Application Firewall blocked request
    EVENT_2FA_ENABLED = '2FA_ENABLED'       # Two-factor authentication enabled
    EVENT_2FA_DISABLED = '2FA_DISABLED'     # Two-factor authentication disabled
    EVENT_2FA_CHALLENGE = '2FA_CHALLENGE'   # Two-factor authentication challenge issued
    
    EVENT_CHOICES = [
        (EVENT_LOGIN, 'User Login'),
        (EVENT_LOGOUT, 'User Logout'),
        (EVENT_LOGIN_FAIL, 'Failed Login Attempt'),
        (EVENT_PASSWORD_CHANGE, 'Password Changed'),
        (EVENT_PASSWORD_RESET, 'Password Reset'),
        (EVENT_USER_CREATED, 'User Account Created'),
        (EVENT_USER_DELETED, 'User Account Deleted'),
        (EVENT_PERMISSION_CHANGE, 'Permission Changed'),
        (EVENT_ADMIN_ACTION, 'Admin Action'),
        (EVENT_SECURITY_SCAN, 'Security Scan'),
        (EVENT_WAF_BLOCK, 'WAF Blocked Request'),
        (EVENT_2FA_ENABLED, '2FA Enabled'),
        (EVENT_2FA_DISABLED, '2FA Disabled'),
        (EVENT_2FA_CHALLENGE, '2FA Challenge'),
        (EVENT_LOGIN_BLOCKED, 'Login Blocked'),
    ]
    
    # Primary fields for security log entries
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text="Unique identifier for the security log entry"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True, 
        db_index=True,
        help_text="When the security event occurred"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="User associated with this security event, if applicable"
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address from which the event originated"
    )
    user_agent = models.TextField(
        null=True, 
        blank=True,
        help_text="Browser/client user agent string"
    )
    event_type = models.CharField(
        max_length=50, 
        choices=EVENT_CHOICES,
        help_text="Type of security event that occurred"
    )
    level = models.CharField(
        max_length=10, 
        choices=LEVEL_CHOICES,
        help_text="Severity level of the security event"
    )
    description = models.TextField(
        help_text="Human-readable description of the security event"
    )
    additional_data = models.JSONField(
        null=True, 
        blank=True,
        help_text="Additional structured data related to the event in JSON format"
    )
    
    def __str__(self):
        """
        Return a string representation of the security log entry.
        
        Creates a formatted string containing the timestamp, severity level,
        event type, and associated user (or 'Anonymous' if no user is associated).
        This representation is used in the admin interface and debugging.
        
        Returns:
            str: A formatted representation of the log entry
        """
        return f"{self.timestamp} - {self.level} - {self.event_type} - {self.user or 'Anonymous'}"
    
    class Meta:
        """
        Meta options for the SecurityLog model.
        
        Defines ordering, verbose names, and database indexes for optimized queries.
        The model is configured for efficient retrieval of security logs with:
        - Reverse chronological ordering (newest first)
        - Indexes on commonly queried fields for performance
        - Appropriate verbose names for admin interface
        """
        ordering = ['-timestamp']  # Most recent events first
        verbose_name = 'Security Log'
        verbose_name_plural = 'Security Logs'
        indexes = [
            models.Index(fields=['timestamp']),   # For time-based filtering and sorting
            models.Index(fields=['event_type']),  # For filtering by event type
            models.Index(fields=['level']),       # For filtering by severity level
            models.Index(fields=['user']),        # For filtering by user
        ]


class FailedLoginAttempt(models.Model):
    """
    Tracks failed login attempts for rate limiting and security monitoring.
    
    This model is used to implement security features like login throttling
    and detecting brute force attacks by tracking consecutive failed attempts.
    """
    username = models.CharField(max_length=150, db_index=True)
    ip_address = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_locked = models.BooleanField(default=False)
    lock_expiry = models.DateTimeField(null=True, blank=True)
    attempt_count = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        """
        Return a string representation of the failed login attempt.
        
        Returns:
            str: A description of the failed login attempt
        """
        return f"{self.username} - {self.ip_address} - {self.timestamp}"
    
    @classmethod
    def record_failure(cls, username, ip_address, user_agent=None):
        """
        Record a failed login attempt and determine if the account should be locked.
        
        Increments the attempt counter or creates a new record if needed.
        Locks the account after multiple consecutive failures.
        
        Args:
            username (str): The username that failed to login
            ip_address (str): The IP address of the request
            user_agent (str, optional): The user agent string
            
        Returns:
            tuple: (bool, int) - (is_locked, minutes_until_unlock)
        """
        # Get recent attempts from this IP for this username
        cutoff_time = timezone.now() - timezone.timedelta(minutes=30)
        recent_attempts = cls.objects.filter(
            username=username,
            ip_address=ip_address,
            timestamp__gte=cutoff_time
        ).order_by('-timestamp')
        
        if recent_attempts.exists():
            attempt = recent_attempts.first()
            attempt.attempt_count += 1
            
            # Lock the account after 5 failed attempts
            if attempt.attempt_count >= 5 and not attempt.is_locked:
                attempt.is_locked = True
                # Lock for 30 minutes
                attempt.lock_expiry = timezone.now() + timezone.timedelta(minutes=30)
                
            attempt.timestamp = timezone.now()
            attempt.save()
        else:
            attempt = cls.objects.create(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent
            )
        
        # Calculate minutes until unlock if locked
        minutes_until_unlock = 0
        if attempt.is_locked and attempt.lock_expiry:
            delta = attempt.lock_expiry - timezone.now()
            minutes_until_unlock = max(0, int(delta.total_seconds() / 60))
            
        return (attempt.is_locked, minutes_until_unlock)
    
    @classmethod
    def is_account_locked(cls, username, ip_address):
        """
        Check if a username is currently locked due to too many failed attempts.
        
        Args:
            username (str): The username to check
            ip_address (str): The IP address of the request
            
        Returns:
            tuple: (bool, int) - (is_locked, minutes_until_unlock)
        """
        cutoff_time = timezone.now() - timezone.timedelta(minutes=30)
        recent_attempts = cls.objects.filter(
            username=username,
            ip_address=ip_address,
            timestamp__gte=cutoff_time,
            is_locked=True
        ).first()
        
        if recent_attempts and recent_attempts.lock_expiry:
            # If lock has expired, remove the lock
            if recent_attempts.lock_expiry <= timezone.now():
                recent_attempts.is_locked = False
                recent_attempts.save()
                return (False, 0)
                
            # Calculate minutes until unlock
            delta = recent_attempts.lock_expiry - timezone.now()
            minutes_until_unlock = max(0, int(delta.total_seconds() / 60))
            return (True, minutes_until_unlock)
            
        return (False, 0)
    
    class Meta:
        """
        Meta options for the FailedLoginAttempt model.
        
        Defines ordering and indexes for query optimization.
        """
        ordering = ['-timestamp']
        verbose_name = 'Failed Login Attempt'
        verbose_name_plural = 'Failed Login Attempts'
        indexes = [
            models.Index(fields=['username', 'ip_address']),
            models.Index(fields=['is_locked']),
        ]


class TwoFactorAuth(models.Model):
    """
    Stores data for two-factor authentication.
    
    This model tracks which users have 2FA enabled and stores
    the necessary data for verifying 2FA tokens.
    """
    # 2FA method choices
    METHOD_APP = 'APP'       # Authenticator app (TOTP)
    METHOD_EMAIL = 'EMAIL'   # Email verification
    METHOD_SMS = 'SMS'       # SMS verification
    
    METHOD_CHOICES = [
        (METHOD_APP, 'Authenticator App'),
        (METHOD_EMAIL, 'Email Verification'),
        (METHOD_SMS, 'SMS Verification'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='two_factor')
    is_enabled = models.BooleanField(default=False)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default=METHOD_APP)
    secret_key = models.CharField(max_length=100, blank=True)  # For TOTP
    backup_codes = models.JSONField(default=list, blank=True)  # List of one-time backup codes
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # For SMS verification
    last_verified = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Return a string representation of the two-factor auth record.
        
        Returns:
            str: A description of the 2FA status for a user
        """
        status = "Enabled" if self.is_enabled else "Disabled"
        return f"{self.user.username} - 2FA {status} ({self.method})"
    
    def generate_backup_codes(self, count=8):
        """
        Generate a set of one-time backup codes for the user.
        
        Args:
            count (int): Number of backup codes to generate
            
        Returns:
            list: The newly generated backup codes
        """
        import secrets
        import string
        
        # Generate random 8-character backup codes
        alphabet = string.ascii_letters + string.digits
        codes = [
            ''.join(secrets.choice(alphabet) for _ in range(8))
            for _ in range(count)
        ]
        
        # Store codes in the database (in practice, these would be hashed)
        self.backup_codes = codes
        self.save()
        
        return codes
    
    def verify_backup_code(self, code):
        """
        Verify and consume a backup code if valid.
        
        Args:
            code (str): The backup code to verify
            
        Returns:
            bool: True if the code was valid and consumed, False otherwise
        """
        if code in self.backup_codes:
            # Remove the used code
            self.backup_codes.remove(code)
            self.save()
            return True
        return False
    
    class Meta:
        """
        Meta options for the TwoFactorAuth model.
        
        Defines verbose names.
        """
        verbose_name = 'Two-Factor Authentication'
        verbose_name_plural = 'Two-Factor Authentications'


class SecurityScan(models.Model):
    """
    Records security vulnerability scans performed on the website.
    
    Tracks scheduled and on-demand security scans including
    scan type, results, and identified vulnerabilities.
    """
    # Scan type choices
    TYPE_FULL = 'FULL'
    TYPE_QUICK = 'QUICK'
    TYPE_TARGETED = 'TARGETED'
    
    TYPE_CHOICES = [
        (TYPE_FULL, 'Full Scan'),
        (TYPE_QUICK, 'Quick Scan'),
        (TYPE_TARGETED, 'Targeted Scan'),
    ]
    
    # Scan status choices
    STATUS_SCHEDULED = 'SCHEDULED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'
    
    STATUS_CHOICES = [
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scan_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    scheduled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    result_summary = models.TextField(blank=True)
    vulnerabilities_found = models.JSONField(default=list, blank=True)
    scan_tool = models.CharField(max_length=100, blank=True)  # Name of tool used for scanning
    target_url = models.URLField(blank=True)  # Specific URL for targeted scans
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        """
        Return a string representation of the security scan.
        
        Returns:
            str: A description of the security scan
        """
        date_str = self.start_time.strftime('%Y-%m-%d %H:%M') if self.start_time else 'Not started'
        return f"{self.scan_type} Scan - {self.status} - {date_str}"
    
    def duration(self):
        """
        Calculate the duration of the scan if completed.
        
        Returns:
            timedelta or None: The duration of the scan or None if not completed
        """
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    class Meta:
        """
        Meta options for the SecurityScan model.
        
        Defines ordering and verbose names.
        """
        ordering = ['-created_at']
        verbose_name = 'Security Scan'
        verbose_name_plural = 'Security Scans'


class BackupRecord(models.Model):
    """
    Tracks website backups for disaster recovery.
    
    Records details about scheduled and on-demand backups including
    status, storage location, and verification results.
    """
    # Backup type choices
    TYPE_FULL = 'FULL'
    TYPE_INCREMENTAL = 'INCREMENTAL'
    TYPE_DATABASE = 'DATABASE'
    TYPE_FILES = 'FILES'
    
    TYPE_CHOICES = [
        (TYPE_FULL, 'Full Backup'),
        (TYPE_INCREMENTAL, 'Incremental Backup'),
        (TYPE_DATABASE, 'Database Only'),
        (TYPE_FILES, 'Files Only'),
    ]
    
    # Backup status choices
    STATUS_SCHEDULED = 'SCHEDULED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'
    STATUS_VERIFIED = 'VERIFIED'
    
    STATUS_CHOICES = [
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_VERIFIED, 'Verified'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    backup_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    size_bytes = models.BigIntegerField(null=True, blank=True)
    file_count = models.IntegerField(null=True, blank=True)
    storage_location = models.CharField(max_length=255)  # S3, Google Drive, local path, etc.
    storage_path = models.CharField(max_length=255)
    is_automated = models.BooleanField(default=True)  # Whether this was an automated backup
    initiated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    verification_result = models.TextField(blank=True)  # Results of verification check
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    retention_days = models.IntegerField(default=30)  # How many days to keep this backup
    
    def __str__(self):
        """
        Return a string representation of the backup record.
        
        Returns:
            str: A description of the backup
        """
        date_str = self.start_time.strftime('%Y-%m-%d %H:%M') if self.start_time else 'Not started'
        return f"{self.backup_type} Backup - {self.status} - {date_str}"
    
    def is_expired(self):
        """
        Check if the backup has exceeded its retention period.
        
        Returns:
            bool: True if the backup should be deleted based on retention policy
        """
        if not self.created_at:
            return False
            
        expiry_date = self.created_at + timezone.timedelta(days=self.retention_days)
        return timezone.now() > expiry_date
    
    class Meta:
        """
        Meta options for the BackupRecord model.
        
        Defines ordering and verbose names.
        """
        ordering = ['-created_at']
        verbose_name = 'Backup Record'
        verbose_name_plural = 'Backup Records'
