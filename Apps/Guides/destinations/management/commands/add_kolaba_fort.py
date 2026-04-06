"""
Management command to add Kolaba Fort as a destination.
"""
import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from destinations.models import Region, Destination, DestinationImage
from django.core.files import File
from django.conf import settings

class Command(BaseCommand):
    help = 'Adds Kolaba Fort as a destination to the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to add Kolaba Fort destination...'))
        
        # Create or get Konkan region
        region, created = Region.objects.get_or_create(
            name='Konkan',
            defaults={
                'slug': 'konkan',
                'description': 'Coastal region of western India known for its beaches, forts, and Konkani cuisine',
                'country': 'India',
                'is_active': True,
                'is_featured': True,
                'created_at': timezone.now(),
                'updated_at': timezone.now()
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Konkan region'))
        else:
            self.stdout.write(self.style.SUCCESS('Konkan region already exists'))
        
        # Create Kolaba Fort destination
        kolaba_fort, created = Destination.objects.get_or_create(
            name='Kolaba Fort',
            defaults={
                'slug': 'kolaba-fort',
                'description': (
                    'Kolaba Fort, also known as Kulaba Fort or Alibag Fort, is a majestic 17th-century sea fort located approximately 1.5 kilometers off the coast of Alibag in the Raigad District of Maharashtra, India. '
                    'This historic fortification was strategically built by the visionary Maratha ruler Chhatrapati Shivaji Maharaj and subsequently fortified by Sambhaji. '
                    'It played a pivotal role as a primary naval station and shipbuilding center for the formidable Maratha empire, defending the coastline from colonial powers.'
                ),
                'short_description': (
                    'Kolaba Fort, a 17th-century sea fort off Alibag, served as a key Maratha naval station. '
                    'Accessible by foot at low tide, it offers ocean views, ancient cannons, temples, and a glimpse into maritime history.'
                ),
                'latitude': 18.634400,
                'longitude': 72.864200,
                'city': 'Alibag',
                'country': 'India',
                'is_featured': True,
                'is_active': True,
                'price': 0.00,  # Free entry
                'rating': 4.5,
                'region': region,
                'created_at': timezone.now(),
                'updated_at': timezone.now()
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Kolaba Fort destination'))
            
            # Add destination images (placeholder paths - you'll need to add actual images to your media directory)
            image_data = [
                {
                    'path': 'destinations/kolaba-fort-aerial.jpg',
                    'caption': 'Aerial view of Kolaba Fort surrounded by the Arabian Sea',
                    'is_primary': True
                },
                {
                    'path': 'destinations/kolaba-fort-interior.jpg',
                    'caption': 'Historic stone walls and freshwater well within Kolaba Fort',
                    'is_primary': False
                },
                {
                    'path': 'destinations/kolaba-fort-cannon.jpg',
                    'caption': 'Centuries-old cannon and animal carvings at Kolaba Fort',
                    'is_primary': False
                }
            ]
            
            for img in image_data:
                # This is a placeholder - in a real scenario, you would need to handle file uploads
                # and create proper File objects for the images
                DestinationImage.objects.create(
                    destination=kolaba_fort,
                    image=img['path'],  # This should be a File object in a real scenario
                    caption=img['caption'],
                    is_primary=img['is_primary'],
                    created_at=timezone.now()
                )
            
            self.stdout.write(self.style.SUCCESS('Added images for Kolaba Fort'))
        else:
            self.stdout.write(self.style.SUCCESS('Kolaba Fort already exists in the database'))
        
        self.stdout.write(self.style.SUCCESS('Successfully completed adding Kolaba Fort destination'))
