"""
URL configuration for the accounts app.

This module defines the URL patterns for user authentication and profile management.
"""
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from django.contrib.auth import views as auth_views
from . import views, template_views
from .otp_views import OTPLoginView, OTPVerifyView, OTPSetupView, OTPManageView
from .mobile_otp_views import MobileOTPLoginView, MobileOTPVerifyView, MobileOTPCompleteView, MobileOTPResendView

# Import OTP URLs
from .urls_otp import urlpatterns as otp_urls

# Define the application namespace
app_name = 'accounts'

# URL patterns for the accounts app
urlpatterns = [
    # Template-based authentication endpoints
    path('login/', template_views.LoginView.as_view(), name='login'),
    path('logout/', template_views.logout_view, name='logout'),
    path('profile/', template_views.ProfileView.as_view(), name='profile'),
    path('register/', template_views.RegisterView.as_view(), name='register'),
    
    # Add alias for django-allauth compatibility
    # This URL pattern is needed because django-allauth expects 'signup' but our app uses 'register'
    path('signup/', template_views.RegisterView.as_view(), name='signup'),
    
    # OTP authentication endpoints
    path('otp/login/', OTPLoginView.as_view(), name='otp_login'),
    path('otp/verify/<uuid:session_key>/', OTPVerifyView.as_view(), name='otp_verify'),
    path('otp/setup/<uuid:session_key>/', OTPSetupView.as_view(), name='otp_setup'),
    path('otp/manage/', OTPManageView.as_view(), name='otp_manage'),
    
    # Mobile OTP authentication endpoints
    path('mobile/login/', MobileOTPLoginView.as_view(), name='mobile_otp_login'),
    path('mobile/verify/', MobileOTPVerifyView.as_view(), name='mobile_otp_verify'),
    path('mobile/complete/', MobileOTPCompleteView.as_view(), name='mobile_otp_complete'),
    path('mobile/resend-otp/', MobileOTPResendView.as_view(), name='mobile_otp_resend'),
    
    # OTP verification URLs
    path('otp/', include((otp_urls, 'otp'), namespace='otp')),
    
    # Password reset URLs
    path('password/change/', 
         template_views.CustomPasswordChangeView.as_view(), 
         name='account_change_password'),
    path('password/change/done/', 
         template_views.CustomPasswordChangeDoneView.as_view(), 
         name='account_change_password_done'),
    path('password/reset/', 
         template_views.CustomPasswordResetView.as_view(), 
         name='account_reset_password'),
    path('password/reset/done/', 
         template_views.CustomPasswordResetDoneView.as_view(), 
         name='account_reset_password_done'),
    path('password/reset/confirm/<uidb64>/<token>/', 
         template_views.CustomPasswordResetConfirmView.as_view(), 
         name='account_reset_password_confirm'),
    path('password/reset/complete/', 
         template_views.CustomPasswordResetCompleteView.as_view(), 
         name='account_reset_password_complete'),
    
    # API authentication endpoints
    path('api/register/', views.RegisterView.as_view(), name='api-register'),
    path('api/login/', views.LoginView.as_view(), name='api-login'),
    path('api/logout/', views.LogoutView.as_view(), name='api-logout'),
    
    # API profile and preferences endpoints
    path('api/profile/', views.UserProfileDetail.as_view(), name='api-profile-detail'),
    path('api/preferences/', views.UserPreferencesView.as_view(), name='api-user-preferences'),
    path('api/change-password/', views.ChangePasswordView.as_view(), name='api-change-password'),
    path('api/users/<int:user_id>/role/', views.UserRoleUpdateView.as_view(), name='api-update-user-role'),
    
    # Token authentication (for API clients)
    path('api/token-auth/', obtain_auth_token, name='api_token_auth'),
]
