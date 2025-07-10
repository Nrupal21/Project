"""
Management command to populate the database with sample destination data.
"""
import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from destinations.models import Region, Destination, DestinationImage, Season, Attraction

class Command(BaseCommand):
    help = 'Populates the database with sample destination data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample destination data...')
        
        # Create sample regions
        asia, _ = Region.objects.get_or_create(
            name='Asia',
            defaults={
                'description': 'The largest and most populous continent',
                'is_featured': True
            }
        )
        
        europe, _ = Region.objects.get_or_create(
            name='Europe',
            defaults={
                'description': 'A continent located entirely in the Northern Hemisphere',
                'is_featured': True
            }
        )
        
        # Create sample destinations
        destinations_data = [
            {
                'name': 'Bali',
                'region': asia,
                'country': 'Indonesia',
                'description': 'A tropical paradise known for its forested volcanic mountains, iconic rice paddies, beaches and coral reefs.',
                'best_time_to_visit': 'April to October',
                'is_featured': True,
                'is_active': True,
                'seasons': [
                    {'name': 'Dry Season', 'months': 'April - October', 'description': 'Best time to visit with less rainfall and pleasant temperatures.'},
                    {'name': 'Wet Season', 'months': 'November - March', 'description': 'Rainy season with higher humidity but fewer tourists.'}
                ],
                'attractions': [
                    'Ubud Monkey Forest',
                    'Tegallalang Rice Terraces',
                    'Tanah Lot Temple',
                    'Uluwatu Temple',
                    'Mount Batur'
                ],
                'image_urls': [
                    'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80',
                    'https://images.unsplash.com/photo-1505228395891-9a51e7e86bf6?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1930&q=80'
                ]
            },
            {
                'name': 'Paris',
                'region': europe,
                'country': 'France',
                'description': 'The City of Light, famous for its art, fashion, gastronomy and culture.',
                'best_time_to_visit': 'April to June and October to November',
                'is_featured': True,
                'is_active': True,
                'seasons': [
                    {'name': 'Spring', 'months': 'March - May', 'description': 'Mild weather and blooming gardens.'},
                    {'name': 'Summer', 'months': 'June - August', 'description': 'Warm weather but crowded with tourists.'},
                    {'name': 'Autumn', 'months': 'September - November', 'description': 'Pleasant temperatures and fall foliage.'},
                    {'name': 'Winter', 'months': 'December - February', 'description': 'Cold but magical with Christmas markets.'}
                ],
                'attractions': [
                    'Eiffel Tower',
                    'Louvre Museum',
                    'Notre-Dame Cathedral',
                    'Montmartre',
                    'Champs-Élysées'
                ],
                'image_urls': [
                    'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1473&q=80',
                    'https://images.unsplash.com/photo-1499856871958-5b9627545d1a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1520&q=80'
                ]
            },
            {
                'name': 'Kyoto',
                'region': asia,
                'country': 'Japan',
                'description': 'A city of classical Buddhist temples, Shinto shrines, palaces and gardens, many of which are listed collectively by UNESCO as a World Heritage Site.',
                'best_time_to_visit': 'March to May and October to November',
                'is_featured': True,
                'is_active': True,
                'seasons': [
                    {'name': 'Cherry Blossom', 'months': 'March - April', 'description': 'Beautiful cherry blossoms but very crowded.'},
                    {'name': 'Summer', 'months': 'June - August', 'description': 'Hot and humid with occasional rain.'},
                    {'name': 'Autumn', 'months': 'September - November', 'description': 'Pleasant weather and stunning fall foliage.'},
                    {'name': 'Winter', 'months': 'December - February', 'description': 'Cold but with fewer tourists.'}
                ],
                'attractions': [
                    'Fushimi Inari Shrine',
                    'Kinkaku-ji (Golden Pavilion)',
                    'Kiyomizu-dera',
                    'Arashiyama Bamboo Grove',
                    'Gion District'
                ],
                'image_urls': [
                    'https://images.unsplash.com/photo-1492571350019-22de08371fd3?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1453&q=80',
                    'https://images.unsplash.com/photo-1558174234-0a0e7d5c8e12?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80'
                ]
            }
        ]
        
        for dest_data in destinations_data:
            # Remove nested data to create the base destination
            seasons = dest_data.pop('seasons', [])
            attractions = dest_data.pop('attractions', [])
            image_urls = dest_data.pop('image_urls', [])
            
            # Create the destination
            destination, created = Destination.objects.get_or_create(
                name=dest_data['name'],
                defaults=dest_data
            )
            
            if created:
                self.stdout.write(f'Created destination: {destination.name}')
                
                # Add seasons
                for season_data in seasons:
                    Season.objects.create(destination=destination, **season_data)
                
                # Add attractions
                for attraction_name in attractions:
                    Attraction.objects.create(destination=destination, name=attraction_name)
                
                # Add images (just storing URLs as strings for now)
                for i, image_url in enumerate(image_urls, 1):
                    DestinationImage.objects.create(
                        destination=destination,
                        image=image_url,
                        caption=f"{destination.name} - Image {i}",
                        is_feature=(i == 1)
                    )
        
        self.stdout.write(self.style.SUCCESS('Successfully populated destination data!'))
