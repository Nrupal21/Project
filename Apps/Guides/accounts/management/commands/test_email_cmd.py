from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Test email sending functionality'

    def handle(self, *args, **options):
        """Send a test email."""
        self.stdout.write("Sending test email...")
        
        try:
            # Send test email
            send_mail(
                'Test Email from TravelGuide',
                'This is a test email from the TravelGuide application.',
                'testpy2168@gmail.com',  # System email
                ['nrupal85@gmail.com'],  # User email
                fail_silently=False,
            )
            
            self.stdout.write(
                self.style.SUCCESS('✅ Email sent successfully!')
            )
            self.stdout.write("\nEmail Details:")
            self.stdout.write(f"From: testpy2168@gmail.com")
            self.stdout.write(f"To: nrupal85@gmail.com")
            
            # Print email settings for debugging
            self.stdout.write("\nCurrent Email Settings:")
            self.stdout.write(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
            self.stdout.write(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
            self.stdout.write(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
            
            return True
            
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'❌ Error sending email: {str(e)}')
            )
            return False
