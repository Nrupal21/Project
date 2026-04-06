"""
URL patterns for the destinations app.

This module defines all URL patterns related to destinations functionality,
including destination listing, details, API endpoints, and related views.
Each URL pattern is mapped to its corresponding view function or class.

The URLs are organized into several groups:
1. API routes through DRF routers
2. Custom API endpoints
3. Web view routes for regular browsing
4. Specific routes for regions and attractions
5. Admin routes for destination approval workflow

The URL structure follows RESTful conventions where possible and separates
admin/management routes from regular user-facing routes for clarity.
Integration with the notification system is handled through view functions.
"""

# Standard library imports
from django.urls import path, include
from django.contrib.auth.decorators import login_required

# Third-party imports
from rest_framework.routers import DefaultRouter

# Import views from the views package
# Now that we've properly set up the __init__.py file, these imports should work correctly
from .views import (
    # Class-based views for web interface with indigo/violet styling
    DestinationListView,
    GuideDashboardView,
    MyDestinationsView,
    MyAttractionsView,
    DestinationDetailView,
    RegionDetailView,
    AttractionListView,
    AttractionDetailView,
    DestinationCreateView,
    AttractionCreateView,
    
    # API ViewSets for REST endpoints
    DestinationViewSet,
    RegionViewSet,
    AttractionViewSet,
    SeasonViewSet
)

# Import guide views for pending destinations workflow
from .guide_views import (
    PendingDestinationCreateView,
    PendingDestinationUpdateView,
    PendingDestinationDeleteView,
    PendingDestinationImageCreateView,
    PendingDestinationImageListView,
    PendingDestinationListView as GuidePendingDestinationListView,
    SubmissionSuccessView
)

# Import admin views for destination approval workflow
from .views.admin import (
    PendingDestinationListView,
    DestinationReviewView,
    approve_destination,
    reject_destination,
    send_destination_approval_notification,
    send_destination_rejection_notification
)

# Import admin views for pending destination approval workflow
from .views.pending_admin import (
    PendingDestinationListView as AdminPendingDestinationListView,
    PendingDestinationReviewView, 
    approve_pending_destination, 
    reject_pending_destination
)

# Import manager dashboard and upload views
from .views import ManagerDashboardView
from .views.manager_upload import ManagerDestinationUploadView

# Import utility functions and views
from .nearby_destinations import nearby_destinations
from .search_views import destination_search

# Create a router for REST API views
# DefaultRouter automatically creates API endpoints with proper HTTP methods
router = DefaultRouter()

# Register viewsets with the router
# Format: router.register(prefix, viewset, basename)
# - prefix: URL prefix for this viewset
# - viewset: The viewset class
# - basename: Base name used for the URL names (optional if viewset has queryset attribute)

# Register viewsets with the router
# Format: router.register(prefix, viewset, basename)
# - prefix: URL prefix for this viewset
# - viewset: The viewset class
# - basename: Base name used for the URL names (optional if viewset has queryset attribute)

# Destinations API endpoints (GET, POST, PUT, DELETE)
router.register(r'api/destinations', DestinationViewSet)

# Regions API endpoints (GET, POST, PUT, DELETE)
router.register(r'api/regions', RegionViewSet)

# Attractions API endpoints (GET, POST, PUT, DELETE)
# Note: basename is provided explicitly since we use get_queryset() method
router.register(r'api/attractions', AttractionViewSet, basename='attraction')

# Seasons API endpoints (GET only, since it's a ReadOnlyModelViewSet)
router.register(r'api/seasons', SeasonViewSet)

# App namespace for URL reversing
# This allows using 'destinations:name' format in reverse() and {% url %} tags
app_name = 'destinations'

