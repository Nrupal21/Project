"""
Template utility functions and context processors for the TravelGuide application.

This module provides shared template utilities, context processors, and helper functions
that enhance template functionality across all apps. It ensures consistent data availability
and formatting in templates while following the user's preference for comprehensive comments.

Key Features:
- Global context processors for common data
- Template helper functions for formatting and calculations
- Consistent data structures for template consumption
- Performance optimizations for template rendering
- Tailwind CSS utility classes and helpers
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Avg, Q
from django.contrib.sites.shortcuts import get_current_site

# Configure logger for this module
logger = logging.getLogger(__name__)


def global_context_processor(request):
    """
    Global context processor that provides common data to all templates.
    
    This context processor adds frequently used data to the template context
    across all views, ensuring consistent availability of site-wide information
    without requiring each view to explicitly provide this data.
    
    Args:
        request: HTTP request object
        
    Returns:
        dict: Context dictionary with global template variables
        
    Context Variables Added:
        - site_name: Name of the current site
        - current_year: Current year for copyright notices
        - debug_mode: Whether Django is in debug mode
        - user_location: User's stored location from session
        - navigation_data: Common navigation menu data
        - site_stats: Basic site statistics for display
    """
    try:
        # Get current site information
        current_site = get_current_site(request)
        
        # Get user location from session if available
        user_location = None
        if 'user_latitude' in request.session and 'user_longitude' in request.session:
            user_location = {
                'latitude': request.session.get('user_latitude'),
                'longitude': request.session.get('user_longitude'),
                'timestamp': request.session.get('location_timestamp')
            }
        
        # Build context dictionary
        context = {
            'site_name': getattr(settings, 'SITE_NAME', current_site.name),
            'current_year': timezone.now().year,
            'debug_mode': settings.DEBUG,
            'user_location': user_location,
            'navigation_data': get_navigation_data(request),
            'site_stats': get_cached_site_stats(),
            'tailwind_config': get_tailwind_config()
        }
        
        logger.debug("Global context processor executed successfully")
        return context
        
    except Exception as e:
        logger.error(f"Error in global context processor: {e}")
        # Return minimal context on error to prevent template failures
        return {
            'site_name': 'TravelGuide',
            'current_year': timezone.now().year,
            'debug_mode': settings.DEBUG
        }


def get_navigation_data(request):
    """
    Generate navigation menu data for consistent site navigation.
    
    This function creates a structured navigation menu that can be used
    across all templates, ensuring consistent navigation experience and
    proper highlighting of active sections.
    
    Args:
        request: HTTP request object for determining active sections
        
    Returns:
        dict: Navigation data structure with menu items and metadata
        
    Navigation Structure:
        - main_menu: Primary navigation items
        - user_menu: User-specific menu items (when authenticated)
        - mobile_menu: Mobile-optimized navigation structure
        - breadcrumbs: Contextual breadcrumb navigation
    """
    try:
        # Get current path for active menu highlighting
        current_path = request.path
        
        # Define main navigation menu items
        main_menu = [
            {
                'name': 'Home',
                'url': '/',
                'icon': 'fas fa-home',
                'active': current_path == '/',
                'description': 'Return to homepage'
            },
            {
                'name': 'Destinations',
                'url': '/destinations/',
                'icon': 'fas fa-map-marker-alt',
                'active': current_path.startswith('/destinations/'),
                'description': 'Explore travel destinations'
            },
            {
                'name': 'Tours',
                'url': '/tours/',
                'icon': 'fas fa-route',
                'active': current_path.startswith('/tours/'),
                'description': 'Browse tour packages'
            },
            {
                'name': 'Gallery',
                'url': '/gallery/',
                'icon': 'fas fa-images',
                'active': current_path.startswith('/gallery/'),
                'description': 'View photo gallery'
            }
        ]
        
        # Define user-specific menu items
        user_menu = []
        if request.user.is_authenticated:
            user_menu = [
                {
                    'name': 'My Bookings',
                    'url': '/bookings/',
                    'icon': 'fas fa-calendar-check',
                    'description': 'View your bookings'
                },
                {
                    'name': 'My Reviews',
                    'url': '/reviews/my-reviews/',
                    'icon': 'fas fa-star',
                    'description': 'Manage your reviews'
                },
                {
                    'name': 'Profile',
                    'url': '/accounts/profile/',
                    'icon': 'fas fa-user',
                    'description': 'Edit your profile'
                }
            ]
        
        # Generate breadcrumbs based on current path
        breadcrumbs = generate_breadcrumbs(current_path)
        
        return {
            'main_menu': main_menu,
            'user_menu': user_menu,
            'mobile_menu': main_menu + user_menu,  # Combined for mobile
            'breadcrumbs': breadcrumbs,
            'has_active_item': any(item['active'] for item in main_menu)
        }
        
    except Exception as e:
        logger.error(f"Error generating navigation data: {e}")
        return {'main_menu': [], 'user_menu': [], 'breadcrumbs': []}


def generate_breadcrumbs(current_path):
    """
    Generate breadcrumb navigation based on the current URL path.
    
    This function creates contextual breadcrumb navigation that helps users
    understand their current location within the site hierarchy.
    
    Args:
        current_path (str): Current URL path
        
    Returns:
        list: List of breadcrumb items with names and URLs
        
    Breadcrumb Structure:
        Each breadcrumb item contains:
        - name: Display name for the breadcrumb
        - url: URL for the breadcrumb link
        - active: Whether this is the current page
    """
    try:
        breadcrumbs = [{'name': 'Home', 'url': '/', 'active': False}]
        
        # Parse path segments
        path_segments = [segment for segment in current_path.split('/') if segment]
        
        if not path_segments:
            breadcrumbs[0]['active'] = True
            return breadcrumbs
        
        # Build breadcrumbs based on path segments
        current_url = ''
        for i, segment in enumerate(path_segments):
            current_url += f'/{segment}'
            is_last = (i == len(path_segments) - 1)
            
            # Convert segment to readable name
            readable_name = segment.replace('-', ' ').replace('_', ' ').title()
            
            # Handle special cases for better naming
            if segment == 'destinations':
                readable_name = 'Destinations'
            elif segment == 'tours':
                readable_name = 'Tours'
            elif segment == 'gallery':
                readable_name = 'Gallery'
            elif segment == 'accounts':
                readable_name = 'Account'
            elif segment == 'bookings':
                readable_name = 'Bookings'
            elif segment == 'reviews':
                readable_name = 'Reviews'
            
            breadcrumbs.append({
                'name': readable_name,
                'url': current_url + '/' if not is_last else current_url,
                'active': is_last
            })
        
        return breadcrumbs
        
    except Exception as e:
        logger.error(f"Error generating breadcrumbs: {e}")
        return [{'name': 'Home', 'url': '/', 'active': True}]


def get_cached_site_stats():
    """
    Retrieve cached site statistics for display in templates.
    
    This function provides basic site statistics that are commonly displayed
    in footers, dashboards, or promotional sections. Results are cached to
    improve performance and reduce database load.
    
    Returns:
        dict: Site statistics including counts and metrics
        
    Statistics Included:
        - total_destinations: Number of active destinations
        - total_tours: Number of active tours
        - total_reviews: Number of approved reviews
        - total_users: Number of registered users
        - featured_destinations: Number of featured destinations
        - recent_activity: Recent activity indicators
    """
    cache_key = 'site_stats_global'
    cached_stats = cache.get(cache_key)
    
    if cached_stats is not None:
        logger.debug("Site stats retrieved from cache")
        return cached_stats
    
    try:
        # Import models here to avoid circular imports
        from destinations.models import Destination
        from tours.models import Tour
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Calculate statistics
        stats = {
            'total_destinations': Destination.objects.filter(is_active=True).count(),
            'total_tours': Tour.objects.filter(is_active=True).count(),
            'featured_destinations': Destination.objects.filter(is_active=True, is_featured=True).count(),
            'total_users': User.objects.filter(is_active=True).count(),
            'last_updated': timezone.now().isoformat()
        }
        
        # Try to get review count if reviews app is available
        try:
            from reviews.models import Review
            stats['total_reviews'] = Review.objects.filter(is_approved=True).count()
        except ImportError:
            stats['total_reviews'] = 0
        
        # Cache for 1 hour
        cache.set(cache_key, stats, 3600)
        logger.debug("Site stats calculated and cached")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error calculating site stats: {e}")
        return {
            'total_destinations': 0,
            'total_tours': 0,
            'total_reviews': 0,
            'total_users': 0,
            'featured_destinations': 0,
            'last_updated': timezone.now().isoformat()
        }


def get_tailwind_config():
    """
    Provide Tailwind CSS configuration and utility classes for templates.
    
    This function returns commonly used Tailwind CSS classes and configurations
    that ensure consistent styling across templates, following the user's
    preference for Tailwind CSS usage.
    
    Returns:
        dict: Tailwind CSS configuration and utility classes
        
    Configuration Includes:
        - color_palette: Consistent color scheme (indigo/violet theme)
        - component_classes: Pre-defined component class combinations
        - responsive_classes: Responsive design utility classes
        - animation_classes: Animation and transition classes
    """
    return {
        'color_palette': {
            'primary': 'indigo-600',
            'primary_hover': 'indigo-700',
            'secondary': 'violet-600',
            'secondary_hover': 'violet-700',
            'accent': 'blue-500',
            'success': 'green-600',
            'warning': 'yellow-500',
            'error': 'red-600',
            'neutral': 'gray-600'
        },
        'component_classes': {
            'btn_primary': 'bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200',
            'btn_secondary': 'bg-violet-600 hover:bg-violet-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200',
            'btn_outline': 'border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-600 hover:text-white font-medium py-2 px-4 rounded-lg transition-all duration-200',
            'card': 'bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200',
            'card_dark': 'bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200',
            'input': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors duration-200',
            'gradient_bg': 'bg-gradient-to-r from-indigo-500 to-violet-600',
            'text_gradient': 'bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent'
        },
        'responsive_classes': {
            'container': 'container mx-auto px-4 sm:px-6 lg:px-8',
            'grid_responsive': 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6',
            'text_responsive': 'text-sm sm:text-base md:text-lg',
            'padding_responsive': 'p-4 sm:p-6 md:p-8',
            'margin_responsive': 'm-4 sm:m-6 md:m-8'
        },
        'animation_classes': {
            'fade_in': 'animate-fade-in',
            'slide_up': 'animate-slide-up',
            'bounce': 'animate-bounce',
            'pulse': 'animate-pulse',
            'spin': 'animate-spin',
            'transition_all': 'transition-all duration-300 ease-in-out',
            'hover_scale': 'hover:scale-105 transition-transform duration-200'
        }
    }


class TemplateHelpers:
    """
    Collection of template helper functions for common operations.
    
    This class provides static methods that can be used in templates
    for formatting, calculations, and data manipulation operations.
    """
    
    @staticmethod
    def format_price(price, currency='USD'):
        """
        Format price for display in templates.
        
        This method formats monetary values consistently across all templates,
        handling different currencies and decimal places appropriately.
        
        Args:
            price (Decimal): Price value to format
            currency (str): Currency code (default: 'USD')
            
        Returns:
            str: Formatted price string
            
        Example:
            >>> TemplateHelpers.format_price(Decimal('123.45'))
            '$123.45'
        """
        try:
            if price is None:
                return 'Price not available'
            
            price_decimal = Decimal(str(price))
            
            # Currency symbol mapping
            currency_symbols = {
                'USD': '$',
                'EUR': '€',
                'GBP': '£',
                'INR': '₹',
                'JPY': '¥'
            }
            
            symbol = currency_symbols.get(currency, currency)
            
            # Format with appropriate decimal places
            if currency == 'JPY':  # Japanese Yen typically has no decimal places
                return f"{symbol}{price_decimal:.0f}"
            else:
                return f"{symbol}{price_decimal:.2f}"
                
        except (ValueError, TypeError):
            return 'Invalid price'
    
    @staticmethod
    def format_distance(distance_km):
        """
        Format distance for display in templates.
        
        This method formats distance values with appropriate units
        and precision for user-friendly display.
        
        Args:
            distance_km (float): Distance in kilometers
            
        Returns:
            str: Formatted distance string
            
        Example:
            >>> TemplateHelpers.format_distance(1.5)
            '1.5 km'
        """
        try:
            if distance_km is None:
                return 'Distance unknown'
            
            distance = float(distance_km)
            
            if distance < 1:
                # Convert to meters for short distances
                meters = distance * 1000
                return f"{meters:.0f} m"
            else:
                # Keep in kilometers for longer distances
                return f"{distance:.1f} km"
                
        except (ValueError, TypeError):
            return 'Invalid distance'
    
    @staticmethod
    def format_rating(rating, max_rating=5):
        """
        Format rating for display with star representation.
        
        This method converts numeric ratings to star-based displays
        commonly used in review and rating systems.
        
        Args:
            rating (Decimal): Rating value
            max_rating (int): Maximum possible rating (default: 5)
            
        Returns:
            dict: Rating data with stars and numeric value
            
        Example:
            >>> TemplateHelpers.format_rating(Decimal('4.5'))
            {'numeric': '4.5', 'stars': '★★★★☆', 'percentage': 90}
        """
        try:
            if rating is None:
                return {
                    'numeric': 'No rating',
                    'stars': '☆☆☆☆☆',
                    'percentage': 0,
                    'full_stars': 0,
                    'half_stars': 0,
                    'empty_stars': max_rating
                }
            
            rating_float = float(rating)
            
            # Calculate star representation
            full_stars = int(rating_float)
            half_stars = 1 if (rating_float - full_stars) >= 0.5 else 0
            empty_stars = max_rating - full_stars - half_stars
            
            # Create star string
            stars = '★' * full_stars + '☆' * half_stars + '☆' * empty_stars
            
            # Calculate percentage for progress bars
            percentage = (rating_float / max_rating) * 100
            
            return {
                'numeric': f"{rating_float:.1f}",
                'stars': stars,
                'percentage': round(percentage),
                'full_stars': full_stars,
                'half_stars': half_stars,
                'empty_stars': empty_stars
            }
            
        except (ValueError, TypeError):
            return {
                'numeric': 'Invalid rating',
                'stars': '☆☆☆☆☆',
                'percentage': 0,
                'full_stars': 0,
                'half_stars': 0,
                'empty_stars': max_rating
            }
    
    @staticmethod
    def truncate_text(text, max_length=100, suffix='...'):
        """
        Truncate text to specified length with suffix.
        
        This method provides consistent text truncation across templates,
        ensuring proper handling of word boundaries and suffix addition.
        
        Args:
            text (str): Text to truncate
            max_length (int): Maximum length (default: 100)
            suffix (str): Suffix to add when truncated (default: '...')
            
        Returns:
            str: Truncated text with suffix if needed
        """
        try:
            if not text or len(text) <= max_length:
                return text
            
            # Find the last space before max_length to avoid cutting words
            truncate_at = max_length - len(suffix)
            last_space = text.rfind(' ', 0, truncate_at)
            
            if last_space > 0:
                return text[:last_space] + suffix
            else:
                return text[:truncate_at] + suffix
                
        except (TypeError, AttributeError):
            return str(text) if text else ''


# Template tag functions that can be registered
def get_template_helpers():
    """
    Get template helper functions for registration as template tags.
    
    This function returns a dictionary of helper functions that can be
    registered as template tags or filters for use in Django templates.
    
    Returns:
        dict: Dictionary of helper functions
    """
    return {
        'format_price': TemplateHelpers.format_price,
        'format_distance': TemplateHelpers.format_distance,
        'format_rating': TemplateHelpers.format_rating,
        'truncate_text': TemplateHelpers.truncate_text
    }
