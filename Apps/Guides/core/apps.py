from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.conf import settings


def create_default_site(sender, **kwargs):
    from django.contrib.sites.models import Site
    if not Site.objects.filter(id=settings.SITE_ID).exists():
        Site.objects.create(
            id=settings.SITE_ID,
            domain='localhost:8000',
            name='localhost'
        )

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core Application'

    def ready(self):
        post_migrate.connect(create_default_site, sender=self)
