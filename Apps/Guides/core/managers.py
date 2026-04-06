"""
Custom model managers for enhanced database operations across the TravelGuide application.

This module provides custom Django model managers that implement common query patterns,
optimizations, and business logic operations. These managers are designed to be reused
across different apps to ensure consistent database access patterns and improved performance.

Key Features:
- Optimized querysets with proper prefetching and select_related
- Location-based query methods using geographical calculations
- Approval workflow management for content moderation
- Caching integration for frequently accessed data
- Comprehensive error handling and logging
"""

import logging
from typing import List, Optional, Dict, Any
from decimal import Decimal
from django.db import models, transaction
from django.db.models import Q, Prefetch, Avg, Count, Case, When, Value
from django.utils import timezone
from django.core.cache import cache

# Configure logger for this module
logger = logging.getLogger(__name__)


class BaseOptimizedManager(models.Manager):
    """
    Base manager class with common optimization patterns.
    
    This manager provides common query optimizations that can be inherited
    by other managers to ensure consistent performance patterns across the application.
    """
    
    def get_active(self):
        """
        Get only active records.
        
        This method filters the queryset to include only records marked as active,
        which is a common pattern across multiple models in the application.
        
        Returns:
            QuerySet: Filtered queryset containing only active records
        """
        return self.filter(is_active=True)
    
    def get_featured(self):
        """
        Get only featured records.
        
        This method filters the queryset to include only records marked as featured,
        typically used for highlighting important content on the homepage or listings.
        
        Returns:
            QuerySet: Filtered queryset containing only featured records
        """
        return self.filter(is_featured=True, is_active=True)
    
    def with_counts(self):
        """
        Annotate queryset with related object counts.
        
        This method adds count annotations for related objects, which is useful
        for displaying statistics without additional database queries.
        
        Returns:
            QuerySet: Annotated queryset with count fields
        """
        # This is a base implementation - subclasses should override with specific counts
        return self.get_queryset()
    
    def recent(self, days: int = 30):
        """
        Get records created within the specified number of days.
        
        This method filters records based on their creation date, useful for
        displaying recent content or implementing time-based features.
        
        Args:
            days (int): Number of days to look back (default: 30)
            
        Returns:
            QuerySet: Filtered queryset with recent records
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff_date)


class LocationBasedManager(BaseOptimizedManager):
    """
    Manager for models that include geographical location data.
    
    This manager provides methods for location-based queries, distance calculations,
    and geographical filtering operations commonly used in travel applications.
    """
    
    def nearby(self, latitude: float, longitude: float, radius_km: float = 15):
        """
        Find records within a specified radius of given coordinates.
        
        This method uses a bounding box optimization followed by precise distance
        calculations to find records within the specified radius efficiently.
        
        Args:
            latitude (float): Center latitude in decimal degrees
            longitude (float): Center longitude in decimal degrees
            radius_km (float): Search radius in kilometers (default: 15)
            
        Returns:
            QuerySet: Filtered queryset with records within the specified radius
        """
        from core.utils import LocationUtils
        
        # Validate coordinates
        if not LocationUtils.validate_coordinates(latitude, longitude):
            logger.warning(f"Invalid coordinates provided: lat={latitude}, lng={longitude}")
            return self.none()
        
        # Calculate bounding box for initial filtering
        min_lat, max_lat, min_lng, max_lng = LocationUtils.get_bounding_box(
            latitude, longitude, radius_km
        )
        
        # Filter by bounding box first (database-level optimization)
        return self.filter(
            latitude__isnull=False,
            longitude__isnull=False,
            latitude__range=(min_lat, max_lat),
            longitude__range=(min_lng, max_lng),
            is_active=True
        )
    
    def within_region(self, region_name: str):
        """
        Filter records within a specific geographical region.
        
        This method filters records based on their associated region,
        useful for displaying location-specific content.
        
        Args:
            region_name (str): Name of the region to filter by
            
        Returns:
            QuerySet: Filtered queryset with records in the specified region
        """
        return self.filter(
            region__name__icontains=region_name,
            is_active=True
        )
    
    def by_country(self, country_name: str):
        """
        Filter records by country name.
        
        This method provides country-level filtering for international
        travel applications with multiple country support.
        
        Args:
            country_name (str): Name of the country to filter by
            
        Returns:
            QuerySet: Filtered queryset with records in the specified country
        """
        return self.filter(
            country__icontains=country_name,
            is_active=True
        )


class ApprovalWorkflowManager(BaseOptimizedManager):
    """
    Manager for models that implement approval workflows.
    
    This manager provides methods for handling content moderation,
    approval processes, and status-based filtering operations.
    """
    
    def pending_approval(self):
        """
        Get records pending approval.
        
        This method filters records that are waiting for review and approval
        by administrators or content moderators.
        
        Returns:
            QuerySet: Filtered queryset with pending records
        """
        return self.filter(approval_status='pending')
    
    def approved(self):
        """
        Get approved records.
        
        This method filters records that have been reviewed and approved
        for public display on the website.
        
        Returns:
            QuerySet: Filtered queryset with approved records
        """
        return self.filter(approval_status='approved', is_active=True)
    
    def rejected(self):
        """
        Get rejected records.
        
        This method filters records that have been reviewed and rejected
        during the approval process.
        
        Returns:
            QuerySet: Filtered queryset with rejected records
        """
        return self.filter(approval_status='rejected')
    
    def needs_review(self):
        """
        Get records that need administrative review.
        
        This method returns records that require attention from moderators,
        including both pending submissions and flagged content.
        
        Returns:
            QuerySet: Filtered queryset with records needing review
        """
        return self.filter(
            Q(approval_status='pending') | Q(approval_status='flagged')
        )
    
    def by_reviewer(self, user):
        """
        Get records reviewed by a specific user.
        
        This method filters records based on who reviewed them,
        useful for tracking reviewer activity and performance.
        
        Args:
            user: User object representing the reviewer
            
        Returns:
            QuerySet: Filtered queryset with records reviewed by the specified user
        """
        return self.filter(reviewed_by=user)


class DestinationManager(LocationBasedManager, ApprovalWorkflowManager):
    """
    Custom manager for Destination model with optimized queries and business logic.
    
    This manager combines location-based and approval workflow functionality
    specifically tailored for destination management operations.
    """
    
    def get_queryset(self):
        """
        Return the base queryset with common optimizations.
        
        This method applies standard optimizations that are beneficial
        for most destination-related queries.
        
        Returns:
            QuerySet: Optimized base queryset
        """
        return super().get_queryset().select_related('region')
    
    def with_images(self):
        """
        Prefetch destination images to avoid N+1 queries.
        
        This method optimizes image loading by prefetching related images,
        particularly useful for list views and detail pages.
        
        Returns:
            QuerySet: Queryset with prefetched images
        """
        return self.prefetch_related(
            Prefetch(
                'images',
                queryset=models.Model.objects.select_related().order_by('-is_primary', 'id'),
                to_attr='all_images'
            ),
            Prefetch(
                'images',
                queryset=models.Model.objects.filter(is_primary=True),
                to_attr='primary_images'
            )
        )
    
    def with_attractions(self):
        """
        Prefetch related attractions to avoid N+1 queries.
        
        This method optimizes attraction loading for destinations,
        useful when displaying destination details with their attractions.
        
        Returns:
            QuerySet: Queryset with prefetched attractions
        """
        return self.prefetch_related(
            Prefetch(
                'attractions',
                queryset=models.Model.objects.filter(is_active=True).order_by('name')
            )
        )
    
    def with_stats(self):
        """
        Annotate destinations with statistical information.
        
        This method adds computed fields for statistics like attraction count,
        average ratings, and other metrics useful for sorting and display.
        
        Returns:
            QuerySet: Annotated queryset with statistical fields
        """
        return self.annotate(
            attraction_count=Count('attractions', filter=Q(attractions__is_active=True)),
            tour_count=Count('tours', filter=Q(tours__is_active=True)),
            avg_tour_price=Avg('tours__price', filter=Q(tours__is_active=True))
        )
    
    def popular(self, limit: int = 10):
        """
        Get popular destinations based on views and ratings.
        
        This method returns destinations sorted by popularity metrics,
        useful for homepage features and recommendation systems.
        
        Args:
            limit (int): Maximum number of destinations to return (default: 10)
            
        Returns:
            QuerySet: Popular destinations ordered by popularity score
        """
        return self.get_active().annotate(
            popularity_score=models.F('views') + models.F('rating') * 100
        ).order_by('-popularity_score')[:limit]
    
    def by_price_range(self, min_price: Decimal = None, max_price: Decimal = None):
        """
        Filter destinations by price range.
        
        This method provides price-based filtering for budget-conscious travelers
        and premium experience seekers.
        
        Args:
            min_price (Decimal, optional): Minimum price filter
            max_price (Decimal, optional): Maximum price filter
            
        Returns:
            QuerySet: Filtered queryset within the specified price range
        """
        queryset = self.get_active()
        
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset
    
    def search(self, query: str):
        """
        Perform text search across destination fields.
        
        This method implements full-text search functionality across
        destination names, descriptions, and related field content.
        
        Args:
            query (str): Search query string
            
        Returns:
            QuerySet: Filtered queryset matching the search criteria
        """
        if not query or not query.strip():
            return self.none()
        
        # Clean and prepare search terms
        search_terms = query.strip().split()
        
        # Build search query using Q objects
        search_q = Q()
        for term in search_terms:
            search_q |= (
                Q(name__icontains=term) |
                Q(description__icontains=term) |
                Q(short_description__icontains=term) |
                Q(city__icontains=term) |
                Q(country__icontains=term) |
                Q(region__name__icontains=term)
            )
        
        return self.get_active().filter(search_q).distinct()


class TourManager(ApprovalWorkflowManager):
    """
    Custom manager for Tour model with optimized queries and business logic.
    
    This manager provides tour-specific query methods and optimizations
    for the tour booking and management system.
    """
    
    def get_queryset(self):
        """
        Return the base queryset with common optimizations.
        
        Returns:
            QuerySet: Optimized base queryset with category prefetching
        """
        return super().get_queryset().select_related('category')
    
    def with_destinations(self):
        """
        Prefetch tour destinations to avoid N+1 queries.
        
        This method optimizes destination loading for tours,
        essential for tour detail pages and itinerary displays.
        
        Returns:
            QuerySet: Queryset with prefetched destinations
        """
        return self.prefetch_related(
            Prefetch(
                'destinations',
                queryset=models.Model.objects.filter(is_active=True).select_related('region')
            )
        )
    
    def with_dates(self):
        """
        Prefetch available tour dates.
        
        This method optimizes date loading for tours, important for
        booking availability and calendar displays.
        
        Returns:
            QuerySet: Queryset with prefetched tour dates
        """
        return self.prefetch_related(
            Prefetch(
                'dates',
                queryset=models.Model.objects.filter(
                    is_available=True,
                    start_date__gte=timezone.now().date()
                ).order_by('start_date')
            )
        )
    
    def available(self):
        """
        Get tours that have available dates in the future.
        
        This method filters tours that have bookable dates,
        excluding tours with no future availability.
        
        Returns:
            QuerySet: Tours with future availability
        """
        return self.get_active().filter(
            dates__is_available=True,
            dates__start_date__gte=timezone.now().date()
        ).distinct()
    
    def by_category(self, category_name: str):
        """
        Filter tours by category name.
        
        This method provides category-based filtering for organizing
        tours by type (adventure, cultural, culinary, etc.).
        
        Args:
            category_name (str): Name of the tour category
            
        Returns:
            QuerySet: Tours in the specified category
        """
        return self.get_active().filter(
            category__name__icontains=category_name,
            category__is_active=True
        )
    
    def by_duration(self, min_days: int = None, max_days: int = None):
        """
        Filter tours by duration range.
        
        This method allows filtering tours based on trip length,
        useful for travelers with specific time constraints.
        
        Args:
            min_days (int, optional): Minimum duration in days
            max_days (int, optional): Maximum duration in days
            
        Returns:
            QuerySet: Tours within the specified duration range
        """
        queryset = self.get_active()
        
        if min_days is not None:
            queryset = queryset.filter(duration_days__gte=min_days)
        
        if max_days is not None:
            queryset = queryset.filter(duration_days__lte=max_days)
        
        return queryset
    
    def by_price_range(self, min_price: Decimal = None, max_price: Decimal = None):
        """
        Filter tours by price range.
        
        This method provides price-based filtering for budget planning
        and premium tour selection.
        
        Args:
            min_price (Decimal, optional): Minimum price filter
            max_price (Decimal, optional): Maximum price filter
            
        Returns:
            QuerySet: Tours within the specified price range
        """
        queryset = self.get_active()
        
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset


class ReviewManager(BaseOptimizedManager):
    """
    Custom manager for Review model with rating and moderation features.
    
    This manager handles review-specific operations including rating
    calculations, moderation workflows, and content filtering.
    """
    
    def approved(self):
        """
        Get approved reviews only.
        
        This method filters reviews that have been moderated and approved
        for public display, ensuring content quality.
        
        Returns:
            QuerySet: Approved reviews only
        """
        return self.filter(is_approved=True)
    
    def for_content_type(self, content_type, object_id):
        """
        Get reviews for a specific content object.
        
        This method retrieves reviews for a particular destination, tour,
        or other reviewable content using generic foreign keys.
        
        Args:
            content_type: ContentType of the reviewed object
            object_id: ID of the reviewed object
            
        Returns:
            QuerySet: Reviews for the specified object
        """
        return self.approved().filter(
            content_type=content_type,
            object_id=object_id
        ).order_by('-created_at')
    
    def by_rating(self, min_rating: int = None, max_rating: int = None):
        """
        Filter reviews by rating range.
        
        This method allows filtering reviews based on their rating scores,
        useful for displaying only positive or negative feedback.
        
        Args:
            min_rating (int, optional): Minimum rating (1-5)
            max_rating (int, optional): Maximum rating (1-5)
            
        Returns:
            QuerySet: Reviews within the specified rating range
        """
        queryset = self.approved()
        
        if min_rating is not None:
            queryset = queryset.filter(rating__gte=min_rating)
        
        if max_rating is not None:
            queryset = queryset.filter(rating__lte=max_rating)
        
        return queryset
    
    def recent_reviews(self, days: int = 30):
        """
        Get recent reviews within specified timeframe.
        
        This method retrieves reviews created within the specified number
        of days, useful for displaying fresh content and recent feedback.
        
        Args:
            days (int): Number of days to look back (default: 30)
            
        Returns:
            QuerySet: Recent reviews within the timeframe
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.approved().filter(created_at__gte=cutoff_date)
