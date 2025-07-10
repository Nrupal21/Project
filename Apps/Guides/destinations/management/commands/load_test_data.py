"""
Management command to load test data for the destinations app.

Usage:
    python manage.py load_test_data
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from destinations.models import Region, Destination, Attraction, Season
from django.core.files import File
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Loads test data for destinations app'

    def handle(self, *args, **options):
        self.stdout.write('Loading test data...')
        
        # Clear existing data (optional, be careful in production)
        # Destination.objects.all().delete()
        # Region.objects.all().delete()
        # Attraction.objects.all().delete()
        
        # Sample regions
        regions_data = [
            {'name': 'North America', 'description': 'United States and Canada'},
            {'name': 'Europe', 'description': 'Historic European destinations'},
            {'name': 'Asia', 'description': 'Exotic Asian locations'},
        ]
        
        # Sample destinations with their attractions
        destinations_data = [
            {
                'name': 'New York City',
                'region': 'North America',
                'short_description': 'The city that never sleeps',
                'description': 'New York City comprises 5 boroughs sitting where the Hudson River meets the Atlantic Ocean.',
                'city': 'New York',
                'country': 'USA',
                'attractions': [
                    {
                        'name': 'Statue of Liberty',
                        'category': 'Landmark',
                        'description': 'A colossal neoclassical sculpture on Liberty Island.'
                    },
                    {
                        'name': 'Central Park',
                        'category': 'Park',
                        'description': 'An urban park in Manhattan.'
                    }
                ]
            },
            {
                'name': 'Paris',
                'region': 'Europe',
                'short_description': 'City of Love',
                'description': 'Paris, France\'s capital, is a major European city and a global center for art, fashion, and culture.',
                'city': 'Paris',
                'country': 'France',
                'attractions': [
                    {
                        'name': 'Eiffel Tower',
                        'category': 'Landmark',
                        'description': 'Wrought-iron lattice tower on the Champ de Mars.'
                    }
                ]
            },
            {
                'name': 'Tokyo',
                'region': 'Asia',
                'short_description': 'Vibrant metropolis',
                'description': 'Japan\'s busy capital, mixes the ultramodern and the traditional.',
                'city': 'Tokyo',
                'country': 'Japan',
                'attractions': [
                    {
                        'name': 'Shibuya Crossing',
                        'category': 'Landmark',
                        'description': 'Famous scramble crossing in front of Shibuya Station.'
                    }
                ]
            },
        ]

        # Create regions
        regions = {}
        for region_data in regions_data:
            region, created = Region.objects.get_or_create(
                name=region_data['name'],
                defaults={
                    'slug': slugify(region_data['name']),
                    'description': region_data['description'],
                    'is_active': True
                }
            )
            regions[region.name] = region
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f"{status} region: {region.name}")

        # Create destinations and their attractions
        for dest_data in destinations_data:
            region_name = dest_data.pop('region')
            attractions_data = dest_data.pop('attractions')
            
            destination, created = Destination.objects.get_or_create(
                name=dest_data['name'],
                defaults={
                    'slug': slugify(dest_data['name']),
                    'region': regions[region_name],
                    'short_description': dest_data['short_description'],
                    'description': dest_data['description'],
                    'city': dest_data['city'],
                    'country': dest_data['country'],
                    'is_featured': True,
                    'is_active': True
                }
            )
            
            # If destination already exists, update is_featured
            if not created:
                destination.is_featured = True
                destination.is_active = True
                destination.save()
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f"{status} destination: {destination.name}")

            # Add attractions
            for attr_data in attractions_data:
                attraction, created = Attraction.objects.get_or_create(
                    name=attr_data['name'],
                    destination=destination,
                    defaults={
                        'category': attr_data['category'],
                        'description': attr_data['description']
                    }
                )
                status = 'Created' if created else 'Already exists'
                self.stdout.write(f"  - {status} attraction: {attraction.name}")

        self.stdout.write(self.style.SUCCESS('Successfully loaded test data!'))
        self.stdout.write('\nTest data summary:')
        self.stdout.write(f"- Regions: {Region.objects.count()}")
        self.stdout.write(f"- Destinations: {Destination.objects.count()}")
        self.stdout.write(f"- Attractions: {Attraction.objects.count()}")
        self.stdout.write('\nYou can now log in to the admin panel to view the test data.')
