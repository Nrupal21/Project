"""
URL Configuration for the Accounts application.

This module defines URL patterns for all account-related functionality including:
- User authentication (login, logout, registration)
- Password management (reset, change)
- Email verification flows using the new VerificationToken model
- Profile and settings management
- User activity views (favorites, bookings, reviews)
- API endpoints for account-related actions
"""

from django.urls import path, include
from . import views
from . import auth_views
from . import views_profile
from . import verification_views_new as verification_views
from . import admin_urls  # Import admin URLs for role management
from django.contrib.auth import views as django_auth_views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs - Handle user login, logout, and registration
    path('login/', auth_views.UserLoginView.as_view(), name='login'),  # Custom login with additional features
    path('logout/', auth_views.UserLogoutView.as_view(), name='logout'),  # Logout with redirect configuration
    
    # User registration with role-based paths
    path('register/', auth_views.UserRegisterView.as_view(), name='register'),  # Default registration (traveler)
    path('register/traveler/', auth_views.UserRegisterView.as_view(), name='register_traveler'),  # Traveler registration
    
    # Guide application URLs - Process for becoming a local guide
    path('guide-application/', auth_views.GuideApplicationView.as_view(), name='guide_application'),  # Apply to be a guide
    path('guide-application/submitted/', auth_views.GuideApplicationSubmittedView.as_view(), name='guide_application_submitted'),  # Application confirmation
    
    # Admin guide application review URLs
    path('admin/guide-applications/', auth_views.AdminGuideApplicationListView.as_view(), name='admin_guide_applications'),  # List all applications
    path('admin/guide-applications/<int:pk>/', auth_views.GuideApplicationReviewView.as_view(), name='review_guide_application'),  # Review specific application
    
    # Password management - Reset and recovery workflows
    path('password-change/', auth_views.UserPasswordChangeView.as_view(), name='password_change'),  # Change password form
    path('password-change/done/', auth_views.UserPasswordChangeDoneView.as_view(), name='password_change_done'),  # Password change success
    path('password-reset/', auth_views.UserPasswordResetView.as_view(), name='password_reset'),  # Request password reset
    path('password-reset/done/', auth_views.UserPasswordResetDoneView.as_view(), name='password_reset_done'),  # Reset request sent
    path('reset/<uidb64>/<token>/', auth_views.UserPasswordResetConfirmView.as_view(), name='password_reset_confirm'),  # Reset form
    path('reset/done/', auth_views.UserPasswordResetCompleteView.as_view(), name='password_reset_complete'),  # Reset successful
    
    # Updated Email verification URLs - Using the new VerificationToken model
    path('verify/<str:token>/', verification_views.verify_email_view, name='verify_email'),  # Process verification links
    path('verification_required/', verification_views.verification_required_view, name='verification_required'),  # Page shown when verification is needed
    path('api/resend_verification_email/', verification_views.resend_verification_email_view, name='resend_verification_email'),  # AJAX endpoint for resending verification
    
    # Profile URLs - View and edit user profiles
    path('profile/', views.profile_view, name='profile'),  # User's profile dashboard
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),  # Edit basic profile information
    
    # Account settings URLs - Manage all user account settings
    path('settings/', views_profile.profile_view, name='settings'),  # Main settings page with tabs
    path('settings/profile/', views_profile.update_profile, name='update_profile'),  # Update profile information
    path('settings/password/', views_profile.update_password, name='change_password'),  # Change password
    path('settings/preferences/', views_profile.update_preferences, name='update_preferences'),  # Update travel preferences
    path('settings/notifications/', views_profile.update_notifications, name='update_notifications'),  # Update notification settings
    
    # User activity URLs - View user-specific content and history
    path('preferences/', views.preferences_view, name='preferences'),  # View/edit travel preferences
    path('favorites/', views.favorites_view, name='favorites'),  # View saved favorites
    path('favorites/add/', views.add_favorite_view, name='add_favorite'),  # Add a new favorite
    path('favorites/remove/<int:favorite_id>/', views.remove_favorite_view, name='remove_favorite'),  # Remove a favorite
    
    # User activity related views
    path('activity/', views.activity_view, name='activity'),  # View recent account activity
    path('bookings/', views.user_bookings_view, name='bookings'),  # View bookings history
    path('reviews/', views.user_reviews_view, name='reviews'),  # View submitted reviews
    
    # API endpoints for AJAX interactions
    path('api/preferences/', views.preferences_api, name='preferences_api'),  # API for updating user preferences
    path('api/favorites/', views.favorites_api, name='favorites_api'),  # API for managing favorites via AJAX
    path('api/profile/', views.profile_api, name='profile_api'),  # API for retrieving/updating profile data
    
    # API endpoints for account operations
    path('api/update_profile/', views.profile_api, name='api_update_profile'),  # API endpoint for profile updates
    path('api/change_avatar/', views.profile_api, name='api_change_avatar'),  # Change profile picture
    
    # Two-factor authentication is handled by the security app
    # The 2FA URLs are included in the security app's urls.py
    
    # Admin role management URLs - Only accessible to admins via AdminRequiredMixin
    path('admin/', include(admin_urls)),  # Include all admin URLs for role management
    
    # Social authentication callback handling
    path('social-auth-complete/<str:backend>/', auth_views.SocialAuthenticationView.as_view(), name='social_complete'),  # Social auth callback
]
