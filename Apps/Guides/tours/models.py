"""
Models for the tours app.

This module contains models for managing tours, packages, and related data in the travel platform.
It defines the data structure for tour categories, tour details, images, itineraries,
inclusions/exclusions, reviews, available dates, and bookings.

The models in this file form the core business logic for the tours functionality,
allowing administrators to create and manage tour packages while enabling users
to browse, review, and book tours.

Key components include:
- TourCategory: For categorizing tours (e.g., Adventure, Cultural, Family)
- Tour: The main tour package model containing core tour information
- TourImage: Images associated with tours
- TourItinerary: Day-by-day breakdown of tour activities
- TourInclusion: Features included or excluded in tour packages
- TourReview: User reviews and ratings for tours
- TourDate: Available departure dates for tours
- Booking: User bookings for specific tour dates
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from destinations.models import Destination
from django.urls import reverse
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone


class TourCategory(models.Model):
    """
    Model representing a category for tours.
    
    This model is used to classify tours into specific categories such as 'Adventure Tours',
    'Cultural Tours', 'Family Tours', etc. Categories help in organizing tours and allow
    users to filter tours based on their interests.
    
    Attributes:
        name (str): The name of the category (e.g., 'Adventure Tours', 'Cultural Tours').
        slug (str): URL-friendly version of the name for SEO and clean URLs.
        description (str): Detailed description of the category for informational purposes.
        icon (str): Font Awesome icon class name (e.g., 'fa-hiking', 'fa-landmark') 
                   used for visual representation in UI.
        is_active (bool): Flag indicating whether the category is currently active and 
                         should be displayed to users in the frontend.
    """
    name = models.CharField(max_length=100, unique=True, help_text="Name of the category")
    slug = models.SlugField(max_length=100, unique=True, help_text="URL-friendly version of the name")
    description = models.TextField(blank=True, help_text="Description of the category")
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    is_active = models.BooleanField(default=True, help_text="Whether the category is active")
    
    class Meta:
        """Metadata options for the TourCategory model."""
        verbose_name = 'Tour Category'
        verbose_name_plural = 'Tour Categories'
        ordering = ['name']
    
    def __str__(self):
        """String representation of the TourCategory model."""
        return self.name


class Tour(models.Model):
    """
    Model representing a tour package offered to customers.
    
    This is the core model of the tours app that contains all the essential information about
    a tour package. Tours are linked to specific destinations and can be categorized for easier browsing.
    Each tour has detailed pricing information, duration specifications, and can be marked as
    featured for promotional purposes.
    
    Tours can have multiple related entities such as images (TourImage), detailed day-by-day itinerary
    (TourItinerary), inclusions/exclusions (TourInclusion), reviews (TourReview), and specific available
    dates for booking (TourDate).
    
    Attributes:
        title (str): The title of the tour (e.g., 'Amazing Paris Getaway').
        slug (str): URL-friendly version of the title for SEO and clean URLs.
        destination (ForeignKey): The destination this tour is associated with.
        category (ForeignKey): The category this tour belongs to (e.g., Adventure, Cultural).
        short_description (str): Brief description for tour listings and preview cards.
        description (str): Detailed description of the tour with all relevant information.
        duration_days (int): Duration of the tour in days (for display purposes).
        duration_nights (int): Duration of the tour in nights (for display purposes).
        max_group_size (int): Maximum number of people allowed in a tour group.
        difficulty (str): Difficulty level of the tour (easy, moderate, challenging, difficult).
        price (Decimal): Base price of the tour per person.
        discount_price (Decimal): Discounted price if any, for promotions or special offers.
        is_featured (bool): Whether the tour should be highlighted in featured sections.
        is_active (bool): Whether the tour is currently active and bookable.
        created_at (datetime): Timestamp when the tour record was created.
        updated_at (datetime): Timestamp when the tour record was last updated.
    """
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('challenging', 'Challenging'),
        ('difficult', 'Difficult'),
    ]
    
    title = models.CharField(max_length=200, help_text="Title of the tour")
    slug = models.SlugField(max_length=200, unique=True, help_text="URL-friendly version of the title")
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='tours',
                                   help_text="The destination this tour is for")
    category = models.ForeignKey(TourCategory, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='tours', help_text="Category of the tour")
    short_description = models.CharField(max_length=255, blank=True,
                                       help_text="Brief description for listings")
    description = models.TextField(help_text="Detailed description of the tour")
    duration_days = models.PositiveIntegerField(help_text="Duration in days")
    duration_nights = models.PositiveIntegerField(help_text="Duration in nights")
    max_group_size = models.PositiveIntegerField(default=10, help_text="Maximum group size")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='moderate',
                                help_text="Difficulty level of the tour")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base price of the tour")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                       help_text="Discounted price if any")
    is_featured = models.BooleanField(default=False, help_text="Whether the tour is featured")
    is_active = models.BooleanField(default=True, help_text="Whether the tour is active and bookable")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the tour was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="When the tour was last updated")
    
    class Meta:
        """Metadata options for the Tour model."""
        ordering = ['-is_featured', 'title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['is_active']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        """String representation of the Tour model."""
        return f"{self.title} - {self.destination.name}"
    
    def get_absolute_url(self):
        """Returns the URL to access a detail record for this tour."""
        return reverse('tours:tour_detail', args=[str(self.slug)])
    
    @property
    def duration_display(self):
        """Returns a formatted string of the tour duration."""
        if self.duration_days == 1:
            days = "1 day"
        else:
            days = f"{self.duration_days} days"
            
        if self.duration_nights == 1:
            nights = "1 night"
        else:
            nights = f"{self.duration_nights} nights"
            
        return f"{days} / {nights}"
        
    @property
    def get_discount_percentage(self):
        """
        Calculate the discount percentage if there is a discount price.
        
        Returns:
            int: The discount percentage as an integer (0-100)
        """
        if not self.discount_price or not self.price:
            return 0
        try:
            percentage = ((float(self.price) - float(self.discount_price)) / float(self.price)) * 100
            return int(round(percentage))
        except (ValueError, TypeError, ZeroDivisionError):
            return 0


class TourImage(models.Model):
    """
    Model for storing images related to a tour package.
    
    This model manages the gallery of images for each tour. Multiple images can be associated with 
    a single tour to showcase different aspects of the experience such as attractions, accommodations,
    activities, etc. One image can be designated as the 'featured' image to be used as the main 
    visual representation of the tour in listings and promotional materials.
    
    Attributes:
        tour (ForeignKey): Reference to the Tour model this image belongs to.
        image (ImageField): The actual image file stored in the media system.
        is_featured (bool): Flag indicating if this is the primary/featured image for the tour.
        created_at (datetime): Timestamp when this image record was created.
        updated_at (datetime): Timestamp when this image record was last updated.
    """
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='images',
                           help_text="The tour this image belongs to")
    image = models.ImageField(upload_to='tours/', help_text="The image file")
    caption = models.CharField(max_length=255, blank=True, help_text="Optional caption for the image")
    is_primary = models.BooleanField(default=False, 
                                   help_text="Whether this is the primary image for the tour")
    order = models.PositiveIntegerField(default=0, help_text="Display order for the image")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the image was uploaded")
    
    class Meta:
        """Metadata options for the TourImage model."""
        ordering = ['order', 'created_at']
        verbose_name = 'Tour Image'
        verbose_name_plural = 'Tour Images'
    
    def __str__(self):
        """String representation of the TourImage model."""
        return f"Image for {self.tour.title}"


class TourItinerary(models.Model):
    """
    Model for storing day-by-day itinerary for a tour package.
    
    This model provides a structured way to represent a detailed day-by-day breakdown of tour activities.
    Each tour can have multiple itinerary items, one for each day of the tour. The collection of
    itinerary items gives potential customers a clear understanding of what to expect during the tour,
    helping them make informed booking decisions.
    
    Attributes:
        tour (ForeignKey): Reference to the Tour model this itinerary item belongs to.
        day (int): The day number in the tour sequence (e.g., Day 1, Day 2).
        title (str): Brief title summarizing the day's activities (e.g., 'Arrival and Welcome Dinner').
        description (str): Detailed description of the day's activities, locations, meals, and experiences.
        created_at (datetime): Timestamp when this itinerary item was created.
        updated_at (datetime): Timestamp when this itinerary item was last updated.
    """
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='itineraries',
                           help_text="The tour this itinerary belongs to")
    day_number = models.PositiveIntegerField(help_text="The day number of the itinerary")
    title = models.CharField(max_length=200, help_text="Title for this day's activities")
    description = models.TextField(help_text="Detailed description of the day's activities")
    accommodation = models.CharField(max_length=255, blank=True,
                                   help_text="Information about the accommodation for this day")
    meals = models.CharField(max_length=255, blank=True,
                           help_text="Information about meals included on this day")
    
    class Meta:
        """Metadata options for the TourItinerary model."""
        verbose_name_plural = 'Tour Itineraries'
        ordering = ['tour', 'day_number']
        unique_together = ['tour', 'day_number']
    
    def __str__(self):
        """String representation of the TourItinerary model."""
        return f"Day {self.day_number}: {self.title} - {self.tour.title}"


class TourInclusion(models.Model):
    """
    Model for storing what's included or excluded in a tour package.
    
    This model clearly defines what services, amenities, meals, activities, and other items are 
    either included in the tour price or explicitly excluded. This transparency helps customers 
    understand exactly what they're paying for and what additional costs they might incur.
    The model can represent both inclusions (e.g., 'Airport transfers', 'Breakfast daily') and 
    exclusions (e.g., 'International flights', 'Travel insurance') through the is_included flag.
    
    Attributes:
        tour (ForeignKey): Reference to the Tour model this inclusion/exclusion belongs to.
        item (str): Description of the inclusion/exclusion item (e.g., 'Breakfast', 'Airport transfer').
        is_included (bool): Flag indicating whether this item is included (True) or excluded (False).
        created_at (datetime): Timestamp when this inclusion/exclusion record was created.
        updated_at (datetime): Timestamp when this inclusion/exclusion record was last updated.
    """
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='inclusions',
                           help_text="The tour this inclusion belongs to")
    name = models.CharField(max_length=200, help_text="Name of the inclusion")
    description = models.TextField(blank=True, help_text="Description of the inclusion")
    is_included = models.BooleanField(default=True, help_text="Whether this is included or excluded")
    
    class Meta:
        """Metadata options for the TourInclusion model."""
        ordering = ['-is_included', 'name']
    
    def __str__(self):
        """String representation of the TourInclusion model."""
        status = "Included" if self.is_included else "Not Included"
        return f"{self.name} ({status}) for {self.tour.title}"


class TourReview(models.Model):
    """
    Model for storing user reviews and ratings of tour packages.
    
    This model captures customer feedback about their tour experiences, including both numerical ratings
    and detailed comments. Reviews help build trust with potential customers by providing social proof
    and authentic experiences from previous travelers. They also provide valuable feedback to tour operators
    for improving their offerings.
    
    The model links both to the specific tour being reviewed and to the user who wrote the review,
    allowing for personalized review displays (with user profiles) and preventing duplicate reviews
    from the same user for the same tour.
    
    Attributes:
        tour (ForeignKey): Reference to the Tour model being reviewed.
        user (ForeignKey): Reference to the User model who wrote the review (authenticated customer).
        rating (int): Numerical rating from 1-5 (1=Poor, 5=Excellent).
        comment (str): Detailed review text with the customer's experience, opinions, and tips.
        created_at (datetime): Timestamp when the review was submitted.
        updated_at (datetime): Timestamp when the review was last updated.
    """
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='reviews',
                           help_text="The tour being reviewed")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                           related_name='tour_reviews', help_text="The user who wrote the review")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(help_text="The review text")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the review was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="When the review was last updated")
    is_approved = models.BooleanField(default=False, 
                                    help_text="Whether the review has been approved for display")
    
    class Meta:
        """Metadata options for the TourReview model."""
        ordering = ['-created_at']
        unique_together = ['tour', 'user']
    
    def __str__(self):
        """String representation of the TourReview model."""
        return f"{self.rating} stars by {self.user} for {self.tour}"


class TourDate(models.Model):
    """
    Model for storing available departure dates and their specific details for a tour package.
    
    This model represents the specific instances when a tour is scheduled to run. While a Tour model
    represents the general tour product, TourDate instances represent specific departures with their
    own dates, potentially unique pricing, and seat availability. This allows for seasonal pricing,
    limited-time offers, and real-time seat inventory management.
    
    Tour dates are critical for the booking process as customers select from available dates when
    making reservations. The model tracks both maximum capacity and current availability to prevent
    overbooking.
    
    Attributes:
        tour (ForeignKey): Reference to the Tour model these dates are for.
        start_date (date): The departure/starting date of the tour.
        end_date (date): The return/ending date of the tour.
        price (Decimal): Special price for this specific departure date (overrides the Tour's base price if set).
        max_seats (int): Maximum number of seats/spots available for this departure date.
        available_seats (int): Number of seats/spots still available for booking (decreases as bookings are made).
        created_at (datetime): Timestamp when this tour date record was created.
        updated_at (datetime): Timestamp when this tour date record was last updated.
    """
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='dates',
                           help_text="The tour these dates are for")
    start_date = models.DateField(help_text="Start date of the tour")
    end_date = models.DateField(help_text="End date of the tour")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                              help_text="Price for this specific date (overrides tour.price if set)")
    available_spots = models.PositiveIntegerField(default=0,
                                                help_text="Number of spots available for this date")
    is_guaranteed = models.BooleanField(default=False,
                                      help_text="Whether the departure is guaranteed")
    notes = models.TextField(blank=True, help_text="Additional notes about this specific tour date")
    
    class Meta:
        """Metadata options for the TourDate model."""
        ordering = ['start_date']
        verbose_name = 'Tour Date'
        verbose_name_plural = 'Tour Dates'
        unique_together = ['tour', 'start_date']
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['is_guaranteed']),
        ]
    
    def __str__(self):
        """String representation of the TourDate model."""
        return f"{self.tour.title} - {self.start_date.strftime('%b %d, %Y')}"
    
    def clean(self):
        """Validate that end_date is after start_date."""
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'End date must be after start date.'})
    
    @property
    def is_past(self):
        """Check if the tour date is in the past."""
        return self.start_date < timezone.now().date()
    
    @property
    def actual_price(self):
        """Get the actual price for this date (either the date-specific price or the tour's default price)."""
        return self.price if self.price else self.tour.price
    
    @property
    def is_available(self):
        """Check if this tour date is available for booking."""
        return not self.is_past and self.available_spots > 0


class Booking(models.Model):
    """
    Model for storing customer reservations for tour packages.
    
    This is a critical model that represents the transaction of a customer booking a specific tour
    on a specific date. It links the customer (user) with their chosen tour date and stores all the
    necessary information about the reservation, including number of travelers, pricing, payment status,
    and any special requests.
    
    The booking model is central to the business operations, as it represents actual sales and revenue.
    It tracks the entire lifecycle of a booking from initial reservation through payment processing
    to completion or cancellation.
    
    Attributes:
        user (ForeignKey): Reference to the User model representing the customer making the booking.
        tour_date (ForeignKey): Reference to the TourDate model representing the specific departure being booked.
        booking_date (date): The date when the booking/reservation was made.
        num_persons (int): Number of travelers/persons included in this booking.
        total_price (Decimal): Total calculated price for all travelers, including any discounts or surcharges.
        payment_status (str): Current status of payment (e.g., 'pending', 'paid', 'refunded').
        booking_status (str): Current status of the booking (e.g., 'confirmed', 'canceled', 'completed').
        special_requests (str): Any special requirements or requests from the customer (e.g., dietary needs, accessibility).
        created_at (datetime): Timestamp when the booking record was created in the system.
        updated_at (datetime): Timestamp when the booking record was last updated.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    PAYMENT_CHOICES = [
        ('pending', 'Pending'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]
    
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='bookings',
                           help_text="The tour being booked")
    tour_date = models.ForeignKey(TourDate, on_delete=models.CASCADE, related_name='bookings',
                               help_text="The specific date of the tour being booked")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                           related_name='tour_bookings', help_text="The user making the booking")
    number_of_people = models.PositiveIntegerField(default=1,
                                                 help_text="Number of people included in the booking")
    booking_date = models.DateTimeField(auto_now_add=True, help_text="When the booking was made")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending',
                          help_text="Current status of the booking")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2,
                                     help_text="Total amount for the booking")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='pending',
                                   help_text="Current status of the payment")
    special_requests = models.TextField(blank=True,
                                     help_text="Any special requests from the user")
    contact_email = models.EmailField(help_text="Contact email for the booking")
    contact_phone = models.CharField(max_length=20, blank=True,
                                  help_text="Contact phone for the booking")
    
    class Meta:
        """Metadata options for the Booking model."""
        ordering = ['-booking_date']
        verbose_name = 'Tour Booking'
        verbose_name_plural = 'Tour Bookings'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['booking_date']),
        ]
    
    def __str__(self):
        """String representation of the Booking model."""
        return f"{self.user} - {self.tour.title} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Override save method to calculate total amount if not provided."""
        if not self.total_amount:
            # Calculate based on tour date price and number of people
            price = self.tour_date.actual_price
            self.total_amount = price * Decimal(self.number_of_people)
        super().save(*args, **kwargs)
