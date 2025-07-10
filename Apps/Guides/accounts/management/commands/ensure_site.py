"""
Management command to ensure the default Site object exists in MongoDB.
This is particularly important for Django applications using MongoDB with Djongo.
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings

class Command(BaseCommand):
    help = 'Ensures the default Site object exists in the database'

    def handle(self, *args, **options):
        """
        Main handler for the management command.
        
        This method ensures that a Site object with ID=1 exists in the database.
        If it doesn't exist, it creates one. If it exists but has incorrect
        values, it updates them to match the settings.
        """
        # Get or create the default site
        site, created = Site.objects.get_or_create(
            pk=1,
            defaults={
                'domain': getattr(settings, 'SITE_DOMAIN', '127.0.0.1:8000'),
                'name': getattr(settings, 'SITE_NAME', 'Local Development')
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Created Site: {site.domain} (ID: {site.id})'))
        else:
            # Update existing site if needed
            update_needed = False
            
            # Check if domain needs update
            if hasattr(settings, 'SITE_DOMAIN') and site.domain != settings.SITE_DOMAIN:
                site.domain = settings.SITE_DOMAIN
                update_needed = True
                
            # Check if name needs update
            if hasattr(settings, 'SITE_NAME') and site.name != settings.SITE_NAME:
                site.name = settings.SITE_NAME
                update_needed = True
                
            if update_needed:
                site.save()
                self.stdout.write(self.style.SUCCESS(f'✅ Updated Site: {site.domain} (ID: {site.id})'))
            else:
                self.stdout.write(self.style.SUCCESS(f'✅ Site already exists: {site.domain} (ID: {site.id})'))
        
        # Verify the site is accessible
        try:
            site = Site.objects.get(id=1)
            self.stdout.write(self.style.SUCCESS(f'✅ Verified access to Site: {site.domain}'))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error verifying site: {e}'))
            return False
