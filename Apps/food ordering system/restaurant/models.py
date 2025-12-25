"""
Restaurant app models.
Defines Restaurant and PendingRestaurant models for managing restaurant information.
"""
from django.db import models
from django.contrib.auth.models import User
from core.models import TimeStampedModel
from core.encryption import EncryptionManager
from django.utils.functional import cached_property
from django.db.models import Avg, Count


class Restaurant(TimeStampedModel):
    """
    Represents a restaurant in the food ordering system.
    
    Fields:
        owner: ForeignKey to User (restaurant owner/manager)
        name: Restaurant name (max 200 characters)
        description: Detailed description of the restaurant
        address: Physical address of the restaurant
        phone: Contact phone number
        email: Contact email address
        cuisine_type: Type of cuisine (Italian, Indian, American, etc.)
        image: Restaurant cover/logo image
        is_active: Boolean to enable/disable restaurant
        is_approved: Boolean to indicate manager approval status
        opening_time: Restaurant opening time
        closing_time: Restaurant closing time
        minimum_order: Minimum order amount
        delivery_fee: Delivery charge
        rating: Average rating (0-5)
    """
    # Cuisine type choices for filtering and categorization
    CUISINE_CHOICES = [
        ('italian', 'Italian'),
        ('indian', 'Indian'),
        ('american', 'American'),
        ('chinese', 'Chinese'),
        ('japanese', 'Japanese'),
        ('mexican', 'Mexican'),
        ('thai', 'Thai'),
        ('mediterranean', 'Mediterranean'),
        ('french', 'French'),
        ('other', 'Other'),
    ]
    
    # Approval status choices
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='restaurants',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Encrypted sensitive fields for restaurant contact information
    _address_encrypted = models.TextField(
        blank=True,
        null=True,
        help_text='Encrypted restaurant physical address'
    )
    _phone_encrypted = models.TextField(
        blank=True,
        null=True,
        help_text='Encrypted restaurant contact phone number'
    )
    _email_encrypted = models.TextField(
        blank=True,
        null=True,
        help_text='Encrypted restaurant contact email'
    )
    cuisine_type = models.CharField(
        max_length=20,
        choices=CUISINE_CHOICES,
        default='other',
        help_text='Primary cuisine type of the restaurant'
    )
    image = models.ImageField(upload_to='restaurants/', blank=True, null=True)
    image_url = models.URLField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text='External image URL (takes precedence over uploaded image)'
    )
    
    def get_image_url(self):
        """
        Get restaurant image URL with intelligent 4-layer fallback system.
        
        Returns priority order:
        1. External image URL from image_url field
        2. Uploaded image file from image field  
        3. Cuisine-specific placeholder images from local media directory
        4. Local default restaurant image
        
        Includes multiple layers of error handling for robustness.
        
        Returns:
            str: Complete image URL for display in templates
        """
        try:
            # First try external image URL (highest priority)
            if self.image_url and self.image_url.strip():
                return self.image_url.strip()
        except (ValueError, AttributeError):
            pass
        
        try:
            # Second try uploaded image from database
            if self.image and hasattr(self.image, 'url'):
                return self.image.url
        except (ValueError, AttributeError, OSError):
            # Handle cases where image file is missing, corrupted, or inaccessible
            pass
        
        try:
            # Third fallback to cuisine-specific placeholder images
            from image_links import get_restaurant_image
            return get_restaurant_image(self.cuisine_type, 0)
        except (ImportError, IndexError, KeyError):
            # Handle cases where image_links.py fails or cuisine not found
            pass
        
        # Ultimate fallback - local default restaurant image
        return '/media/placeholders/restaurant_default.jpg'
    
    def get_thumbnail_url(self):
        """
        Get thumbnail version of restaurant image.
        
        Returns:
            str: Thumbnail image URL or fallback
        """
        # For now, return same as get_image_url()
        # TODO: Implement actual thumbnail generation
        return self.get_image_url()
    is_active = models.BooleanField(default=False)  # Changed to False by default
    is_approved = models.BooleanField(
        default=False,
        help_text='Whether the restaurant has been approved by a manager'
    )
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
        help_text='Current approval status of the restaurant'
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        help_text='Reason for rejection if applicable'
    )
    opening_time = models.TimeField(default='09:00')
    closing_time = models.TimeField(default='22:00')
    minimum_order = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text='Minimum order amount in rupees'
    )
    delivery_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text='Delivery charge in rupees'
    )
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00,
        help_text='Average rating (0-5)'
    )
    
    # Property methods for transparent encryption/decryption
    @property
    def address(self):
        """
        Get decrypted restaurant address.
        
        Transparently decrypts the address when accessed.
        
        Returns:
            str: Decrypted address or empty string
        """
        return EncryptionManager.decrypt(self._address_encrypted) or ''
    
    @address.setter
    def address(self, value):
        """
        Set and encrypt restaurant address.
        
        Transparently encrypts the address when set.
        
        Args:
            value (str): Plaintext address to encrypt
        """
        self._address_encrypted = EncryptionManager.encrypt(value)
    
    @property
    def phone(self):
        """
        Get decrypted restaurant phone number.
        
        Transparently decrypts the phone number when accessed.
        
        Returns:
            str: Decrypted phone number or empty string
        """
        return EncryptionManager.decrypt(self._phone_encrypted) or ''
    
    @phone.setter
    def phone(self, value):
        """
        Set and encrypt restaurant phone number.
        
        Transparently encrypts the phone number when set.
        
        Args:
            value (str): Plaintext phone number to encrypt
        """
        self._phone_encrypted = EncryptionManager.encrypt(value)
    
    @property
    def email(self):
        """
        Get decrypted restaurant email.
        
        Transparently decrypts the email when accessed.
        
        Returns:
            str: Decrypted email or empty string
        """
        return EncryptionManager.decrypt(self._email_encrypted) or ''
    
    @email.setter
    def email(self, value):
        """
        Set and encrypt restaurant email.
        
        Transparently encrypts the email when set.
        
        Args:
            value (str): Plaintext email to encrypt
        """
        self._email_encrypted = EncryptionManager.encrypt(value)
    
    class Meta:
        verbose_name = 'Restaurant'
        verbose_name_plural = 'Restaurants'
        ordering = ['-rating', 'name']
    
    def __str__(self):
        """
        Returns string representation of the restaurant.
        
        Returns:
            str: Restaurant name
        """
        return self.name
    
    def is_open(self):
        """
        Check if restaurant is currently open.
        
        Returns:
            bool: True if restaurant is open, False otherwise
        """
        from datetime import datetime
        now = datetime.now().time()
        return self.opening_time <= now <= self.closing_time
    
    def approve_restaurant(self):
        """
        Approve the restaurant and make it active.
        
        Sets is_approved to True, is_active to True, and approval_status to 'approved'.
        """
        self.is_approved = True
        self.is_active = True
        self.approval_status = 'approved'
        self.rejection_reason = None
        self.save()
    
    def reject_restaurant(self, reason):
        """
        Reject the restaurant with a reason.
        
        Args:
            reason (str): Reason for rejection
        """
        self.is_approved = False
        self.is_active = False
        self.approval_status = 'rejected'
        self.rejection_reason = reason
        self.save()
    
    def get_total_orders(self):
        """
        Get total number of orders for this restaurant.
        
        Returns:
            int: Total order count
        """
        from orders.models import OrderItem
        return OrderItem.objects.filter(menu_item__restaurant=self).values('order').distinct().count()
    
    def get_total_revenue(self):
        """
        Calculate total revenue from all orders.
        
        Returns:
            Decimal: Total revenue amount
        """
        from orders.models import OrderItem
        from django.db.models import Sum, F
        
        total = OrderItem.objects.filter(
            menu_item__restaurant=self,
            order__status='delivered'
        ).aggregate(
            revenue=Sum(F('price') * F('quantity'))
        )['revenue']
        
        return total or 0
    
    def get_average_order_value(self):
        """
        Calculate average order value for this restaurant.
        
        Returns:
            Decimal: Average order amount
        """
        total_revenue = self.get_total_revenue()
        total_orders = self.get_total_orders()
        
        if total_orders > 0:
            return total_revenue / total_orders
        return 0
    
    @cached_property
    def average_rating(self):
        """
        Calculate average rating from non-hidden restaurant reviews.
        
        Returns:
            float: Average rating (0-5) with one decimal place
        """
        from customer.models import RestaurantReview
        
        avg_rating = RestaurantReview.objects.filter(
            restaurant=self,
            is_hidden=False
        ).aggregate(
            average=Avg('rating')
        )['average']
        
        return round(avg_rating, 1) if avg_rating else 0.0
    
    @cached_property
    def review_count(self):
        """
        Count non-hidden restaurant reviews for this restaurant.
        
        Returns:
            int: Total count of visible reviews
        """
        from customer.models import RestaurantReview
        
        count = RestaurantReview.objects.filter(
            restaurant=self,
            is_hidden=False
        ).aggregate(
            total=Count('id')
        )['total']
        
        return count or 0
    
    def update_rating(self):
        """
        Update the cached rating field based on current reviews.
        
        This method should be called when reviews are added, updated, or hidden.
        """
        self.rating = self.average_rating
        self.save(update_fields=['rating'])
    
    def get_review_count(self):
        """
        Get total number of reviews for this restaurant.
        
        Returns:
            int: Total review count
        """
        return self.reviews.filter(is_approved=True).count()
    
    def get_average_rating(self):
        """
        Calculate average rating from approved reviews.
        
        Returns:
            float: Average rating or 0 if no reviews
        """
        from django.db.models import Avg
        
        avg = self.reviews.filter(is_approved=True).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating']
        
        return round(avg, 2) if avg else 0
    
    def update_rating(self):
        """
        Update restaurant rating based on approved reviews.
        Auto-calculated from customer reviews.
        """
        self.rating = self.get_average_rating()
        self.save(update_fields=['rating'])
    
    def get_popular_items(self, limit=5):
        """
        Get most popular menu items based on order count.
        
        Args:
            limit (int): Number of items to return
        
        Returns:
            QuerySet: Top menu items ordered by popularity
        """
        from orders.models import OrderItem
        from django.db.models import Count, Sum
        
        return self.menu_items.annotate(
            order_count=Count('orderitem'),
            total_sold=Sum('orderitem__quantity')
        ).filter(order_count__gt=0).order_by('-order_count')[:limit]
    
    def get_wishlist_count(self):
        """
        Get number of customers who wishlisted this restaurant.
        
        Returns:
            int: Wishlist count
        """
        return self.wishlisted_by.count()


