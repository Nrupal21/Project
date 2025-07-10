"""
Management command to populate the database with sample tour data.
"""
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from destinations.models import Region, Destination
from tours.models import (
    TourCategory, Tour, TourImage, 
    TourItinerary, TourInclusion, TourReview
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with sample tour data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample tour data...')
        
        # Create sample categories
        categories = [
            {'name': 'Adventure', 'icon': 'fas fa-hiking'},
            {'name': 'Cultural', 'icon': 'fas fa-landmark'},
            {'name': 'Beach', 'icon': 'fas fa-umbrella-beach'},
            {'name': 'Wildlife', 'icon': 'fas fa-paw'},
            {'name': 'Honeymoon', 'icon': 'fas fa-heart'},
        ]
        
        created_categories = []
        for cat_data in categories:
            category, created = TourCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'icon': cat_data['icon']}
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
            created_categories.append(category)
        
        # Get or create a region and destination
        region, _ = Region.objects.get_or_create(
            name='Asia',
            defaults={
                'description': 'The largest and most populous continent',
                'image': 'regions/asia.jpg'
            }
        )
        
        destination, _ = Destination.objects.get_or_create(
            name='Bali',
            defaults={
                'region': region,
                'country': 'Indonesia',
                'description': 'A tropical paradise known for its forested volcanic mountains, iconic rice paddies, beaches and coral reefs.',
                'best_time_to_visit': 'April to October',
                'is_featured': True,
                'is_active': True
            }
        )
        
        # Create sample tours
        tours_data = [
            {
                'title': 'Bali Adventure Tour',
                'description': 'Experience the best of Bali with this action-packed adventure tour.',
                'duration_days': 7,
                'duration_nights': 6,
                'price': 1299.99,
                'discount_price': 1099.99,
                'max_group_size': 15,
                'category': created_categories[0],  # Adventure
                'destination': destination,
                'is_featured': True,
                'is_active': True,
                'highlights': [
                    'Trekking Mount Batur at sunrise',
                    'White water rafting on Ayung River',
                    'Snorkeling at Menjangan Island',
                    'Visiting Ubud Monkey Forest'
                ],
                'itinerary': [
                    {'day': 1, 'title': 'Arrival in Bali', 'description': 'Airport pickup and transfer to Ubud. Free time to explore.'},
                    {'day': 2, 'title': 'Mount Batur Sunrise Trek', 'description': 'Early morning trek to Mount Batur for sunrise views.'},
                    {'day': 3, 'title': 'Ayung River Rafting', 'description': 'Exciting white water rafting adventure.'},
                    {'day': 4, 'title': 'Ubud Exploration', 'description': 'Visit Ubud Monkey Forest, Tegalalang Rice Terraces, and local markets.'},
                    {'day': 5, 'title': 'Menjangan Island', 'description': 'Full day snorkeling trip to Menjangan Island.'},
                    {'day': 6, 'title': 'Free Day', 'description': 'Free day to relax or explore on your own.'},
                    {'day': 7, 'title': 'Departure', 'description': 'Transfer to the airport for departure.'},
                ],
                'inclusions': [
                    '6 nights accommodation in 4-star hotels',
                    'Daily breakfast',
                    'All activities mentioned in the itinerary',
                    'English speaking guide',
                    'All transportation during the tour',
                    'Entrance fees to all attractions',
                ],
                'exclusions': [
                    'International flights',
                    'Travel insurance',
                    'Meals not mentioned',
                    'Personal expenses',
                ]
            },
            {
                'title': 'Bali Cultural Experience',
                'description': 'Immerse yourself in the rich culture and traditions of Bali.',
                'duration_days': 5,
                'duration_nights': 4,
                'price': 899.99,
                'category': created_categories[1],  # Cultural
                'destination': destination,
                'is_featured': True,
                'is_active': True,
                'highlights': [
                    'Traditional Balinese dance performance',
                    'Temple visits including Tanah Lot and Uluwatu',
                    'Balinese cooking class',
                    'Visit to local artisan villages'
                ],
                'itinerary': [
                    {'day': 1, 'title': 'Arrival in Bali', 'description': 'Airport pickup and transfer to hotel. Evening traditional dance performance.'},
                    {'day': 2, 'title': 'Temples Tour', 'description': 'Visit Tanah Lot, Uluwatu, and other important temples.'},
                    {'day': 3, 'title': 'Cultural Workshops', 'description': 'Balinese cooking class and batik making workshop.'},
                    {'day': 4, 'title': 'Artisan Villages', 'description': 'Visit Ubud art market and traditional artisan villages.'},
                    {'day': 5, 'title': 'Departure', 'description': 'Transfer to the airport for departure.'},
                ],
                'inclusions': [
                    '4 nights accommodation in 4-star hotels',
                    'Daily breakfast',
                    'All activities mentioned in the itinerary',
                    'English speaking guide',
                    'All transportation during the tour',
                    'Entrance fees to all attractions',
                ],
                'exclusions': [
                    'International flights',
                    'Travel insurance',
                    'Meals not mentioned',
                    'Personal expenses',
                ]
            },
        ]
        
        # Create tours
        for tour_data in tours_data:
            # Remove nested data to create the base tour
            highlights = tour_data.pop('highlights', [])
            itinerary = tour_data.pop('itinerary', [])
            inclusions = tour_data.pop('inclusions', [])
            exclusions = tour_data.pop('exclusions', [])
            
            # Create the tour
            tour = Tour.objects.create(**tour_data)
            
            # Add highlights as tags
            for highlight in highlights:
                tour.tags.add(highlight)
            
            # Create itinerary items
            for day in itinerary:
                TourItinerary.objects.create(tour=tour, **day)
            
            # Create inclusions and exclusions
            for inclusion in inclusions:
                TourInclusion.objects.create(tour=tour, description=inclusion, is_included=True)
            
            for exclusion in exclusions:
                TourInclusion.objects.create(tour=tour, description=exclusion, is_included=False)
            
            self.stdout.write(f'Created tour: {tour.title}')
            
            # Create a sample review
            user, _ = User.objects.get_or_create(
                username='testuser',
                defaults={'email': 'test@example.com', 'password': 'testpass123'}
            )
            
            TourReview.objects.create(
                tour=tour,
                user=user,
                rating=random.randint(4, 5),
                comment='Amazing experience! Highly recommended.',
                is_approved=True
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully populated tour data!'))
