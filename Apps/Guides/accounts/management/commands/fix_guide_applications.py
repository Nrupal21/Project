"""
Management command to fix guide application issues in the database.
"""
from django.core.management.base import BaseCommand
from accounts.models import GuideApplication, UserProfile
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    """
    Command to fix guide application issues in the database.
    
    This command reads the guide application table and makes necessary updates
    to ensure data consistency and fix any issues.
    """
    help = 'Fix guide application issues in the database'

    def handle(self, *args, **options):
        """
        Execute the command to fix guide applications.
        
        Reads all guide applications and makes necessary updates.
        """
        self.stdout.write(self.style.SUCCESS('Fixing Guide Application Issues'))
        
        # Get all guide applications
        applications = GuideApplication.objects.select_related('user', 'reviewed_by').all()
        
        if not applications:
            self.stdout.write(self.style.WARNING('No guide applications found in the database.'))
            return
        
        self.stdout.write(f"Found {applications.count()} guide applications")
        updates_made = 0
        
        for app in applications:
            app_updates = 0
            self.stdout.write(f"\nApplication ID: {app.id}")
            self.stdout.write(f"User: {app.user.username} (ID: {app.user.id})")
            self.stdout.write(f"Status: {app.get_status_display()}")
            
            # Fix NULL notes
            if app.notes is None:
                self.stdout.write(self.style.WARNING(f"- Fixing NULL notes for application {app.id}"))
                app.notes = ""
                app_updates += 1
            
            # Check if approved but user profile not updated
            if app.status == 'APPROVED':
                try:
                    profile = UserProfile.objects.get(user=app.user)
                    if not profile.is_guide:
                        self.stdout.write(self.style.WARNING(
                            f"- Fixing user profile for {app.user.username} (setting is_guide=True)"
                        ))
                        profile.is_guide = True
                        profile.guide_since = app.review_date or timezone.now()
                        profile.save(update_fields=['is_guide', 'guide_since'])
                        app_updates += 1
                except UserProfile.DoesNotExist:
                    self.stdout.write(self.style.ERROR(
                        f"- User profile not found for {app.user.username}"
                    ))
            
            # Check for applications with verification status but still in PENDING
            if (app.id_verification_status and app.background_check_status and 
                app.status == 'PENDING'):
                self.stdout.write(self.style.WARNING(
                    f"- Updating status from PENDING to UNDER_REVIEW for application {app.id}"
                ))
                app.status = 'UNDER_REVIEW'
                app_updates += 1
            
            # Save changes if any were made
            if app_updates > 0:
                app.save()
                updates_made += 1
        
        self.stdout.write(self.style.SUCCESS(f"\nUpdated {updates_made} guide applications."))