class PendingRestaurant(TimeStampedModel):
    """
    Represents a pending restaurant application submitted by customers.
    
    This model stores restaurant applications that are waiting for manager approval.
    Once approved, the data is transferred to the Restaurant model.
    
    Fields:
        user: ForeignKey to User (customer applying to become restaurant owner)
        restaurant_name: Proposed restaurant name
        description: Restaurant description
        address: Restaurant address
        phone: Contact phone number
        email: Restaurant contact email
        cuisine_type: Type of cuisine
        image: Restaurant image
        opening_time: Business opening time
        closing_time: Business closing time
        minimum_order: Minimum order amount
        delivery_fee: Delivery fee
        status: Application status (pending, approved, rejected)
        rejection_reason: Reason for rejection
        processed_by: Manager who processed the application
        processed_at: When the application was processed
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pending_restaurants',
        help_text='Customer applying to become a restaurant owner'
    )
    restaurant_name = models.CharField(
        max_length=200,
        help_text='Proposed restaurant name'
    )
    description = models.TextField(
        help_text='Restaurant description and specialties'
    )
    
    # Encrypted sensitive fields for pending restaurant contact information
    _address_encrypted = models.TextField(
        blank=True,
        null=True,
        help_text='Encrypted restaurant physical address'
    )
    _phone_encrypted = models.TextField(
        blank=True,
        null=True,
        help_text='Encrypted contact phone number'
    )
    _email_encrypted = models.TextField(
        blank=True,
        null=True,
        help_text='Encrypted restaurant contact email'
    )
    cuisine_type = models.CharField(
        max_length=20,
        choices=Restaurant.CUISINE_CHOICES,
        default='other',
        help_text='Primary cuisine type'
    )
    image = models.ImageField(
        upload_to='pending_restaurants/',
        blank=True,
        null=True,
        help_text='Restaurant logo or cover photo'
    )
    opening_time = models.TimeField(
        default='09:00',
        help_text='Business opening time'
    )
    closing_time = models.TimeField(
        default='22:00',
        help_text='Business closing time'
    )
    minimum_order = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Minimum order amount in rupees'
    )
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Delivery charge in rupees'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Application status'
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        help_text='Reason for rejection if applicable'
    )
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_restaurants',
        help_text='Manager who processed this application'
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this application was processed'
    )
    
    # Property methods for transparent encryption/decryption
    @property
    def address(self):
        """
        Get decrypted restaurant address.
        
        Returns:
            str: Decrypted address or empty string
        """
        return EncryptionManager.decrypt(self._address_encrypted) or ''
    
    @address.setter
    def address(self, value):
        """
        Set and encrypt restaurant address.
        
        Args:
            value (str): Plaintext address to encrypt
        """
        self._address_encrypted = EncryptionManager.encrypt(value)
    
    @property
    def phone(self):
        """
        Get decrypted restaurant phone number.
        
        Returns:
            str: Decrypted phone number or empty string
        """
        return EncryptionManager.decrypt(self._phone_encrypted) or ''
    
    @phone.setter
    def phone(self, value):
        """
        Set and encrypt restaurant phone number.
        
        Args:
            value (str): Plaintext phone number to encrypt
        """
        self._phone_encrypted = EncryptionManager.encrypt(value)
    
    @property
    def email(self):
        """
        Get decrypted restaurant email.
        
        Returns:
            str: Decrypted email or empty string
        """
        return EncryptionManager.decrypt(self._email_encrypted) or ''
    
    @email.setter
    def email(self, value):
        """
        Set and encrypt restaurant email.
        
        Args:
            value (str): Plaintext email to encrypt
        """
        self._email_encrypted = EncryptionManager.encrypt(value)
    
    class Meta:
        verbose_name = 'Pending Restaurant'
        verbose_name_plural = 'Pending Restaurants'
        ordering = ['-created_at']
    
    def __str__(self):
        """
        Returns string representation of the pending restaurant.
        
        Returns:
            str: Restaurant name with status
        """
        return f"{self.restaurant_name} - {self.get_status_display()}"
    
    def approve_application(self, manager):
        """
        Approve the restaurant application and create the actual restaurant.
        
        Args:
            manager (User): The manager approving the application
            
        Returns:
            Restaurant: The created restaurant object
        """
        from django.contrib.auth.models import Group
        from django.utils import timezone
        
        # Create the actual restaurant
        restaurant = Restaurant.objects.create(
            owner=self.user,
            name=self.restaurant_name,
            description=self.description,
            address=self.address,
            phone=self.phone,
            email=self.email,
            cuisine_type=self.cuisine_type,
            image=self.image,
            opening_time=self.opening_time,
            closing_time=self.closing_time,
            minimum_order=self.minimum_order,
            delivery_fee=self.delivery_fee,
            is_approved=True,
            is_active=True,
            approval_status='approved'
        )
        
        # Assign user to Restaurant Owner group
        restaurant_group = Group.objects.filter(name='Restaurant Owner').first()
        if restaurant_group:
            self.user.groups.add(restaurant_group)
        
        # Update pending application status
        self.status = 'approved'
        self.processed_by = manager
        self.processed_at = timezone.now()
        self.save()
        
        return restaurant
    
    def reject_application(self, manager, reason):
        """
        Reject the restaurant application.
        
        Args:
            manager (User): The manager rejecting the application
            reason (str): Reason for rejection
        """
        from django.utils import timezone
        
        self.status = 'rejected'
        self.rejection_reason = reason
        self.processed_by = manager
        self.processed_at = timezone.now()
        self.save()


class ManagerLoginLog(TimeStampedModel):
    """
    Tracks manager login details for security and audit purposes.
    
    This model maintains a comprehensive log of all staff user authentication
    events including login time, logout time, IP address, user agent, and session duration.
    
    Fields:
        user: ForeignKey to User (staff member who logged in)
        login_time: When the manager logged in
        logout_time: When the manager logged out (null for active sessions)
        ip_address: IP address from which the login occurred
        user_agent: Browser/device information
        session_duration: Duration of the session in minutes
        is_active_session: Whether this session is currently active
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='manager_login_logs',
        help_text='Staff member who performed the login'
    )
    login_time = models.DateTimeField(
        help_text='Timestamp when the manager logged in'
    )
    logout_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when the manager logged out'
    )
    ip_address = models.GenericIPAddressField(
        help_text='IP address from which the login originated'
    )
    user_agent = models.TextField(
        help_text='Browser and device information'
    )
    session_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Session duration in minutes'
    )
    is_active_session = models.BooleanField(
        default=True,
        help_text='Whether this session is currently active'
    )
    
    class Meta:
        verbose_name = 'Manager Login Log'
        verbose_name_plural = 'Manager Login Logs'
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', '-login_time']),
            models.Index(fields=['-login_time']),
            models.Index(fields=['is_active_session']),
        ]
    
    def __str__(self):
        """
        Returns string representation of the login log.
        
        Returns:
            str: User and login time
        """
        return f"{self.user.username} - {self.login_time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def calculate_session_duration(self):
        """
        Calculate and update the session duration.
        
        This method calculates the duration between login_time and logout_time
        and updates the session_duration field.
        """
        if self.logout_time and self.login_time:
            duration = self.logout_time - self.login_time
            self.session_duration = int(duration.total_seconds() / 60)  # Convert to minutes
            self.save()
    
    def end_session(self):
        """
        End the current session by setting logout_time and calculating duration.
        
        This method should be called when a manager logs out or when the session expires.
        """
        from django.utils import timezone
        self.logout_time = timezone.now()
        self.is_active_session = False
        self.calculate_session_duration()
    
    @classmethod
    def log_login(cls, user, request):
        """
        Create a new login log entry.
        
        Args:
            user (User): The staff user who logged in
            request (HttpRequest): The current request object
            
        Returns:
            ManagerLoginLog: The created log entry
        """
        from django.utils import timezone
        
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        return cls.objects.create(
            user=user,
            login_time=timezone.now(),
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def get_active_sessions(cls):
        """
        Get all currently active manager sessions.
        
        Returns:
            QuerySet: Active login sessions
        """
        return cls.objects.filter(is_active_session=True)
    
    @classmethod
    def get_user_login_history(cls, user, limit=50):
        """
        Get login history for a specific user.
        
        Args:
            user (User): The user to get history for
            limit (int): Maximum number of records to return
            
        Returns:
            QuerySet: User's login history
        """
        return cls.objects.filter(user=user).order_by('-login_time')[:limit]


class MarketingCampaign(TimeStampedModel):
    """
    Represents a marketing email campaign created by a restaurant.
    
    This model allows restaurant owners to create and manage promotional email
    campaigns targeting customers who have ordered from their restaurant.
    
    Fields:
        restaurant: ForeignKey to Restaurant (campaign creator)
        name: Campaign name for identification
        subject: Email subject line
        template: Email template to use
        message: Custom email message content
        status: Campaign status (draft, scheduled, sent, completed)
        target_customers: Type of customers to target
        scheduled_at: When to send the campaign
        sent_at: When the campaign was actually sent
        created_by: User who created the campaign
    """
    
    CAMPAIGN_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    TARGET_CHOICES = [
        ('all_customers', 'All Customers'),
        ('recent_customers', 'Recent Customers (Last 30 Days)'),
        ('repeat_customers', 'Repeat Customers (3+ Orders)'),
        ('high_value_customers', 'High Value Customers (Avg Order > ₹500)'),
        ('inactive_customers', 'Inactive Customers (No Orders in 60 Days)'),
    ]
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='marketing_campaigns',
        help_text='Restaurant creating this campaign'
    )
    name = models.CharField(
        max_length=200,
        help_text='Campaign name for internal reference'
    )
    subject = models.CharField(
        max_length=200,
        help_text='Email subject line for customers'
    )
    template = models.CharField(
        max_length=100,
        default='emails/promotional_base.html',
        help_text='Email template to use for this campaign'
    )
    message = models.TextField(
        help_text='Custom message content for the email'
    )
    status = models.CharField(
        max_length=20,
        choices=CAMPAIGN_STATUS_CHOICES,
        default='draft',
        help_text='Current status of the campaign'
    )
    target_customers = models.CharField(
        max_length=30,
        choices=TARGET_CHOICES,
        default='all_customers',
        help_text='Which customer segment to target'
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When to schedule the campaign for sending'
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the campaign was actually sent'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_campaigns',
        help_text='User who created this campaign'
    )
    
    class Meta:
        verbose_name = 'Marketing Campaign'
        verbose_name_plural = 'Marketing Campaigns'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_at']),
        ]
    
    def __str__(self):
        """
        Returns string representation of the marketing campaign.
        
        Returns:
            str: Campaign name and restaurant
        """
        return f"{self.name} - {self.restaurant.name}"
    
    def get_target_customers(self):
        """
        Get the list of target customers based on the target_customers choice.
        
        Returns:
            QuerySet: Users who match the targeting criteria and have opted in
        """
        from orders.models import OrderItem
        from django.db.models import Count, Avg, Sum, Q
        from datetime import datetime, timedelta
        from customer.models import EmailPreference
        
        # Base query: users who have ordered from this restaurant and opted in for promotional emails
        base_customers = User.objects.filter(
            orders__items__menu_item__restaurant=self.restaurant,
            email_preferences__promotional_emails=True
        ).distinct()
        
        # Apply targeting filter
        if self.target_customers == 'all_customers':
            return base_customers
            
        elif self.target_customers == 'recent_customers':
            # Customers who ordered in last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            return base_customers.filter(
                orders__created_at__gte=thirty_days_ago
            ).distinct()
            
        elif self.target_customers == 'repeat_customers':
            # Customers with 3 or more orders
            return base_customers.annotate(
                order_count=Count('orders')
            ).filter(order_count__gte=3)
            
        elif self.target_customers == 'high_value_customers':
            # Customers with average order value > 500
            return base_customers.annotate(
                avg_order=Avg('orders__total_amount')
            ).filter(avg_order__gt=500)
            
        elif self.target_customers == 'inactive_customers':
            # Customers who haven't ordered in 60 days
            sixty_days_ago = datetime.now() - timedelta(days=60)
            return base_customers.filter(
                orders__created_at__lt=sixty_days_ago
            ).distinct()
            
        else:
            return User.objects.none()
    
    def get_campaign_stats(self):
        """
        Get campaign statistics.
        
        Returns:
            dict: Campaign statistics including target count, sent count, etc.
        """
        target_customers = self.get_target_customers()
        recipients = self.recipients.all()
        
        return {
            'target_count': target_customers.count(),
            'sent_count': recipients.filter(status='sent').count(),
            'failed_count': recipients.filter(status='failed').count(),
            'pending_count': recipients.filter(status='pending').count(),
            'success_rate': (recipients.filter(status='sent').count() / max(recipients.count(), 1)) * 100
        }
    
    def send_campaign(self):
        """
        Send the campaign to all target customers.
        
        This method creates CampaignRecipient records for each target customer
        and triggers the email sending process.
        """
        from core.utils import EmailUtils
        from django.utils import timezone
        
        if self.status != 'draft':
            raise ValueError("Only draft campaigns can be sent")
        
        # Update status to sending
        self.status = 'sending'
        self.save()
        
        # Get target customers
        target_customers = self.get_target_customers()
        
        # Create recipient records
        recipients = []
        for customer in target_customers:
            recipient = CampaignRecipient.objects.create(
                campaign=self,
                customer=customer,
                email=customer.email,
                status='pending'
            )
            recipients.append(recipient)
        
        # Prepare email context
        context = {
            'restaurant': self.restaurant,
            'campaign_name': self.name,
            'custom_message': self.message,
            'site_name': 'Food Ordering System',
            'site_url': 'https://tetech.in/',
            'site_domain': 'tetech.in',
            'current_year': timezone.now().year,
        }
        
        # Send emails
        results = EmailUtils.send_promotional_email(
            subject=self.subject,
            template_name=self.template,
            context=context,
            user_list=target_customers,
            fail_silently=True,
        )
        
        # Update recipient statuses
        sent_count = 0
        failed_count = 0
        
        for recipient in recipients:
            if recipient.customer.email in results['failed']:
                recipient.status = 'failed'
                recipient.error_message = 'Email sending failed'
                failed_count += 1
            else:
                recipient.status = 'sent'
                recipient.sent_at = timezone.now()
                sent_count += 1
            recipient.save()
        
        # Update campaign status
        self.status = 'sent' if sent_count > 0 else 'failed'
        self.sent_at = timezone.now()
        self.save()
        
        return {
            'sent': sent_count,
            'failed': failed_count,
            'total': len(recipients)
        }


