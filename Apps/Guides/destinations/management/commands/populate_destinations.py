
"""
Management command to populate the database with sample destinations.

This command creates sample destinations, regions, and destination images
to ensure the home page displays dynamic content properly.
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from destinations.models import Region, Destination, DestinationImage
from django.core.files.base import ContentFile
import random
import os
import logging

# Set up logger
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Command to populate the database with sample destinations.
    
    This command creates a set of sample destinations with regions and images
    to ensure the home page displays dynamic content properly.
    """
    help = 'Populates the database with sample destinations'
    
    def add_arguments(self, parser):
        """
        Add command line arguments.
        
        Args:
            parser: ArgumentParser instance
        """
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of destinations to create (default: 10)'
        )
    
    def handle(self, *args, **options):
        """
        Execute the command to populate destinations.
        
        Args:
            *args: Variable length argument list
            **options: Arbitrary keyword arguments
        """
        count = options['count']
        self.stdout.write(f'Creating {count} sample destinations...')
        
        # Create regions if they don't exist
        regions = self._create_regions()
        
        # Create destinations
        created_count = self._create_destinations(regions, count)
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {created_count} destinations'
        ))
    
    def _create_regions(self):
        """
        Create sample regions if they don't exist.
        
        Returns:
            list: List of Region objects
        """
        region_data = [
            {
                'name': 'Europe',
                'description': 'Explore the diverse cultures and historic landmarks of Europe.',
                'country': 'Various',
                'is_featured': True
            },
            {
                'name': 'Asia',
                'description': 'Discover ancient traditions and modern wonders across Asia.',
                'country': 'Various',
                'is_featured': True
            },
            {
                'name': 'North America',
                'description': 'Experience the natural beauty and vibrant cities of North America.',
                'country': 'Various',
                'is_featured': False
            },
            {
                'name': 'South America',
                'description': 'Journey through the diverse landscapes and rich cultures of South America.',
                'country': 'Various',
                'is_featured': False
            },
            {
                'name': 'Africa',
                'description': 'Explore the wildlife, landscapes, and cultural heritage of Africa.',
                'country': 'Various',
                'is_featured': True
            },
            {
                'name': 'Oceania',
                'description': 'Discover the stunning islands and unique ecosystems of Oceania.',
                'country': 'Various',
                'is_featured': False
            }
        ]
        
        regions = []
        for data in region_data:
            region, created = Region.objects.get_or_create(
                name=data['name'],
                defaults={
                    'slug': slugify(data['name']),
                    'description': data['description'],
                    'country': data['country'],
                    'is_featured': data['is_featured'],
                    'is_active': True
                }
            )
            regions.append(region)
            if created:
                self.stdout.write(f'Created region: {region.name}')
            else:
                self.stdout.write(f'Region already exists: {region.name}')
        
        return regions
    
    def _create_destinations(self, regions, count):
        """
        Create sample destinations.
        
        Args:
            regions: List of Region objects
            count: Number of destinations to create
            
        Returns:
            int: Number of destinations created
        """
        # Sample destination data focused on Alibag and nearby places
        destination_data = [
            {
                'name': 'Alibag Beach',
                'short_description': 'Scenic beach with golden sands',
                'description': 'Alibag Beach is a popular weekend getaway from Mumbai, known for its clean golden sands and serene atmosphere. The beach offers water sports and beautiful sunsets.',
                'city': 'Alibag',
                'country': 'India',
                'latitude': 18.6414,
                'longitude': 72.8722,
                'price': 50.00,
                'rating': 4.3,
                'region_name': 'Asia',
                'is_featured': True
            },
            {
                'name': 'Murud-Janjira Fort',
                'short_description': 'Historic island fort',
                'description': 'Murud-Janjira is a majestic fort located on an oval-shaped rock off the Arabian Sea coast. It\\'s known for its massive walls and 19 rounded bastions still intact.',
                'city': 'Murud',
                'country': 'India',
                'latitude': 18.2989,
                'longitude': 72.9617,
                'price': 30.00,
                'rating': 4.5,
                'region_name': 'Asia',
                'is_featured': True
            },
            {
                'name': 'Kashid Beach',
                'short_description': 'Pristine white sand beach',
                'description': 'Kashid Beach is famous for its white sand and clear blue waters. It\\'s less crowded than other beaches in the region, making it perfect for a peaceful getaway.',
                'city': 'Kashid',
                'country': 'India',
                'latitude': 18.4306,
                'longitude': 72.9008,
                'price': 40.00,
                'rating': 4.4,
                'region_name': 'Asia',
                'is_featured': True
            },
            {
                'name': 'Korlai Fort',
                'short_description': 'Portuguese sea fort',
                'description': 'Korlai Fort is a Portuguese fortification located on an island near Alibag. It offers panoramic views of the Arabian Sea and the surrounding landscape.',
                'city': 'Korlai',
                'country': 'India',
                'latitude': 18.5154,
                'longitude': 72.9112,
                'price': 20.00,
                'rating': 4.2,
                'region_name': 'Asia',
                'is_featured': True
            },
            {
                'name': 'Nagaon Beach',
                'short_description': 'Family-friendly beach destination',
                'description': 'Nagaon Beach is known for its clean shoreline and coconut palms. It\\'s a great spot for swimming and enjoying local seafood delicacies.',
                'city': 'Nagaon',
                'country': 'India',
                'latitude': 18.5522,
                'longitude': 72.9375,
                'price': 35.00,
                'rating': 4.1,
                'region_name': 'Asia',
                'is_featured': True
            },
            {
                'name': 'Kihim Beach',
                'short_description': 'Secluded beach with casuarina trees',
                'description': 'Kihim Beach is known for its casuarina groves, white sand, and clear waters. It\\'s a perfect spot for nature lovers and bird watchers.',
                'city': 'Kihim',
                'country': 'India',
                'latitude': 18.5667,
                'longitude': 72.9000,
                'price': 25.00,
                'rating': 4.3,
                'region_name': 'Asia',
                'is_featured': True
            },
            {
                'name': 'Phansad Wildlife Sanctuary',
                'short_description': 'Biodiversity hotspot',
                'description': 'Phansad Wildlife Sanctuary is home to diverse flora and fauna, including leopards, wild boars, and various bird species. It offers great opportunities for wildlife spotting and nature walks.',
                'city': 'Murud',
                'country': 'India',
                'latitude': 18.4167,
                'longitude': 72.9167,
                'price': 50.00,
                'rating': 4.4,
                'region_name': 'Asia',
                'is_featured': True
            },
            {
                'name': 'Akshi Beach',
                'short_description': 'Tranquil beach experience',
                'description': 'Akshi Beach is a peaceful alternative to the more crowded beaches in the region, offering clean sands and clear waters in a serene environment.',
                'city': 'Akshi',
                'country': 'India',
                'latitude': 18.5833,
                'longitude': 72.9167,
                'price': 20.00,
                'rating': 4.0,
                'region_name': 'Asia',
                'is_featured': False
            },
            {
                'name': 'Revdanda Beach',
                'short_description': 'Historical beach with fort ruins',
                'description': 'Revdanda Beach is known for its historical significance and the nearby Revdanda Fort. The beach offers a mix of history and natural beauty.',
                'city': 'Revdanda',
                'country': 'India',
                'latitude': 18.5500,
                'longitude': 72.9333,
                'price': 25.00,
                'rating': 4.1,
                'region_name': 'Asia',
                'is_featured': True
            },
            {
                'name': 'Kolaba Fort',
                'short_description': 'Seaside fort in Alibag',
                'description': 'Kolaba Fort is a historic fort in Alibag that can be reached by foot during low tide. It offers great views of the Arabian Sea and the surrounding area.',
                'city': 'Alibag',
                'country': 'India',
                'latitude': 18.6333,
                'longitude': 72.8667,
                'price': 15.00,
                'rating': 4.2,
                'region_name': 'Asia',
                'is_featured': True
            },
            {
                'name': 'Mandwa Beach',
                'short_description': 'Gateway to Alibag by sea',
                'description': 'Mandwa Beach is a popular entry point to Alibag via ferry from Mumbai. The beach is known for its clean sands and water sports activities.',
                'city': 'Mandwa',
                'country': 'India',
                'latitude': 18.8000,
                'longitude': 72.8833,
                'price': 30.00,
                'rating': 4.0,
                'region_name': 'Asia',
                'is_featured': False
            },
            {
                'name': 'Sagargad Fort',
                'short_description': 'Hill fort with panoramic views',
                'description': 'Sagargad Fort offers breathtaking views of the Arabian Sea and the surrounding region. It\\'s a great spot for trekking and photography.',
                'city': 'Sagargad',
                'country': 'India',
                'latitude': 18.5333,
                'longitude': 72.9333,
                'price': 20.00,
                'rating': 4.3,
                'region_name': 'Asia',
                'is_featured': True
            }
        ]
        
        # Limit to requested count
        destination_data = destination_data[:count]
        
        # Create destinations
        created_count = 0
        for data in destination_data:
            # Find the region
            region_name = data.pop('region_name')
            region = next((r for r in regions if r.name == region_name), None)
            
            if not region:
                self.stdout.write(self.style.WARNING(
                    f'Region {region_name} not found, skipping destination {data["name"]}'
                ))
                continue
            
            # Create or update destination
            dest, created = Destination.objects.get_or_create(
                name=data['name'],
                defaults={
                    'region': region,
                    'slug': slugify(data['name']),
                    'short_description': data['short_description'],
                    'description': data['description'],
                    'city': data['city'],
                    'country': data['country'],
                    'latitude': data['latitude'],
                    'longitude': data['longitude'],
                    'price': data['price'],
                    'rating': data['rating'],
                    'is_active': True,
                    'is_featured': data['is_featured']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created destination: {dest.name}')
                
                # Create a placeholder image for the destination
                self._create_placeholder_image(dest)
            else:
                self.stdout.write(f'Destination already exists: {dest.name}')
        
        return created_count
    
    def _create_placeholder_image(self, destination):
        """
        Create a placeholder image for a destination.
        
        Args:
            destination: Destination object
        """
        # Check if destination already has images
        if destination.images.exists():
            return
        
        try:
            # Create a primary image
            image = DestinationImage(
                destination=destination,
                caption=f'Main image for {destination.name}',
                is_primary=True
            )
            
            # Use a placeholder image
            image_path = os.path.join('static', 'img', 'placeholder.jpg')
            if not os.path.exists(image_path):
                self.stdout.write(self.style.WARNING(
                    f'Placeholder image not found at {image_path}, skipping image creation'
                ))
                return
            
            with open(image_path, 'rb') as f:
                image_content = f.read()
                image_name = f'{slugify(destination.name)}_main.jpg'
                image.image.save(image_name, ContentFile(image_content), save=True)
            
            self.stdout.write(f'Created image for {destination.name}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Error creating image for {destination.name}: {e}'
            ))
