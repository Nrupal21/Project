"""
URL configuration for food_ordering project.
Routes URLs to appropriate app views.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.health_check import health_check, readiness_check, liveness_check

# Main URL patterns for the entire project
urlpatterns = [
    # Health check endpoints for monitoring and load balancers
    path('health/', health_check, name='health_check'),
    path('readiness/', readiness_check, name='readiness_check'),
    path('liveness/', liveness_check, name='liveness_check'),
    
    # Admin monitoring dashboard (privacy-safe analytics) - MUST come before admin.site.urls
    path('admin/monitoring/', include('core.urls_admin')),
    
    # Django admin interface
    path('admin/', admin.site.urls),
    
    # Core authentication routes (unified login/logout)
    path('auth/', include('core.urls')),
    
    # Customer-facing routes (home, menu, cart, checkout)
    path('', include('customer.urls')),
    
    # Restaurant dashboard routes
    path('restaurant/', include('restaurant.urls')),
    
    # Order management and promo codes
    path('orders/', include('orders.urls')),
]

# Serve media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
