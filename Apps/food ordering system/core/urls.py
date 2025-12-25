"""
Core app URLs for the food ordering system.
Contains unified authentication URLs for role-based login system.
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    # Unified Authentication URLs
    path('login/', views.UnifiedLoginView.as_view(), name='login'),
    path('register/', views.UnifiedRegistrationView.as_view(), name='register'),
    path('register/restaurant/', views.RestaurantRegistrationView.as_view(), name='register_restaurant'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Dashboard redirect URLs
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('home/', views.home_redirect, name='home_redirect'),
    
    # Session management API endpoints
    path('session-status/', views.session_status, name='session_status'),
    path('extend-session/', views.extend_session, name='extend_session'),
    
    # Password Reset URLs
    path('password-reset/', views.CustomPasswordResetView.as_view(
        template_name='core/password_reset_form.html',
        email_template_name='core/password_reset_email.txt',
        html_email_template_name='core/password_reset_email.html',
        subject_template_name='core/password_reset_subject.txt',
        success_url='/auth/password-reset/done/'
    ), name='password_reset'),
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='core/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='core/password_reset_confirm.html',
        success_url='/auth/reset/done/',
        post_reset_login=False
    ), name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='core/password_reset_complete.html'
    ), name='password_reset_complete'),
]
