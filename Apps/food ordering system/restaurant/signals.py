"""
Django signals for restaurant app.
Handles automatic logging of manager authentication events.
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from .models import ManagerLoginLog


@receiver(user_logged_in)
def log_manager_login(sender, request, user, **kwargs):
    """
    Signal handler for user login events.
    
    Automatically creates a login log entry when a staff user logs in.
    This provides comprehensive audit tracking for manager authentication.
    
    Args:
        sender: Signal sender (not used)
        request: HttpRequest object containing request metadata
        user: User object that logged in
        **kwargs: Additional signal arguments (not used)
    """
    # Only log staff user logins
    if user.is_staff:
        try:
            ManagerLoginLog.log_login(user, request)
        except Exception as e:
            # Log the error but don't break the login process
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log manager login for {user.username}: {str(e)}")


@receiver(user_logged_out)
def log_manager_logout(sender, request, user, **kwargs):
    """
    Signal handler for user logout events.
    
    Automatically ends active login sessions when a staff user logs out.
    This completes the audit trail by marking session end times.
    
    Args:
        sender: Signal sender (not used)
        request: HttpRequest object (may not contain user info in all cases)
        user: User object that logged out (may be None for anonymous logout)
        **kwargs: Additional signal arguments (not used)
    """
    # Only log staff user logouts
    if user and user.is_staff:
        try:
            # Find and end the most recent active session for this user
            active_sessions = ManagerLoginLog.objects.filter(
                user=user,
                is_active_session=True
            ).order_by('-login_time')
            
            if active_sessions.exists():
                latest_session = active_sessions.first()
                latest_session.end_session()
        except Exception as e:
            # Log the error but don't break the logout process
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log manager logout for {user.username}: {str(e)}")


def cleanup_expired_sessions():
    """
    Utility function to clean up expired sessions.
    
    This function should be called periodically (e.g., via cron job)
    to mark very old active sessions as expired. Sessions older than
    24 hours are considered expired.
    
    Returns:
        int: Number of sessions that were marked as expired
    """
    from datetime import timedelta
    
    # Find sessions older than 24 hours that are still marked as active
    cutoff_time = timezone.now() - timedelta(hours=24)
    expired_sessions = ManagerLoginLog.objects.filter(
        login_time__lt=cutoff_time,
        is_active_session=True,
        logout_time__isnull=True
    )
    
    count = 0
    for session in expired_sessions:
        session.end_session()
        count += 1
    
    return count
