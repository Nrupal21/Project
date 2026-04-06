"""
Management command to inspect guide application data in the database.
"""
from django.core.management.base import BaseCommand
from accounts.models import GuideApplication
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    """
    Command to inspect guide application data in the database.
    
    This command retrieves and displays information about guide applications
    to help with debugging and development.
    """
    help = 'Inspect guide application data in the database'

    def handle(self, *args, **options):
        """
        Execute the command to inspect guide applications.
        
        Retrieves all guide applications and displays their details.
        """
        self.stdout.write(self.style.SUCCESS('Inspecting Guide Applications'))
        
        # Get all guide applications
        applications = GuideApplication.objects.select_related('user', 'reviewed_by').all()
        
        if not applications:
            self.stdout.write(self.style.WARNING('No guide applications found in the database.'))
            return
        
        self.stdout.write(f"Found {applications.count()} guide applications:")
        self.stdout.write("=" * 80)
        
        # Display details for each application
        for app in applications:
            self.stdout.write(f"\nApplication ID: {app.id}")
            self.stdout.write(f"User: {app.user.username} (ID: {app.user.id})")
            self.stdout.write(f"Status: {app.get_status_display()}")
            self.stdout.write(f"Application Date: {app.application_date}")
            self.stdout.write(f"Experience: {app.experience}")
            self.stdout.write(f"Languages: {app.languages}")
            self.stdout.write(f"ID Type: {app.id_type}")
            self.stdout.write(f"ID Verification Status: {app.id_verification_status}")
            self.stdout.write(f"Background Check Status: {app.background_check_status}")
            
            if app.reviewed_by:
                self.stdout.write(f"Reviewed By: {app.reviewed_by.username} (ID: {app.reviewed_by.id})")
            
            if app.review_date:
                self.stdout.write(f"Review Date: {app.review_date}")
                
            if app.rejection_reason:
                self.stdout.write(f"Rejection Reason: {app.rejection_reason}")
            
            self.stdout.write("Notes:")
            if app.notes:
                self.stdout.write(f"{app.notes}")
            else:
                self.stdout.write("No notes")
                
            self.stdout.write("-" * 80)
