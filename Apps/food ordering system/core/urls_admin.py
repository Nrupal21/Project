"""
Admin monitoring URLs for comprehensive website analytics.
Privacy-safe aggregated statistics and monitoring endpoints.
Enhanced with real-time analytics and system-wide reporting.
"""

from django.urls import path
from . import admin_views

app_name = 'admin_monitoring'

urlpatterns = [
    # Main comprehensive analytics dashboard
    path('dashboard/', admin_views.monitoring_dashboard, name='monitoring_dashboard'),
    
    # Specialized analytics dashboards
    path('analytics/authentication/', admin_views.authentication_analytics, name='authentication_analytics'),
    path('analytics/business/', admin_views.business_analytics, name='business_analytics'),
    path('analytics/restaurant/', admin_views.restaurant_analytics, name='restaurant_analytics'),
    path('analytics/customer/', admin_views.customer_analytics, name='customer_analytics'),
    path('analytics/health/', admin_views.system_health_analytics, name='system_health_analytics'),
    
    # Legacy analytics routes (maintained for compatibility)
    path('analytics/', admin_views.analytics_trends, name='analytics_trends'),
    path('content/', admin_views.content_monitoring, name='content_monitoring'),
    path('health/', admin_views.system_health, name='health'),
    
    # API endpoints for real-time updates
    path('api/stats/', admin_views.api_real_time_stats, name='api_stats'),
    
    # Export functionality
    path('export/csv/', admin_views.export_analytics_csv, name='export_csv'),
]
