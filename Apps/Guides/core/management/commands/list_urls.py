from django.core.management.base import BaseCommand
from django.urls import get_resolver

class Command(BaseCommand):
    help = 'List all URLs in the project'

    def handle(self, *args, **options):
        resolver = get_resolver()
        self.print_urls(resolver)

    def print_urls(self, url_patterns, prefix=''):
        for pattern in url_patterns.url_patterns:
            if hasattr(pattern, 'url_patterns'):
                # This is an include
                self.print_urls(pattern, prefix + pattern.pattern._route)
            else:
                # This is a direct URL pattern
                if hasattr(pattern, 'name') and pattern.name:
                    self.stdout.write(f"{prefix}{pattern.pattern} -> {pattern.name}")
                else:
                    self.stdout.write(f"{prefix}{pattern.pattern}")
