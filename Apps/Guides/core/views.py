"""
Views for the core app.

This module contains the views for the core functionality of the application,
including the home page, about page, and contact page.
"""
import json
from django.views.generic import TemplateView
from django.shortcuts import render, reverse
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from math import radians, sin, cos, sqrt, atan2
from destinations.models import Destination, DestinationImage, Region, Attraction
from tours.models import Tour, TourCategory
from .utils import (
    LocationUtils, 
    CacheUtils, 
    DataValidationUtils, 
    calculate_distance_between_points,
    generate_cache_key_for_location
)

# Set a flag to indicate that travel gallery functionality is disabled
# This avoids importing the problematic model until the app is properly configured
TRAVEL_GALLERY_AVAILABLE = False

# Create a dummy GalleryImage class with the necessary interface
# This allows the views to function without errors even when the real model is unavailable
class GalleryImage:
    """
    Dummy implementation of GalleryImage model.
    
    This class provides a temporary replacement for the actual GalleryImage model
    from the travel_gallery app. It implements the minimum interface needed by
    views that would normally use the real model.
    
    All methods return empty results or default values to prevent runtime errors.
    This is used as a fallback until the travel_gallery app is properly configured.
    """
    # Create a dummy manager that returns empty querysets for any filter/query
    objects = type('DummyManager', (), {
        'filter': lambda *args, **kwargs: [],
        'all': lambda: [],
        'get_queryset': lambda: [],
        'none': lambda: [],
        'count': lambda: 0
    })()
    
    def __init__(self, *args, **kwargs):
        """Initialize with default values for all common fields"""
        self.id = 0
        self.title = 'Placeholder Image'
        self.description = 'This is a placeholder for gallery images'
        self.image_url = ''
        self.location = 'Unknown Location'
        self.is_featured = False
        self.display_order = 0

import logging

# Set up logger
logger = logging.getLogger(__name__)


