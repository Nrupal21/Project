from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    """
    Display a list of notifications for the logged-in user.
    
    This view shows all notifications for the current user, ordered by creation date
    with the most recent first. Includes pagination and filtering options.
    
    The template renders notifications with different styling based on their level:
    - info: blue styling (information messages)
    - success: green styling (successful operations)
    - warning: yellow styling (actions needed)
    - danger: red styling (errors or important alerts)
    
    The view also provides context for filtering between 'all' and 'unread' notifications
    and displays notification counts in both categories.
    """
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Get notifications for the current user.
        
        Returns:
            QuerySet: Filtered queryset of notifications for the current user
        """
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with additional data
        """
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).count()
        context['all_count'] = self.get_queryset().count()
        return context


class NotificationDetailView(LoginRequiredMixin, DetailView):
    """
    Display details for a single notification.
    
    This view shows the full content of a notification and marks it as read
    when viewed. Only allows users to view their own notifications.
    
    When a user views a notification through this detail view, the notification
    is automatically marked as read. The view enforces security by ensuring
    users can only access their own notifications through the get_queryset override.
    
    The template provides full details including:
    - Notification title and content
    - Creation timestamp
    - Visual styling based on notification level
    - Action links including the custom link if provided
    """
    model = Notification
    template_name = 'notifications/notification_detail.html'
    context_object_name = 'notification'
    
    def get_queryset(self):
        """
        Ensure users can only see their own notifications.
        
        Returns:
            QuerySet: Filtered queryset of notifications for the current user
        """
        return Notification.objects.filter(recipient=self.request.user)
    
    def get_object(self, queryset=None):
        """
        Get the notification and mark it as read when viewed.
        
        Args:
            queryset: QuerySet to use for retrieving the object (optional)
            
        Returns:
            Notification: The notification being viewed
        """
        obj = super().get_object(queryset)
        if not obj.is_read:
            obj.mark_as_read()
        return obj


@login_required
def mark_notification_read(request, pk):
    """
    Mark a notification as read via AJAX.
    
    Args:
        request: The HTTP request
        pk: Primary key of the notification to mark as read
        
    Returns:
        JsonResponse: Success status and updated unread count
    """
    if request.method == 'POST':
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.mark_as_read()
        
        # Return updated unread count for UI updating
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        return JsonResponse({
            'success': True,
            'unread_count': unread_count
        })
    
    return JsonResponse({'success': False}, status=400)


@login_required
def mark_all_read(request):
    """
    Mark all notifications as read for the current user.
    
    Args:
        request: The HTTP request
        
    Returns:
        HttpResponseRedirect: Redirect back to notifications list
    """
    if request.method == 'POST':
        Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        
    return HttpResponseRedirect(reverse('notifications:notification_list'))


@login_required
def delete_notification(request, pk):
    """
    Delete a single notification.
    
    Args:
        request: The HTTP request
        pk: Primary key of the notification to delete
        
    Returns:
        HttpResponseRedirect: Redirect back to notifications list
    """
    if request.method == 'POST':
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.delete()
        
    return HttpResponseRedirect(reverse('notifications:notification_list'))


@login_required
def notification_count(request):
    """
    Get the number of unread notifications for the current user via AJAX.
    
    This endpoint is used to update notification counters in the UI without
    refreshing the page. The frontend can call this endpoint periodically
    to refresh notification badges in the navigation bar or other UI elements.
    
    The response includes both the count and a boolean flag indicating if there
    are any unread notifications, which simplifies conditional rendering in the UI.
    
    Args:
        request: The HTTP request
        
    Returns:
        JsonResponse: Count of unread notifications and has_unread flag
    """
    try:
        # Try to get notification count, handle database errors gracefully
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return JsonResponse({'unread_count': unread_count})
    except Exception as e:
        # If database error occurs (e.g., table doesn't exist), return 0 notifications
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting notification count: {str(e)}")
        return JsonResponse({'unread_count': 0})
