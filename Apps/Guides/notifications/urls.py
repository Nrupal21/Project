"""
URL patterns for the notifications app.

This module defines all URL patterns related to user notifications,
including notification listing, detail views, and AJAX endpoints.
Each URL pattern is mapped to its corresponding view function or class.

The URLs are organized into two main groups:
1. Web views for human interaction (notification list and detail pages)
2. AJAX endpoints for dynamic frontend interaction (read/delete operations)

All views include proper authentication checks to ensure users can only
access their own notifications. The AJAX endpoints support the interactive
notification interface in the frontend with minimal page reloads.
"""

from django.urls import path
from . import views

# App namespace for URL reversing
app_name = 'notifications'

# URL patterns for the notifications app
urlpatterns = [
    # Web views - Human-facing pages for viewing notifications
    path('', views.NotificationListView.as_view(), name='notification_list'),  # List all notifications with filtering
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),  # View a single notification in detail
    
    # AJAX endpoints - Support dynamic interaction without page reloads
    path('<int:pk>/read/', views.mark_notification_read, name='mark_read'),  # Mark single notification as read
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),  # Bulk action to mark all as read
    path('<int:pk>/delete/', views.delete_notification, name='delete'),  # Delete a notification
    path('count/', views.notification_count, name='count'),  # Get unread count for navbar badge
]