# URL patterns for the destinations app
urlpatterns = [
    # Web views - Destinations (must come before API routes to avoid conflicts)
    path('', DestinationListView.as_view(), name='destination_list'),
    path('dashboard/', login_required(GuideDashboardView.as_view()), name='guide_dashboard'),
    path('my-destinations/', login_required(MyDestinationsView.as_view()), name='my_destinations'),
    
    # PRIMARY GUIDE DESTINATION SUBMISSION WORKFLOW
    # All guide destination submissions now go through the pending approval system
    # This ensures proper moderation and quality control for user-generated content
    
    # Main destination creation route - now primarily for guides (redirects to pending workflow)
    path('create/', login_required(DestinationCreateView.as_view()), name='destination_create'),
    
    # Guide submission workflow routes
    path('submit/', login_required(PendingDestinationCreateView.as_view()), 
         name='pending_destination_create'),  # Submit a new destination for approval
    path('my-submissions/', login_required(PendingDestinationListView.as_view()),
         name='my_pending_destinations'),  # View all guide's submissions and their status
    path('submissions/<int:pk>/edit/', login_required(PendingDestinationUpdateView.as_view()),
         name='pending_destination_update'),  # Edit a pending or rejected submission
    path('submissions/<int:pk>/delete/', login_required(PendingDestinationDeleteView.as_view()),
         name='pending_destination_delete'),  # Delete/withdraw a submission
    path('submissions/<int:pk>/images/', login_required(PendingDestinationImageListView.as_view()),
         name='pending_destination_images'),  # Manage images for a pending destination
    path('submissions/<int:pk>/images/add/', login_required(PendingDestinationImageCreateView.as_view()),
         name='pending_destination_add_image'),  # Add images to a pending destination
    path('submit/success/', login_required(SubmissionSuccessView.as_view()),
         name='submission_success'),  # Success page after destination submission
    
    path('<slug:slug>/', DestinationDetailView.as_view(), name='destination_detail'),
    
    # Region routes
    path('region/<slug:slug>/', RegionDetailView.as_view(), name='region_detail'),
    
    # Attraction routes
    path('attractions/', AttractionListView.as_view(), name='attraction_list'),
    path('attractions/my-attractions/', login_required(MyAttractionsView.as_view()), name='my_attractions'),
    path('attractions/create/', login_required(AttractionCreateView.as_view()), name='attraction_create'),
    path('attractions/create/from-destination/<int:destination_id>/', 
         login_required(AttractionCreateView.as_view()), 
         name='attraction_create_for_destination'),
    path('attractions/<slug:slug>/', AttractionDetailView.as_view(), name='attraction_detail'),
    
    # Admin/Management routes for destination approval workflow
    # Each route is protected by login_required and further guarded by StaffRequiredMixin
    path('admin/dashboard/', login_required(ManagerDashboardView.as_view()),
         name='admin_manager_dashboard'),  # Manager dashboard with approval workflow overview
         
    path('admin/destinations/upload/', login_required(ManagerDestinationUploadView.as_view()),
         name='admin_upload_destination'),  # Direct destination upload for managers
    
    path('admin/pending/', login_required(AdminPendingDestinationListView.as_view()),
         name='admin_pending_destinations'),  # List all pending destinations awaiting review
          
    path('admin/review/<int:pk>/', login_required(PendingDestinationReviewView.as_view()),
         name='admin_review_pending_destination'),  # Detailed review interface for pending destinations
          
    path('admin/approve/<int:pk>/', approve_pending_destination,
         name='admin_approve_pending_destination'),  # Approve and transfer to main destinations table
    
    path('admin/reject/<int:pk>/', reject_pending_destination,
         name='admin_reject_pending_destination'),  # Reject a pending destination with reason and sends notifications
    
    # API routes - Include all router-generated URLs under /api/
    path('api/', include([
        # Include router URLs under /api/
        path('', include(router.urls)),
        # Custom API endpoints under /api/
        path('nearby/', nearby_destinations, name='nearby_destinations'),
    ])),
    
    # Search endpoint for destination autocomplete
    path('search/', destination_search, name='search'),
]
