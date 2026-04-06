"""
Management command to add Alibag and nearby destinations to the database.

This command populates the database with destinations in the Alibag area of Maharashtra, India.
It creates a 'Konkan' region if it doesn't exist, and adds multiple destinations within that region,
including beaches and historic forts. Each destination includes detailed information such as 
geographical coordinates, ratings, prices, and descriptions.

The command also adds sample images for the destinations to provide a complete visual experience
on the website. All destinations are marked as featured and active by default.

Usage:
    python manage.py add_alibag_destinations

No additional arguments are required.
"""
# Django management command framework
from django.core.management.base import BaseCommand

# Import destination-related models from our app
from destinations.models import Destination, Region, DestinationImage

# Django file handling utilities for image creation
from django.core.files.base import ContentFile

# Standard library for file path operations
import os

class Command(BaseCommand):
    """
    Django management command to populate the database with Alibag destinations.
    
    This command extends Django's BaseCommand to provide functionality for adding
    sample destinations in the Alibag region to the database. It's useful for:
    - Initial data seeding for development or testing
    - Demonstrating the destination features of the application
    - Providing sample content for the home page featured destinations section
    
    The command handles creating both the parent region and multiple destinations
    within that region, complete with geographical data and ratings.
    """
    
    # Short help text displayed when running 'python manage.py help add_alibag_destinations'
    help = 'Add Alibag and nearby places to the database'
    
    def handle(self, *args, **options):
        """
        Main command execution method.
        
        This method performs the following operations:
        1. Creates or retrieves the Konkan region
        2. Defines destination data including location details, ratings, and descriptions
        3. Creates destination records in the database if they don't already exist
        4. Outputs success messages for each created destination
        
        Args:
            *args: Variable length argument list
            **options: Arbitrary keyword arguments from command line
            
        Returns:
            None. Results are printed to stdout.
        """
        # Create or get the region
        # Using get_or_create to avoid duplicates - this either retrieves an existing region
        # or creates a new one if it doesn't exist
        region, created = Region.objects.get_or_create(
            name='Konkan',  # Look up by name as the primary identifier
            defaults={
                # These values are only used when creating a new region
                'slug': 'konkan',  # URL-friendly version of the name
                'description': 'The Konkan region of Maharashtra, known for its beautiful beaches and historic forts.',
                'country': 'India',  # Country where the region is located
                'is_active': True,   # Make the region available on the site
                'is_featured': True  # Show in featured regions sections
            }
        )
        
        # Provide feedback about whether we created a new region or used an existing one
        if created:
            # Success message with green styling for a newly created region
            self.stdout.write(self.style.SUCCESS(f'Created region: {region.name}'))
        else:
            # Informational message for using an existing region
            self.stdout.write(f'Using existing region: {region.name}')

        # List of destinations to add
        # Each destination is defined as a dictionary with all necessary fields
        # All destinations are in the Konkan region of Maharashtra, India
        # Fields include:
        # - name: The display name of the destination
        # - slug: URL-friendly version of the name (used in destination detail URLs)
        # - short_description: Brief tagline for the destination
        # - description: Detailed information about the destination
        # - city: The city where the destination is located
        # - country: The country where the destination is located
        # - latitude/longitude: Geographical coordinates for mapping
        # - price: Starting price point for visiting (in USD)
        # - rating: Average rating on a 5-point scale
        # - is_featured: Whether to show this destination in featured sections
        destinations = [
            {
                # Kolaba Fort destination data
                # Historic sea fort off the coast of Alibag
                'name': 'Kolaba Fort',
                'slug': 'kolaba-fort',
                'short_description': 'Kolaba Fort, a 17th-century sea fort off Alibag, served as a key Maratha naval station. Accessible by foot at low tide, it offers ocean views, ancient cannons, temples, and a glimpse into maritime history.',
                'description': 'Kolaba Fort, also known as Kulaba Fort or Alibag Fort, is a majestic 17th-century sea fort located approximately 1.5 kilometers off the coast of Alibag in the Raigad District of Maharashtra, India. This historic fortification was strategically built by the visionary Maratha ruler Chhatrapati Shivaji Maharaj and subsequently fortified by Sambhaji. It played a pivotal role as a primary naval station and shipbuilding center for the formidable Maratha empire, defending the coastline from colonial powers.',
                'city': 'Alibag',
                'country': 'India',
                'latitude': 18.6344,
                'longitude': 72.8642,
                'price': 25.00,  # Entry fee in USD
                'rating': 4.6,   # Average visitor rating
                'is_featured': True
            },
            {
                # Alibag Beach destination data
                # Main beach near Alibag town center
                'name': 'Alibag Beach',
                'slug': 'alibag-beach',
                'short_description': 'Alibag Beach, near Alibag city center, is known for its calm waters, offering boat rides to Kolaba Fort and a lively atmosphere, popular for evening walks and scenic views.',
                'description': 'Alibag Beach is a popular coastal destination located near the heart of Alibag city in the Raigad District of Maharashtra, India. Known for its calm and shallow waters, it offers picturesque views, particularly of the historic Kolaba Fort situated a short distance into the Arabian Sea. The beach is a favorite spot for evening strolls, and boat rides are available to access the fort during high tide. Its lively atmosphere, coupled with the availability of local snacks and activities, makes it a significant tourist attraction in the Konkan region.',
                'city': 'Alibag',
                'country': 'India',
                'latitude': 18.6199,
                'longitude': 72.8826,
                'price': 0.00,    # Free access
                'rating': 4.3,    # Average visitor rating
                'is_featured': True
            },
            {
                # Varsoli Beach destination data
                # Quieter beach near Alibag
                'name': 'Varsoli Beach',
                'slug': 'varsoli-beach',
                'short_description': 'Varsoli Beach, located 3-4 km from Alibag city, is a quiet and less crowded beach ideal for swimming and relaxation, offering a serene environment.',
                'description': 'Varsoli Beach is a serene and less crowded coastal stretch situated approximately 3-4 kilometers from the bustling Alibag city center in the Raigad District of Maharashtra, India. Unlike its more popular counterpart, Alibag Beach, Varsoli offers a tranquil environment with calm waters, making it an ideal spot for swimming, relaxing, and enjoying peaceful walks along the shore. It is known for its clean sands and a quiet ambiance, attracting visitors seeking a more laid-back beach experience away from the crowds.',
                'city': 'Alibag',
                'country': 'India',
                'latitude': 18.6316,
                'longitude': 72.8805,
                'price': 0.00,    # Free access
                'rating': 4.2,    # Average visitor rating
                'is_featured': True
            },
            {
                # Khanderi Island Beach destination data
                # Secluded beach on a historic island
                'name': 'Khanderi Island Beach',
                'slug': 'khanderi-island-beach',
                'short_description': 'Khanderi Island Beach, located on Khanderi Island about 7 km from Alibag, offers a quiet beach experience and the opportunity to explore the historic Khanderi Fort.',
                'description': 'Khanderi Island Beach is a secluded and tranquil beach located on Khanderi Island, approximately 7 kilometers off the coast of Alibag in the Raigad District of Maharashtra, India. This island destination is ideal for visitors seeking a peaceful escape and the opportunity to explore the historic Khanderi Fort. The beach offers calm waters and a serene environment, making it perfect for relaxation and enjoying the natural beauty of the Arabian Sea.',
                'city': 'Alibag',
                'country': 'India',
                'latitude': 18.5803,
                'longitude': 72.9734,
                'price': 30.00,   # Boat ride and entry fee in USD
                'rating': 4.4,    # Average visitor rating
                'is_featured': False
            },
            {
                # Kankeshwar Temple destination data
                # Hill temple with panoramic views
                'name': 'Kankeshwar Temple',
                'slug': 'kankeshwar-temple',
                'short_description': 'Hill top Shiva temple in forested surroundings, reached via ~700 stone steps, offering scenic sea and forest views along with ancient Pushkarni tank.',
                'description': 'Kankeshwar Temple is a serene 8th century Shiva shrine perched atop a 1,200 ft hill near Mapgaon, about 12 km from Alibag. The hike involves roughly 650–700 stone steps through dense forest, passing landmarks like Devachi Payari and Gaymandi pond. Built in Hoysala/Hemadpanti style by Govind Rangdas, the temple features a Pushkarni tank, multiple shrines, and unique architecture. The lush forest is home to raptors, snakes, and wildlife, adding to the spiritual and natural experience. From the hilltop, visitors enjoy panoramic views of the Arabian Sea and nearby forts, making this a peaceful pilgrimage and trek.',
                'city': 'Mapgaon',
                'country': 'India',
                'latitude': 18.652,
                'longitude': 72.912,
                'price': 0.00,    # Free entry
                'rating': 4.7,    # Average visitor rating
                'is_featured': True
            }
        ]

        # Define destination images data
        # Each destination has a list of images with captions and primary status
        # This allows us to create rich visual content for each destination
        destination_images = {
            # Images for Kolaba Fort
            'kolaba-fort': [
                {
                    'image_name': 'kolaba-fort-aerial.jpg',
                    'caption': 'Aerial view of Kolaba Fort surrounded by the Arabian Sea',
                    'is_primary': True,
                    'order': 1
                },
                {
                    'image_name': 'kolaba-fort-interior.jpg',
                    'caption': 'Historic stone walls and freshwater well within Kolaba Fort',
                    'is_primary': False,
                    'order': 2
                },
                {
                    'image_name': 'kolaba-fort-cannon.jpg',
                    'caption': 'Centuries-old cannon and animal carvings at Kolaba Fort',
                    'is_primary': False,
                    'order': 3
                }
            ],
            # Images for Alibag Beach
            'alibag-beach': [
                {
                    'image_name': 'alibag-beach-sunset.jpg',
                    'caption': 'Panoramic view of Alibag Beach at sunset with Kolaba Fort in the distance',
                    'is_primary': True,
                    'order': 1
                },
                {
                    'image_name': 'alibag-beach-boats.jpg',
                    'caption': 'Boats lined up on Alibag Beach with people enjoying the view',
                    'is_primary': False,
                    'order': 2
                },
                {
                    'image_name': 'alibag-beach-walk.jpg',
                    'caption': 'Visitors enjoying an evening walk on the sandy shores of Alibag Beach',
                    'is_primary': False,
                    'order': 3
                }
            ],
            # Images for Varsoli Beach
            'varsoli-beach': [
                {
                    'image_name': 'varsoli-beach-calm.jpg',
                    'caption': 'Panoramic view of Varsoli Beach with its calm and clear waters',
                    'is_primary': True,
                    'order': 1
                },
                {
                    'image_name': 'varsoli-beach-relax.jpg',
                    'caption': 'Visitors relaxing and enjoying the quiet environment of Varsoli Beach',
                    'is_primary': False,
                    'order': 2
                },
                {
                    'image_name': 'varsoli-beach-boats.jpg',
                    'caption': 'Colorful boats anchored at the tranquil Varsoli Beach during sunset',
                    'is_primary': False,
                    'order': 3
                }
            ],
            # Images for Khanderi Island Beach
            'khanderi-island-beach': [
                {
                    'image_name': 'khanderi-beach-fort-view.jpg',
                    'caption': 'View of Khanderi Island Beach with the historic Khanderi Fort in the background',
                    'is_primary': True,
                    'order': 1
                },
                {
                    'image_name': 'khanderi-beach-shore.jpg',
                    'caption': 'Serene waters and sandy shores of Khanderi Island Beach',
                    'is_primary': False,
                    'order': 2
                },
                {
                    'image_name': 'khanderi-fort-exterior.jpg',
                    'caption': 'Exterior view of the historic Khanderi Fort on Khanderi Island',
                    'is_primary': False,
                    'order': 3
                }
            ],
            # Images for Kankeshwar Temple
            'kankeshwar-temple': [
                {
                    'image_name': 'kankeshwar-temple-exterior.jpg',
                    'caption': 'Golden shikhara of Kankeshwar Temple among green foliage',
                    'is_primary': True,
                    'order': 1
                },
                {
                    'image_name': 'kankeshwar-temple-tank.jpg',
                    'caption': 'Stone lined Pushkarni water tank at hilltop temple',
                    'is_primary': False,
                    'order': 2
                },
                {
                    'image_name': 'kankeshwar-temple-steps.jpg',
                    'caption': 'Stone steps winding through forest to temple',
                    'is_primary': False,
                    'order': 3
                }
            ]
        }
        
        # Add each destination
        # Iterate through the destination data and create records in the database
        for dest_data in destinations:
            # Check if destination already exists by slug to avoid duplicates
            # Slug is used as it's a unique identifier for destinations
            if Destination.objects.filter(slug=dest_data['slug']).exists():
                self.stdout.write(f"Destination {dest_data['name']} already exists, skipping...")
                continue

            # Create the destination record in the database
            # We use dictionary unpacking to pass all fields from the destination data
            # The region field is set separately as it's a foreign key relationship
            # Any 'images' key is excluded as it would be handled separately if present
            dest = Destination.objects.create(
                region=region,  # Associate with the Konkan region created/retrieved above
                **{k: v for k, v in dest_data.items() if k != 'images'}
            )
            
            # Output success message with green styling
            self.stdout.write(self.style.SUCCESS(f"Created destination: {dest.name}"))
            
            # Add images for this destination if available
            # Images are created as DestinationImage objects linked to the destination
            if dest.slug in destination_images:
                # Loop through each image defined for this destination
                for img_data in destination_images[dest.slug]:
                    # Create a placeholder image file
                    # In a real scenario, you would use actual image files
                    # Here we're creating empty placeholder files for demonstration
                    image_path = f"destinations/{img_data['image_name']}"
                    
                    # Check if this image already exists to avoid duplicates
                    if DestinationImage.objects.filter(image=image_path).exists():
                        self.stdout.write(f"Image {image_path} already exists, skipping...")
                        continue
                    
                    # Create the image record with a placeholder file
                    # In production, you would use real image files
                    try:
                        # Create the destination image record
                        # Make sure field names match the model definition
                        image = DestinationImage.objects.create(
                            destination=dest,
                            image=image_path,  # Path where the image would be stored
                            caption=img_data['caption'],  # Caption for the image
                            is_primary=img_data['is_primary']  # Whether this is the main image
                        )
                        self.stdout.write(f"Added image: {image_path} to {dest.name}")
                    except Exception as e:
                        # Log any errors during image creation
                        self.stdout.write(self.style.ERROR(f"Error adding image {image_path}: {e}"))

        # Final success message indicating all destinations were processed
        self.stdout.write(self.style.SUCCESS('Successfully added Alibag and nearby places to the database!'))
        self.stdout.write('Note: Image paths were created as placeholders. In a production environment, you would need to upload actual image files to these paths.')