class CampaignRecipient(TimeStampedModel):
    """
    Represents a recipient of a marketing campaign.
    
    This model tracks the status of each email sent as part of a campaign,
    allowing for detailed reporting and analytics.
    
    Fields:
        campaign: ForeignKey to MarketingCampaign
        customer: ForeignKey to User (recipient)
        email: Email address used for sending
        status: Delivery status
        sent_at: When the email was sent
        error_message: Any error that occurred during sending
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
    ]
    
    campaign = models.ForeignKey(
        MarketingCampaign,
        on_delete=models.CASCADE,
        related_name='recipients',
        help_text='Campaign this recipient belongs to'
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='campaign_recipients',
        help_text='Customer who received the email'
    )
    email = models.EmailField(
        help_text='Email address used for sending'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Current delivery status'
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the email was successfully sent'
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text='Error message if sending failed'
    )
    
    class Meta:
        verbose_name = 'Campaign Recipient'
        verbose_name_plural = 'Campaign Recipients'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
        ]
        unique_together = ['campaign', 'customer']
    
    def __str__(self):
        """
        Returns string representation of the campaign recipient.
        
        Returns:
            str: Customer email and campaign name
        """
        return f"{self.customer.email} - {self.campaign.name}"


class RestaurantTable(TimeStampedModel):
    """
    Represents a physical table in a restaurant for QR code menu ordering.
    
    This model manages individual tables within a restaurant, generates unique
    QR codes for each table, and tracks table status and capacity.
    
    Fields:
        restaurant: ForeignKey to Restaurant (which restaurant owns this table)
        table_number: Unique table identifier within the restaurant
        capacity: Number of seats at this table
        qr_code: Generated QR code image for this table
        qr_code_uuid: Unique UUID for QR code URL generation
        is_active: Whether this table is currently active
        location_description: Optional description of table location (e.g., "Near window", "Corner booth")
    
    Methods:
        generate_qr_code(): Generates QR code image for this table
        get_qr_code_url(): Returns the URL that QR code should point to
        get_menu_url(): Returns the full menu URL for this table
    """
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='tables',
        help_text='Restaurant that owns this table'
    )
    table_number = models.CharField(
        max_length=20,
        help_text='Table number or identifier (e.g., "T1", "A-5", "101")'
    )
    capacity = models.PositiveIntegerField(
        default=4,
        help_text='Number of people this table can accommodate'
    )
    qr_code = models.ImageField(
        upload_to='table_qr_codes/',
        blank=True,
        null=True,
        help_text='Generated QR code image for this table'
    )
    qr_code_uuid = models.UUIDField(
        unique=True,
        help_text='Unique identifier for QR code URL'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this table is currently active and available'
    )
    location_description = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Optional description of table location (e.g., "Near window", "Patio area")'
    )
    section = models.CharField(
        max_length=20,
        choices=[
            ('ac', 'A/C'),
            ('non_ac', 'Non A/C'),
            ('bar', 'Bar'),
        ],
        default='ac',
        help_text='Restaurant section where this table is located'
    )
    
    class Meta:
        verbose_name = 'Restaurant Table'
        verbose_name_plural = 'Restaurant Tables'
        ordering = ['restaurant', 'table_number']
        unique_together = ['restaurant', 'table_number']
        indexes = [
            models.Index(fields=['restaurant', 'table_number']),
            models.Index(fields=['qr_code_uuid']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        """
        Returns string representation of the table.
        
        Returns:
            str: Restaurant name and table number
        """
        return f"{self.restaurant.name} - Table {self.table_number}"
    
    def save(self, *args, **kwargs):
        """
        Override save method to generate UUID and QR code on creation.
        
        This method automatically generates a unique UUID for the table
        if one doesn't exist, which is used for QR code URL generation.
        """
        import uuid
        
        # Generate UUID if not exists
        if not self.qr_code_uuid:
            self.qr_code_uuid = uuid.uuid4()
        
        super().save(*args, **kwargs)
        
        # Generate QR code after saving (so we have an ID)
        if not self.qr_code:
            self.generate_qr_code()
    
    def get_menu_url(self):
        """
        Get the full menu URL for this table that QR code will point to.
        
        This URL includes the table's unique UUID which identifies the table
        and restaurant when customers scan the QR code.
        
        Returns:
            str: Full URL for table menu page
        """
        from django.urls import reverse
        from django.contrib.sites.models import Site
        
        try:
            # Get current site domain
            current_site = Site.objects.get_current()
            domain = current_site.domain
            protocol = 'https' if domain != 'localhost' and domain != '127.0.0.1' else 'http'
        except:
            # Fallback to default domain
            domain = 'localhost:8000'
            protocol = 'http'
        
        # Generate URL path using UUID
        path = reverse('customer:table_menu', kwargs={'uuid': str(self.qr_code_uuid)})
        
        return f"{protocol}://{domain}{path}"
    
    def generate_qr_code(self):
        """
        Generate QR code image for this table.
        
        This method creates a QR code that points to the table's menu URL.
        The QR code is saved as an image file in the media directory.
        
        Uses the qrcode library to generate the QR code image with
        optimal settings for restaurant menu scanning.
        
        Returns:
            bool: True if QR code was generated successfully, False otherwise
        """
        try:
            import qrcode
            from io import BytesIO
            from django.core.files import File
            from PIL import Image, ImageDraw, ImageFont
            
            # Get the menu URL for this table
            menu_url = self.get_menu_url()
            
            # Create QR code instance with optimal settings
            qr = qrcode.QRCode(
                version=1,  # Controls QR code size (1 is smallest, 40 is largest)
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction for damaged codes
                box_size=10,  # Size of each box in pixels
                border=4,  # Border size (minimum is 4)
            )
            
            # Add data to QR code
            qr.add_data(menu_url)
            qr.make(fit=True)
            
            # Create QR code image with white background
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to RGB mode for consistency
            qr_image = qr_image.convert('RGB')
            
            # Create a new image with extra space for text
            img_width, img_height = qr_image.size
            final_height = img_height + 60  # Add space for text
            final_image = Image.new('RGB', (img_width, final_height), 'white')
            
            # Paste QR code onto final image
            final_image.paste(qr_image, (0, 0))
            
            # Add text below QR code
            draw = ImageDraw.Draw(final_image)
            text = f"Table {self.table_number}"
            restaurant_text = self.restaurant.name
            
            # Try to use a font, fallback to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 20)
                small_font = ImageFont.truetype("arial.ttf", 14)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Calculate text position (centered)
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (img_width - text_width) // 2
            text_y = img_height + 10
            
            # Draw table number
            draw.text((text_x, text_y), text, fill='black', font=font)
            
            # Draw restaurant name
            rest_bbox = draw.textbbox((0, 0), restaurant_text, font=small_font)
            rest_width = rest_bbox[2] - rest_bbox[0]
            rest_x = (img_width - rest_width) // 2
            rest_y = text_y + 30
            draw.text((rest_x, rest_y), restaurant_text, fill='gray', font=small_font)
            
            # Save to BytesIO
            buffer = BytesIO()
            final_image.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Save to model field
            filename = f'table_{self.restaurant.id}_{self.table_number}_{self.qr_code_uuid}.png'
            self.qr_code.save(filename, File(buffer), save=True)
            
            return True
            
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return False
    
    def regenerate_qr_code(self):
        """
        Regenerate QR code for this table.
        
        This method deletes the existing QR code and generates a new one.
        Useful when table details change or QR code needs to be updated.
        
        Returns:
            bool: True if regeneration was successful, False otherwise
        """
        # Delete old QR code if exists
        if self.qr_code:
            try:
                import os
                if os.path.exists(self.qr_code.path):
                    os.remove(self.qr_code.path)
            except Exception as e:
                print(f"Error deleting old QR code: {e}")
        
        # Clear the field
        self.qr_code = None
        self.save(update_fields=['qr_code'])
        
        # Generate new QR code
        return self.generate_qr_code()
    
    @classmethod
    def get_table_by_uuid(cls, uuid):
        """
        Retrieve a table by its QR code UUID.
        
        This method is used when a customer scans a QR code to find
        the corresponding table and restaurant.
        
        Args:
            uuid (str or UUID): The unique identifier from the QR code
            
        Returns:
            RestaurantTable: The table object or None if not found
        """
        try:
            return cls.objects.select_related('restaurant').get(
                qr_code_uuid=uuid,
                is_active=True
            )
        except cls.DoesNotExist:
            return None
    
    def get_stats(self):
        """
        Get statistics for this table (orders, revenue, etc.).
        
        Returns:
            dict: Dictionary containing table statistics
        """
        from orders.models import Order
        from django.db.models import Sum, Count, Avg
        
        # Get orders for this table (if we track table in orders)
        # For now, return basic info
        return {
            'table_number': self.table_number,
            'capacity': self.capacity,
            'is_active': self.is_active,
            'restaurant': self.restaurant.name,
        }
