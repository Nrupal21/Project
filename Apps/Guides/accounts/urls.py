"""
URL Configuration for the Accounts application.

This module defines URL patterns for all account-related functionality including:
- User authentication (login, logout, registration)
- Password management (reset, change)
- Email verification flows
- Profile and settings management
- User activity views (favorites, bookings, reviews)
- API endpoints for account-related actions
"""

from django.urls import path, include
from django.views.generic import TemplateView
from . import views
from . import auth_views
from . import views_profile
from . import views_verification
from . import views_registration
from . import admin_urls  # Import admin URLs for role management
from . import guide_views  # Import guide application management views
from django.contrib.auth import views as django_auth_views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs - Handle user login, logout, and registration
    path('login/', auth_views.UserLoginView.as_view(), name='login'),  # Custom login with additional features
    path('logout/', auth_views.UserLogoutView.as_view(), name='logout'),  # Logout with redirect configuration
    
    # User registration
    path('register/', auth_views.UserRegisterView.as_view(), name='register'),  # User registration
    path('register/success/', views_registration.RegistrationSuccessView.as_view(), name='registration_success'),  # Registration success page
    
    # Password management - Reset and recovery workflows
    path('password-change/', auth_views.UserPasswordChangeView.as_view(), name='password_change'),  # Change password form
    path('password-change/done/', auth_views.UserPasswordChangeDoneView.as_view(), name='password_change_done'),  # Password change success
    path('password-reset/', auth_views.UserPasswordResetView.as_view(), name='password_reset'),  # Request password reset
    path('password-reset/done/', auth_views.UserPasswordResetDoneView.as_view(), name='password_reset_done'),  # Reset request sent
    path('reset/<uidb64>/<token>/', auth_views.UserPasswordResetConfirmView.as_view(), name='password_reset_confirm'),  # Reset form
    path('reset/done/', auth_views.UserPasswordResetCompleteView.as_view(), name='password_reset_complete'),  # Reset successful
    
    # Email verification URLs - Handle email verification flows
    path('verify/<uidb64>/<token>/', views_verification.verify_email_view, name='verify_email'),  # Process verification links
    path('verification_required/', views_verification.verification_required_view, name='verification_required'),  # Page shown when verification is needed
    path('api/resend_verification_email/', views_verification.resend_verification_email_view, name='resend_verification_email'),  # AJAX endpoint for resending verification
    
    # Profile URLs - View and edit user profiles
    path('profile/', views.profile_view, name='profile'),  # User's profile dashboard
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),  # Edit basic profile information
    
    # Guide Application URLs
    path('guide/apply/', auth_views.GuideApplicationView.as_view(), name='guide_application'),  # Apply to be a guide
    path('guide/application/submitted/', TemplateView.as_view(template_name='accounts/guide_application_submitted.html'), name='guide_application_submitted'),  # Application submitted confirmation
    
    # Guide Application Management (Admin)
    path('guide/applications/', guide_views.GuideApplicationListView.as_view(), name='guide_applications_list'),  # List all applications (admin)
    path('guide/applications/<int:pk>/', guide_views.GuideApplicationDetailView.as_view(), name='review_guide_application'),  # Review specific application (admin)
    path('guide/applications/<int:pk>/add-note/', guide_views.AddApplicationNoteView.as_view(), name='add_application_note'),  # Add note to application
    path('api/guide-applications/<int:pk>/update-status/', guide_views.UpdateGuideApplicationStatusView.as_view(), name='update_application_status'),  # API endpoint for status updates
    
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
    
    # Profile management URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/preferences/', views.preferences_view, name='preferences'),
    path('profile/favorites/', views.favorites_view, name='favorites'),
    path('profile/activity/', views.activity_view, name='activity'),
    path('profile/bookings/', views.user_bookings_view, name='user_bookings'),
    path('profile/reviews/', views.user_reviews_view, name='user_reviews'),
    
    # View another user's profile by ID
    path('users/<int:user_id>/profile/', views.user_profile_view, name='user_profile'),  # View user profile
    
    # View guide profile
    path('guides/<int:user_id>/profile/', guide_views.guide_profile_view, name='guide_profile'),  # View guide profile
    
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
