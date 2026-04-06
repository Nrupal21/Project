from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import GuideApplication

class Command(BaseCommand):
    help = 'Test guide application email functionality'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Create or get test user
        user, created = User.objects.get_or_create(
            username='test_guide',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'Guide',
                'is_active': True
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created test user'))
        
        # Create test application
        app, created = GuideApplication.objects.get_or_create(
            user=user,
            defaults={
                'bio': 'Test bio',
                'experience': '5 years',
                'specialties': 'Hiking, History',
                'phone_number': '+1234567890',
                'status': 'PENDING'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created test guide application'))
        
        # Test sending email
        from accounts.utils import send_guide_application_confirmation
        
        self.stdout.write('Sending test email...')
        success = send_guide_application_confirmation(user, app)
        
        if success:
            self.stdout.write(self.style.SUCCESS('✅ Email sent successfully!'))
            self.stdout.write('Check the console output above for the email content.')
        else:
            self.stdout.write(self.style.ERROR('❌ Failed to send email'))
        
        return success
