from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings

class Command(BaseCommand):
    help = 'Creates the default site if it does not exist'

    def handle(self, *args, **options):
        domain = 'localhost:8000'
        name = 'localhost'
        
        # Create or update the site with ID=1
        site, created = Site.objects.get_or_create(
            id=settings.SITE_ID,
            defaults={
                'domain': domain,
                'name': name
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Successfully created site {domain}'))
        else:
            site.domain = domain
            site.name = name
            site.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully updated site {domain}'))