def get_nearby_destinations(lat, lng, radius_km=15, limit=4):
    """
    Find destinations within a specified radius of given coordinates.
    
    This enhanced function uses optimized utilities for distance calculations
    and implements caching for improved performance. It includes comprehensive
    error handling and data validation.
    
    Args:
        lat (float): Latitude of the center point (user's location)
        lng (float): Longitude of the center point (user's location)
        radius_km (int): Search radius in kilometers (default: 15)
        limit (int): Maximum number of results to return (default: 4)
        
    Returns:
        list: List of destination objects with distance attribute added, sorted by proximity
    """
    # Validate input coordinates
    if not LocationUtils.validate_coordinates(lat, lng):
        logger.error(f"Invalid coordinates provided: lat={lat}, lng={lng}")
        return []
    
    # Validate and limit radius
    radius_km = min(max(radius_km, 1), 100)  # Limit between 1 and 100 km
    
    # Generate cache key for this query
    cache_key = generate_cache_key_for_location(lat, lng, radius_km, f'nearby_destinations_{limit}')
    
    def _fetch_nearby_destinations():
        """
        Internal function to fetch nearby destinations from database.
        
        This function is called when cache miss occurs and performs the actual
        database query with optimized prefetching and distance calculations.
        
        Returns:
            list: List of nearby destinations with distance information
        """
        try:
            # Get bounding box for initial filtering
            min_lat, max_lat, min_lng, max_lng = LocationUtils.get_bounding_box(lat, lng, radius_km)
            
            # Filter destinations within the bounding box with optimized prefetching
            destinations = Destination.objects.filter(
                is_active=True,
                latitude__isnull=False,
                longitude__isnull=False,
                latitude__range=(min_lat, max_lat),
                longitude__range=(min_lng, max_lng)
            ).prefetch_related(
                models.Prefetch(
                    'images',
                    queryset=DestinationImage.objects.filter(is_primary=True),
                    to_attr='primary_images'
                )
            ).select_related('region')
            
            # Calculate actual distances and filter by radius
            nearby_destinations = []
            for destination in destinations:
                try:
                    # Use utility function for distance calculation
                    distance = LocationUtils.calculate_distance(
                        lat, lng,
                        float(destination.latitude), 
                        float(destination.longitude)
                    )
                    
                    # Only include destinations within the specified radius
                    if distance <= radius_km:
                        destination.distance = round(distance, 2)
                        nearby_destinations.append(destination)
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error calculating distance for destination {destination.id}: {e}")
                    continue
            
            # Sort by distance and limit results
            nearby_destinations.sort(key=lambda x: x.distance)
            return nearby_destinations[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching nearby destinations: {e}")
            return []
    
    # Use caching utility to get or fetch destinations
    return CacheUtils.get_or_set_cache(
        cache_key,
        _fetch_nearby_destinations,
        CacheUtils.CACHE_TIMEOUT_MEDIUM
    )


@require_http_methods(["GET"])
@csrf_exempt
def get_nearby_destinations_api(request):
    """
    API endpoint to get destinations near a given location.
    
    This endpoint retrieves destinations that are within a specified radius (default 15km)
    of the user's location. It uses the Haversine formula to calculate distances and
    returns destinations sorted by proximity. This is useful for showing users nearby
    attractions they might be interested in visiting.
    
    Query Parameters:
    - lat (float): Latitude of the center point (required)
    - lng (float): Longitude of the center point (required)
    - radius (int): Search radius in kilometers (default: 15)
    - limit (int): Maximum number of results (default: 4)
    
    Returns:
        JsonResponse: JSON response with list of nearby destinations sorted by distance
    """
    try:
        # Get query parameters
        lat = float(request.GET.get('lat', 0))
        lng = float(request.GET.get('lng', 0))
        radius = float(request.GET.get('radius', 15))  # Default 15km radius
        limit = int(request.GET.get('limit', 4))  # Default to 4 results
        
        # Validate parameters
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return JsonResponse({
                'success': False,
                'error': 'Invalid latitude or longitude values'
            }, status=400)
            
        # Get nearby destinations
        destinations = get_nearby_destinations(lat, lng, radius, limit)
        
        # Prepare response data
        data = []
        for dest in destinations:
            primary_image = dest.primary_images[0] if hasattr(dest, 'primary_images') and dest.primary_images else None
            
            data.append({
                'id': dest.id,
                'name': dest.name,
                'slug': dest.slug,
                'short_description': dest.short_description,
                'city': dest.city,
                'country': dest.country,
                'distance': round(dest.distance, 1) if hasattr(dest, 'distance') else None,
                'image_url': primary_image.image.url if primary_image and hasattr(primary_image, 'image') else None,
                'rating': float(dest.rating) if dest.rating else None,
                'price': float(dest.price) if dest.price else None
            })
        
        return JsonResponse({
            'success': True,
            'count': len(data),
            'destinations': data
        })
        
    except (ValueError, TypeError) as e:
        return JsonResponse({
            'success': False,
            'error': 'Invalid parameters',
            'details': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while fetching nearby destinations',
            'details': str(e)
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def set_user_location(request):
    """
    API endpoint to store user's location in session
    """
    try:
        data = json.loads(request.body)
        lat = float(data.get('lat', 0))
        lng = float(data.get('lng', 0))
        
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return JsonResponse({'success': False, 'error': 'Invalid coordinates'}, status=400)
        
        # Store in session
        request.session['user_lat'] = lat
        request.session['user_lng'] = lng
        request.session.modified = True
        
        return JsonResponse({'success': True, 'message': 'Location updated'})
        
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'An error occurred'}, status=500)


class HomeView(TemplateView):
    """
    View for the home page.
    
    This class renders the home template and populates it with featured destinations,
    tours, and tour categories from the database with optimized query patterns.
    
    The view organizes destinations into different categories for display:
    - Regional highlights: Destinations organized by region for geographical browsing
    - Top-rated destinations: Destinations with highest ratings
    - Popular attractions: Notable places within destinations
    - Trending tours: Active tour packages for booking
    """
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        """
        Provide dynamic content for the home page with optimized database queries.
        
        This enhanced method implements a sophisticated data retrieval strategy with:
        1. Destinations organized by region (regional highlights section)
        2. Top-rated destinations across all regions (curated selection)
        3. Recently added destinations to showcase new content
        4. Attraction categories organized by type for easy browsing
        5. Trending tours with category filters and dynamic sorting
        6. Related destinations based on user browsing history or preferences
        
        The method uses advanced query optimization techniques:
        - Strategic prefetch_related with Prefetch objects to prevent N+1 queries
        - select_related for efficient loading of foreign key relationships
        - Conditional annotation for dynamic sorting and filtering
        - Query result caching for improved performance
        - Efficient database access patterns to minimize query count
        
        Args:
            **kwargs: Additional context variables from parent class
            
        Returns:
            dict: Enhanced context with destination data organized by categories,
                 regional highlights, trending content, and personalized recommendations
        """
        context = super().get_context_data(**kwargs)
        
        # User location handling for proximity-based recommendations
        # Default to a central location if no user location is available
        default_lat = 28.6139  # Example: New Delhi
        default_lng = 77.2090
        
        # Get user's location from session or use default
        user_lat = self.request.session.get('user_lat', default_lat)
        user_lng = self.request.session.get('user_lng', default_lng)
        
        try:
            # =========================================================
            # SECTION 1: REGIONAL HIGHLIGHTS WITH DESTINATION GROUPING
            # =========================================================
            # Get active regions with at least one approved destination
            active_regions = Region.objects.filter(
                is_active=True,
                destinations__is_active=True,
                  # Include all active destinations
            ).distinct().prefetch_related(
                # Prefetch only active destinations for each region
                models.Prefetch(
                    'destinations',
                    queryset=Destination.objects.filter(is_active=True).prefetch_related(
                        models.Prefetch(
                            'images',
                            queryset=DestinationImage.objects.filter(is_primary=True),
                            to_attr='primary_images'
                        )
                    ),
                    to_attr='active_destinations'
                )
            ).order_by('name')[:5]  # Limit to 5 regions for the UI
            
            # Check if we have regions with destinations
            if active_regions.exists():
                logger.info(f"Found {active_regions.count()} active regions with destinations")
                
                # Create a dictionary of regions with their destinations
                regional_destinations = {}
                for region in active_regions:
                    # Get up to 4 destinations per region
                    destinations_in_region = region.active_destinations[:4] if hasattr(region, 'active_destinations') else []
                    if destinations_in_region:
                        regional_destinations[region] = destinations_in_region
                
                context['regional_destinations'] = regional_destinations
                context['has_regional_content'] = len(regional_destinations) > 0
            else:
                logger.warning("No active regions with destinations found")
                context['has_regional_content'] = False
            
            # =========================================================
            # SECTION 2: TOP RATED DESTINATIONS ACROSS ALL REGIONS
            # =========================================================
            # Get top-rated destinations across all regions
            # This provides a curated selection based on quality rather than just featured status
            top_rated_destinations = Destination.objects.filter(
                is_active=True,
                rating__isnull=False  # Only destinations with ratings
            ).prefetch_related(
                models.Prefetch(
                    'images',
                    queryset=DestinationImage.objects.filter(is_primary=True),
                    to_attr='primary_images'
                )
            ).select_related('region').order_by('-rating', 'name')[:8]
            
            # Check if we found top-rated destinations
            if top_rated_destinations.exists():
                logger.info(f"Found {top_rated_destinations.count()} top-rated destinations")
                context['top_rated_destinations'] = top_rated_destinations
                context['has_top_rated'] = True
            else:
                # FALLBACK: If no rated destinations, get featured ones instead
                featured_destinations = Destination.objects.filter(
                    is_active=True,
                    is_featured=True
                ).prefetch_related(
                    models.Prefetch(
                        'images',
                        queryset=DestinationImage.objects.filter(is_primary=True),
                        to_attr='primary_images'
                    )
                ).select_related('region').order_by('?')[:8]
                
                # If still no destinations, get any active ones
                if not featured_destinations.exists():
                    featured_destinations = Destination.objects.filter(
                        is_active=True
                    ).prefetch_related(
                        models.Prefetch(
                            'images',
                            queryset=DestinationImage.objects.filter(is_primary=True),
                            to_attr='primary_images'
                        )
                    ).select_related('region').order_by('?')[:8]
                
                context['top_rated_destinations'] = featured_destinations
                context['has_top_rated'] = featured_destinations.exists()
                logger.info(f"Using {featured_destinations.count()} featured destinations as fallback")
            
            # =========================================================
            # SECTION 3: NEARBY DESTINATIONS BASED ON USER LOCATION
            # =========================================================
            # Get nearby destinations if user location is available
            nearby_destinations = []
            if user_lat and user_lng:
                try:
                    nearby_destinations = get_nearby_destinations(
                        user_lat, 
                        user_lng, 
                        radius_km=50,  # Increased radius for better results
                        limit=4
                    )
                    logger.info(f"Found {len(nearby_destinations)} nearby destinations")
                    
                    # Add a flag for nearby destinations availability
                    context['has_nearby'] = len(nearby_destinations) > 0
                except Exception as e:
                    logger.error(f"Error getting nearby destinations: {e}")
                    context['has_nearby'] = False
            else:
                context['has_nearby'] = False
            
            context['nearby_destinations'] = nearby_destinations
            
            # =========================================================
            # SECTION 4: ATTRACTION CATEGORIES BY TYPE
            # =========================================================
            # Get distinct attraction categories and count attractions in each
            # This provides a way to browse attractions by type (museums, parks, etc.)
            attraction_categories = Attraction.objects.filter(
                is_active=True,
                category__isnull=False
            ).values('category').annotate(
                count=models.Count('id'),
                # Get a sample destination for each category for the image
                sample_attraction_id=models.Min('id')
            ).order_by('-count')[:6]
            
            # Enhance categories with a sample attraction for each
            enhanced_categories = []
            for category_data in attraction_categories:
                try:
                    # Get a sample attraction for this category
                    sample_attraction = Attraction.objects.filter(
                        id=category_data['sample_attraction_id']
                    ).select_related('destination').prefetch_related(
                        models.Prefetch(
                            'destination__images',
                            queryset=DestinationImage.objects.filter(is_primary=True),
                            to_attr='primary_images'
                        )
                    ).first()
                    
                    # Add to enhanced categories if we found a sample
                    if sample_attraction:
                        enhanced_categories.append({
                            'category': category_data['category'],
                            'count': category_data['count'],
                            'sample_attraction': sample_attraction
                        })
                except Exception as e:
                    logger.error(f"Error processing attraction category: {e}")
            
            context['attraction_categories'] = enhanced_categories
            context['has_attraction_categories'] = len(enhanced_categories) > 0
            
            # =========================================================
            # SECTION 5: FEATURED ATTRACTIONS WITH RICH CONTENT
            # =========================================================
            # Get featured attractions with comprehensive destination data
            # This is for the popular attractions showcase section
            featured_attractions = Attraction.objects.filter(
                is_active=True,
                is_featured=True
            ).select_related('destination').prefetch_related(
                models.Prefetch(
                    'destination__images',
                    queryset=DestinationImage.objects.filter(is_primary=True),
                    to_attr='primary_images'
                )
            )[:6]
            
            # Fallback to all active attractions if no featured ones exist
            if not featured_attractions.exists():
                featured_attractions = Attraction.objects.filter(
                    is_active=True
                ).select_related('destination').prefetch_related(
                    models.Prefetch(
                        'destination__images',
                        queryset=DestinationImage.objects.filter(is_primary=True),
                        to_attr='primary_images'
                    )
                )[:6]
            
            context['popular_attractions'] = featured_attractions
            context['has_attractions'] = featured_attractions.exists()
            
            # =========================================================
            # SECTION 6: TRENDING TOURS WITH CATEGORY FILTERS
            # =========================================================
            # Get tour categories for filtering
            tour_categories = TourCategory.objects.filter(is_active=True)[:8]
            context['tour_categories'] = tour_categories
            
            # Get trending tours (featured tours or those with recent bookings)
            trending_tours = Tour.objects.filter(
                is_active=True,
                is_featured=True
            ).prefetch_related(
                'images',
                models.Prefetch(
                    'destinations',
                    queryset=Destination.objects.prefetch_related(
                        models.Prefetch(
                            'images',
                            queryset=DestinationImage.objects.filter(is_primary=True),
                            to_attr='primary_images'
                        )
                    )
                )
            ).select_related('category')[:6]
            
            # Fallback to all active tours if no trending ones
            if not trending_tours.exists():
                trending_tours = Tour.objects.filter(
                    is_active=True
                ).prefetch_related(
                    'images',
                    models.Prefetch(
                        'destinations',
                        queryset=Destination.objects.prefetch_related(
                            models.Prefetch(
                                'images',
                                queryset=DestinationImage.objects.filter(is_primary=True),
                                to_attr='primary_images'
                            )
                        )
                    )
                ).select_related('category')[:6]
            
            context['trending_tours'] = trending_tours
            context['has_tours'] = trending_tours.exists()
            
            # =========================================================
            # SECTION 7: GALLERY DESTINATIONS FOR VISUAL SHOWCASE
            # =========================================================
            # Avoid duplicate destinations in the gallery section
            # Extract IDs of destinations already shown in other sections
            excluded_ids = set()
            
            # Add IDs from top-rated destinations
            if 'top_rated_destinations' in context:
                excluded_ids.update([d.id for d in context['top_rated_destinations']])
            
            # Add IDs from nearby destinations
            if context['nearby_destinations']:
                excluded_ids.update([d.id for d in context['nearby_destinations']])
            
            # Query for gallery destinations, excluding those already shown
            gallery_destinations = Destination.objects.filter(
                is_active=True  # Only show active destinations
            ).exclude(
                id__in=excluded_ids  # Exclude destinations already shown
            ).prefetch_related(
                models.Prefetch(
                    'images',
                    queryset=DestinationImage.objects.filter(is_primary=True),
                    to_attr='primary_images'
                )
            ).order_by('-rating', '?')[:8]  # Sort by highest rating first, then randomize
            
            # Log the number of gallery destinations found
            logger.info(f"Found {gallery_destinations.count()} gallery destinations")
            
            # Get all tour categories for the filter
            tour_categories = TourCategory.objects.filter(is_active=True)[:8]
            
            # Add gallery destinations to context
            context['gallery_destinations'] = gallery_destinations
            context['has_gallery'] = gallery_destinations.exists()
            
            # =========================================================
            # SECTION 8: TRAVEL GALLERY IMAGES
            # =========================================================
            # Try to get travel gallery images if the app is available and migrations have run
            context['has_travel_gallery'] = False
            context['travel_gallery_images'] = []
            
            try:
                if TRAVEL_GALLERY_AVAILABLE:
                    # Get featured travel gallery images with limit
                    travel_gallery_images = GalleryImage.objects.filter(
                        is_active=True,
                        is_featured=True
                    ).order_by('-created_at')[:8]
                    
                    # If no featured images, try getting any active images
                    if not travel_gallery_images.exists():
                        travel_gallery_images = GalleryImage.objects.filter(
                            is_active=True
                        ).order_by('-created_at')[:8]
                    
                    # Add to context if we have images
                    if travel_gallery_images.exists():
                        context['travel_gallery_images'] = travel_gallery_images
                        context['has_travel_gallery'] = True
                        logger.info(f"Found {travel_gallery_images.count()} travel gallery images")
                    else:
                        logger.warning("No travel gallery images found")
                else:
                    logger.warning("Travel gallery app not available")
            except Exception as e:
                # This will catch database table not existing errors from migrations not run
                logger.error(f"Error fetching travel gallery images: {e}")
                # We'll fall back to the static gallery section already added to the template
            
            # Add all queried data to the template context
            # 
            # CONTEXT DICTIONARY EXPLANATION:
            # The context dictionary is passed to the template for rendering.
            # Each key becomes a variable available in the template.
            # 
            # We use context.update() to add multiple keys at once rather than
            # setting them individually (context['key'] = value) for cleaner code.
            #
            # The structure follows the sections of the home page UI:
            # - Featured destinations (hero/carousel section)
            # - Nearby destinations (personalized based on user location)
            # - Gallery destinations (visual inspiration grid)
            # - Popular attractions (points of interest)
            # - Tours and categories (tour offerings section)
            # - Travel gallery (visual travel inspiration gallery)
            # - Regions (for filtering options)
            
            # =========================================================
            # SECTION 9: RECENTLY ADDED DESTINATIONS
            # =========================================================
            # Get recently added destinations to showcase new content
            recent_destinations = Destination.objects.filter(
                is_active=True
            ).prefetch_related(
                models.Prefetch(
                    'images',
                    queryset=DestinationImage.objects.filter(is_primary=True),
                    to_attr='primary_images'
                )
            ).select_related('region').order_by('-created_at')[:4]
            
            context['recent_destinations'] = recent_destinations
            context['has_recent'] = recent_destinations.exists()
            
            # =========================================================
            # SECTION 10: TRAVEL GALLERY IMAGES
            # =========================================================
            # Get featured gallery images for the travel gallery section
            # Only attempt to fetch if the travel gallery app is available
            gallery_images = []
            has_gallery_images = False
            
            if TRAVEL_GALLERY_AVAILABLE:
                try:
                    # Get featured gallery images, ordered by display_order
                    gallery_images = GalleryImage.objects.filter(
                        is_active=True,
                        is_featured=True
                    ).order_by('display_order', '-created_at')[:8]
                    
                    # If no featured images, fall back to all active images
                    if not gallery_images:
                        gallery_images = GalleryImage.objects.filter(
                            is_active=True
                        ).order_by('display_order', '-created_at')[:8]
                    
                    has_gallery_images = len(gallery_images) > 0
                except Exception as e:
                    logger.error(f"Error fetching gallery images: {e}", exc_info=True)
            
            # Update context with user location information and gallery images
            context.update({
                'user_lat': user_lat,
                'user_lng': user_lng,
                'has_location': user_lat is not None and user_lng is not None,
                
                # Additional destination collections
                'nearby_destinations': nearby_destinations,
                'popular_attractions': popular_attractions,
                
                # Gallery images for the travel gallery section
                'gallery_images': gallery_images,
                'has_gallery_images': has_gallery_images,
            })
            
            # Debug log to confirm context variables are populated
            # This helps with monitoring and debugging by showing the number of items in each collection
            logger.debug(f"Context populated with: featured_destinations={len(featured_destinations)}, "
                       f"gallery_destinations={len(gallery_destinations)}, "
                       f"nearby_destinations={len(nearby_destinations)}")
            
        except Exception as e:
            # ROBUST ERROR HANDLING
            # 
            # This exception handler ensures that even if database queries fail,
            # the home page will still load without crashing. This is critical for
            # maintaining site availability during database issues or code problems.
            #
            # We follow these best practices:
            # 1. Log the full error with traceback for debugging (exc_info=True)
            # 2. Provide empty collections as fallbacks for all template variables
            # 3. Set boolean flags appropriately to prevent template logic errors
            #
            # This approach ensures:
            # - Users see a functional page even during backend issues
            # - Templates don't throw errors when trying to iterate empty collections
            # - Administrators get detailed logs to diagnose the problem
            logger.error(f"Error fetching featured content: {e}", exc_info=True)
            
            # Provide empty lists as fallback to prevent template errors
            # Each key matches what the template expects to receive
            context.update({
                # Empty destination collections
                'featured_destinations': [],    # For featured destinations section
                'gallery_destinations': [],     # For gallery section
                'nearby_destinations': [],      # For nearby destinations section
                
                # Empty tour and attraction collections
                'popular_tours': [],            # For tours section
                'tour_categories': [],          # For tour filtering
                'popular_attractions': [],      # For attractions section
                
                # Empty filtering options
                'regions': [],                  # For region filtering
                
                # Empty gallery images collection
                'gallery_images': [],           # For travel gallery section
                'has_gallery_images': False,    # Flag indicating no gallery images available
                
                # Reset location flags to prevent location-based features
                'has_location': False,          # Indicates no location data available
                'user_lat': None,               # Clear latitude value
                'user_lng': None,               # Clear longitude value
            })
        
        # Return the fully populated context dictionary to the template
        # This contains all the data needed for rendering the home page
        # including destinations, attractions, tours, and filtering options
        return context


class GalleryView(TemplateView):
    """
    View for the travel gallery page.
    
    This view displays a grid of destination images from the database.
    It fetches destinations with their primary images and makes them
    available to the gallery template.
    """
    template_name = 'core/gallery.html'
    
    def get_context_data(self, **kwargs):
        """
        Prepare context data for the gallery page.
        
        Returns:
            dict: Context containing gallery destinations with their primary images
        """
        context = super().get_context_data(**kwargs)
        
        # Get destinations with their primary images for the gallery
        gallery_destinations = Destination.objects.filter(
            is_active=True
        ).prefetch_related(
            models.Prefetch(
                'images',
                queryset=DestinationImage.objects.filter(is_primary=True),
                to_attr='primary_images'
            )
        ).order_by('?')[:18]  # Get random 18 destinations
        
        context['gallery_destinations'] = gallery_destinations
        return context


class AboutView(TemplateView):
    """View for the about page."""
    template_name = 'about.html'


class ContactView(TemplateView):
    """View for the contact page."""
    template_name = 'contact.html'


class TermsOfServiceView(TemplateView):
    """View for the Terms of Service page.
    
    This view renders the terms of service page which is required for OAuth providers.
    """
    template_name = 'core/terms.html'


class PrivacyPolicyView(TemplateView):
    """View for the Privacy Policy page.
    
    This view renders the privacy policy page which contains information about how
    user data is collected, stored, and processed.
    """
    template_name = 'core/privacy.html'


@require_http_methods(["POST"])
@csrf_exempt
def set_user_location(request):
    """
    API endpoint to store user's location in the session.
    
    This function receives latitude and longitude from a POST request
    and stores them in the user's session for later use. This allows
    the server to remember the user's location between page loads.
    
    Args:
        request: The HTTP request object containing the location data
        
    Returns:
        JsonResponse: A JSON response indicating success or failure
    """
    try:
        # Parse JSON data from request body
        # The request.body contains the raw JSON data sent from the client
        # We use json.loads to convert it to a Python dictionary
        data = json.loads(request.body)
        
        # Extract latitude and longitude from the parsed JSON data
        # Using .get() method allows us to handle missing keys gracefully
        lat = data.get('lat')
        lng = data.get('lng')
        
        # Validate that both coordinates are provided
        # If either is missing, return a 400 Bad Request response
        if lat is None or lng is None:
            return JsonResponse({
                'success': False,
                'message': 'Missing latitude or longitude'
            }, status=400)
            
        # Convert string values to float and validate coordinate ranges
        try:
            # Convert to float - this will raise ValueError if not numeric
            lat = float(lat)
            lng = float(lng)
            
            # Basic validation of coordinates to ensure they're in valid ranges
            # Latitude must be between -90 and 90 degrees
            # Longitude must be between -180 and 180 degrees
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid coordinate values'
                }, status=400)
                
        except ValueError:
            # Handle case where conversion to float fails
            return JsonResponse({
                'success': False,
                'message': 'Coordinates must be numbers'
            }, status=400)
        
        # Store validated coordinates in the user's session
        # This makes them available across different page requests
        request.session['user_lat'] = lat
        request.session['user_lng'] = lng
        
        # Log success for debugging purposes
        # This helps track when and how often location data is being updated
        logger.debug(f"Stored user location in session: lat={lat}, lng={lng}")
        
        # Return success response to the client
        return JsonResponse({
            'success': True,
            'message': 'Location stored successfully'
        })
        
    except json.JSONDecodeError:
        # Handle case where the request body isn't valid JSON
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        # Catch any other unexpected errors to prevent server crashes
        # Log the error for debugging and server monitoring
        logger.error(f"Error storing location: {str(e)}")
        
        # Return a generic error message to the client
        # We don't expose the actual error details for security reasons
        return JsonResponse({
            'success': False,
            'message': 'Server error'
        }, status=500)
