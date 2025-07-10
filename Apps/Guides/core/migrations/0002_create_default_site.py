from django.db import migrations
from django.conf import settings

def create_default_site(apps, schema_editor):
    """Create the default site if it doesn't exist."""
    Site = apps.get_model('sites', 'Site')
    domain = 'localhost:8000'
    name = 'localhost'
    
    # Create or update the site with ID=1
    Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={
            'domain': domain,
            'name': name
        }
    )

class Migration(migrations.Migration):
    """Migration to create the default site."""
    dependencies = [
        ('sites', '0002_alter_domain_unique'),  # This ensures sites app is migrated first
    ]

    operations = [
        migrations.RunPython(create_default_site),
    ]
