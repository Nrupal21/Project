from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.conf import settings


class Notification(models.Model):
    """
    Model for storing user notifications.
    
    This model represents notifications sent to users throughout the system.
    Notifications are linked to specific users and can reference any model
    in the system through a generic foreign key relationship.
    
    The notification system supports four different importance levels (info, success,
    warning, danger) which determine the visual styling in the UI. Each notification
    can also include an optional link to direct users to relevant pages.
    
    The UI for notifications uses the indigo/violet color theme for consistent
    styling across the application. Urgent notifications use a more prominent
    shade of violet for better visibility.
    
    The model includes a generic foreign key relationship allowing notifications
    to be associated with any object in the system (e.g., a new comment, an approved
    destination, a booking confirmation, etc.).
    
    Attributes:
        recipient: The user who will receive this notification
        title: Brief title/heading of the notification
        message: Full notification content/body text
        level: Importance level (info, success, warning, danger)
        is_read: Whether the user has read this notification
        created_at: When this notification was created
        content_type: Type of the related object (optional)
        object_id: ID of the related object (optional)
        content_object: Related object this notification is about (optional)
        link_url: Optional URL to include with the notification
        link_text: Text for the link button (if link_url is provided)
    """
    
    # Notification model configuration and metadata
    # Notification importance levels
    LEVEL_INFO = 'info'
    LEVEL_SUCCESS = 'success'
    LEVEL_WARNING = 'warning'
    LEVEL_DANGER = 'danger'
    
    LEVEL_CHOICES = [
        (LEVEL_INFO, 'Information'),
        (LEVEL_SUCCESS, 'Success'),
        (LEVEL_WARNING, 'Warning'),
        (LEVEL_DANGER, 'Danger'),
    ]
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User who will receive this notification"
    )
    title = models.CharField(max_length=255, help_text="Brief title for the notification")
    message = models.TextField(help_text="Main content of the notification")
    level = models.CharField(
        max_length=20, 
        choices=LEVEL_CHOICES,
        default=LEVEL_INFO,
        help_text="Importance level of this notification"
    )
    is_read = models.BooleanField(default=False, help_text="Whether this notification has been read")
    created_at = models.DateTimeField(default=timezone.now, help_text="When this notification was created")
    
    # Generic relation to any model (optional)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Type of the related object"
    )
    object_id = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="ID of the related object"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Optional link to include with notification
    link_url = models.CharField(max_length=255, null=True, blank=True, help_text="URL to include with notification")
    link_text = models.CharField(max_length=100, null=True, blank=True, help_text="Text for the link button")
    
    class Meta:
        app_label = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        """
        Return string representation of this notification.
        
        Returns:
            str: Notification title and recipient username
        """
        return f"{self.title} (to {self.recipient.username})"
    
    def mark_as_read(self):
        """
        Mark this notification as read and save it.
        """
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
            
    def get_absolute_url(self):
        """
        Get the URL for viewing this notification.
        
        If a link_url is specified, returns that; otherwise returns
        the URL to the notification detail view.
        
        Returns:
            str: URL for this notification
        """
        if self.link_url:
            return self.link_url
        return reverse('notifications:notification_detail', args=[self.pk])
    
    @classmethod
    def create_notification(cls, recipient, title, message, level=LEVEL_INFO, 
                          related_object=None, link_url=None, link_text=None):
        """
        Create and save a new notification.
        
        This is a convenience method to create notifications more easily
        from anywhere in the codebase.
        
        Args:
            recipient: User who will receive this notification
            title: Brief title/heading
            message: Full notification content
            level: Importance level (info, success, warning, danger)
            related_object: Object this notification is about (optional)
            link_url: URL to include with notification (optional)
            link_text: Text for the link button (optional)
            
        Returns:
            Notification: The created notification instance
        """
        notification = cls(
            recipient=recipient,
            title=title,
            message=message,
            level=level,
            link_url=link_url,
            link_text=link_text
        )
        
        # Set the related object if provided
        if related_object:
            notification.content_object = related_object
            
        notification.save()
        return notification
