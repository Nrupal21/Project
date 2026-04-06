"""
URL patterns for security-related views.

This module defines URL patterns for user authentication, registration,
role management, and other security-related functionality.
"""

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'security'

urlpatterns = [
    # Authentication URLs
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Two-factor authentication routes
    path('2fa/setup/', views.TwoFactorSetupView.as_view(), name='twofa_setup'),
    path('2fa/confirm/', views.TwoFactorConfirmView.as_view(), name='twofa_confirm'),
    path('2fa/backup-codes/', views.TwoFactorBackupCodesView.as_view(), name='twofa_backup_codes'),
    path('2fa/manage/', views.TwoFactorManageView.as_view(), name='twofa_manage'),
    path('2fa/verify/', views.TwoFactorVerifyView.as_view(), name='twofa_verify'),
    path('2fa/disable/', views.disable_two_factor, name='twofa_disable'),
    path('2fa/regenerate-backup-codes/', views.regenerate_backup_codes, name='twofa_regenerate_backup'),
]
