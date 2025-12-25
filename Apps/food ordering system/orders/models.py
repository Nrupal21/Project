"""
Orders app models.
Defines Order and OrderItem models for managing customer orders.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.functional import cached_property
from core.models import TimeStampedModel
from menu.models import MenuItem
import uuid


class Order(TimeStampedModel):
    """
    Represents a customer order.
    
    Fields:
        order_id: Unique identifier for the order (UUID)
        customer_name: Name of the customer placing the order
        customer_phone: Customer's phone number
        customer_address: Delivery address
        total_amount: Total order value
        status: Current order status
        notes: Additional instructions or notes
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('preparing', 'Preparing'),
        ('serving', 'Serving'),  # New status for table orders - food is being served to customers
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    DELIVERY_CHOICES = [
        ('delivery', 'Delivery'),
        ('takeaway', 'Takeaway'),
        ('dine_in', 'Dine In'),
    ]
    
    ORDER_TYPE_CHOICES = [
        ('qr_code', 'QR Code Order'),
        ('dine_in', 'Dine In'),
        ('delivery', 'Delivery'),
        ('takeaway', 'Takeaway'),
        ('staff', 'Staff Order'),
    ]
    
    DELIVERY_TIME_CHOICES = [
        ('asap', 'ASAP (25-35 min)'),
        ('30min', '30 minutes'),
        ('1hr', '1 hour'),
        ('2hr', '2 hours'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('online', 'Online Payment'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order_id = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # Keep order even if user is deleted
        null=True,
        blank=True,
        related_name='orders'
    )
    
    # Table and order type tracking for QR code orders and dine-in
    table = models.ForeignKey(
        'restaurant.RestaurantTable',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text='Table from which this order was placed (for QR code and dine-in orders)'
    )
    order_type = models.CharField(
        max_length=20,
        choices=ORDER_TYPE_CHOICES,
        default='delivery',
        help_text='Type of order: QR code, dine-in, delivery, takeaway, or staff order'
    )
    is_table_order = models.BooleanField(
        default=False,
        help_text='Quick flag to identify table-based orders (QR code or dine-in)'
    )
    
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=15)
    customer_address = models.TextField(blank=True, null=True)
    
    # Guest checkout fields for QR table ordering
    guest_email = models.EmailField(
        blank=True, 
        null=True,
        help_text='Guest email for bill delivery (QR table orders)'
    )
    guest_phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text='Guest phone for bill delivery (QR table orders)'
    )
    delivery_method = models.CharField(
        max_length=20,
        choices=DELIVERY_CHOICES,
        default='delivery'
    )
    delivery_time = models.CharField(
        max_length=10,
        choices=DELIVERY_TIME_CHOICES,
        default='asap',
        help_text='Preferred delivery time slot selected by customer'
    )
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    notes = models.TextField(blank=True, null=True)
    
    # Promo code and discount tracking
    promo_code = models.ForeignKey(
        'PromoCode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text='Promo code applied to this order'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Total discount amount applied to this order'
    )
    delivery_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Delivery charge for this order'
    )
    free_delivery_applied = models.BooleanField(
        default=False,
        help_text='Whether free delivery was applied via promo code'
    )
    
    # Payment tracking fields
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cod',
        help_text='Payment method selected by customer'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        help_text='Current payment status'
    )
    razorpay_order_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Razorpay order ID for online payments'
    )
    razorpay_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Razorpay payment ID after successful payment'
    )
    razorpay_signature = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Razorpay signature for payment verification'
    )
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
    
    def __str__(self):
        """
        Returns string representation of the order.
        
        Returns:
            str: Order ID with customer name
        """
        return f"Order #{str(self.order_id)[:8]} - {self.customer_name}"
    
    def get_status_display_class(self):
        """
        Returns Tailwind CSS class for status badge.
        
        Returns:
            str: CSS class for status styling
        """
        status_classes = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'accepted': 'bg-blue-100 text-blue-800',
            'preparing': 'bg-purple-100 text-purple-800',
            'out_for_delivery': 'bg-indigo-100 text-indigo-800',
            'delivered': 'bg-green-100 text-green-800',
            'cancelled': 'bg-red-100 text-red-800',
        }
        return status_classes.get(self.status, 'bg-gray-100 text-gray-800')
    
    def can_review_order(self):
        """
        Check if the current user can review this order.
        
        Returns:
            bool: True if order is delivered and user hasn't already reviewed it
        """
        if not self.user or self.status != 'delivered':
            return False
        
        # Get the restaurant from the first order item
        first_item = self.items.first()
        if not first_item:
            return False
        
        restaurant = first_item.menu_item.restaurant
        
        # Check if user already reviewed this restaurant
        from customer.models import RestaurantReview
        existing_review = RestaurantReview.objects.filter(
            user=self.user,
            order=self,
            restaurant=restaurant
        ).first()
        
        return existing_review is None
    
    def can_review_item(self, menu_item_id):
        """
        Check if the current user can review a specific menu item from this order.
        
        Args:
            menu_item_id (int): ID of the menu item to check
            
        Returns:
            bool: True if order is delivered, item is in order, and user hasn't already reviewed it
        """
        if not self.user or self.status != 'delivered':
            return False
        
        # Check if menu item is in this order
        item_exists = self.items.filter(menu_item_id=menu_item_id).exists()
        if not item_exists:
            return False
        
        # Check if user already reviewed this menu item
        from customer.models import MenuItemReview
        existing_review = MenuItemReview.objects.filter(
            user=self.user,
            order=self,
            menu_item_id=menu_item_id
        ).first()
        
        return existing_review is None
    
    def get_reviewable_items(self):
        """
        Get list of menu items from this order that can be reviewed by the user.
        
        Returns:
            QuerySet: Menu items that haven't been reviewed yet
        """
        if not self.user or self.status != 'delivered':
            return self.items.none()
        
        from customer.models import MenuItemReview
        
        # Get items that haven't been reviewed yet
        reviewed_item_ids = MenuItemReview.objects.filter(
            user=self.user,
            order=self
        ).values_list('menu_item_id', flat=True)
        
        return self.items.exclude(menu_item_id__in=reviewed_item_ids)


class OrderItem(TimeStampedModel):
    """
    Represents an individual item in an order.
    
    Fields:
        order: Foreign key to Order model
        menu_item: Foreign key to MenuItem model
        quantity: Number of items ordered
        price: Price per item at time of order
        subtotal: Calculated subtotal (quantity * price)
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    
    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
    
    def __str__(self):
        """
        Returns string representation of the order item.
        
        Returns:
            str: Menu item name with quantity
        """
        return f"{self.quantity}x {self.menu_item.name}"
    
    def get_total(self):
        """
        Calculate the total price for this order item.
        
        Returns:
            Decimal: Total price (quantity * price)
        """
        return self.subtotal
    
    def save(self, *args, **kwargs):
        """
        Override save method to calculate subtotal.
        Automatically calculates subtotal based on quantity and price.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        self.subtotal = self.quantity * self.price
        super().save(*args, **kwargs)


class PromoCode(models.Model):
    """
    Model for managing promotional codes and discounts.
    
    Supports various discount types including percentage off, fixed amount,
    and free delivery. Can be restaurant-specific or global.
    """
    
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage Off'),
        ('fixed', 'Fixed Amount Off'),
        ('free_delivery', 'Free Delivery'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Unique promo code that customers will enter'
    )
    name = models.CharField(
        max_length=100,
        help_text='Display name for the promo code'
    )
    description = models.TextField(
        blank=True,
        help_text='Description of the promo code for customers'
    )
    
    # Discount configuration
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPES,
        help_text='Type of discount to apply'
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Discount value (percentage or amount)'
    )
    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Minimum order amount required to use this promo code'
    )
    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='Maximum discount amount for percentage discounts'
    )
    
    # Usage limits
    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Maximum number of times this promo code can be used'
    )
    usage_limit_per_user = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Maximum times a single user can use this promo code'
    )
    
    # Time constraints
    start_date = models.DateTimeField(
        help_text='When the promo code becomes active'
    )
    end_date = models.DateTimeField(
        help_text='When the promo code expires'
    )
    
    # Targeting
    restaurant = models.ForeignKey(
        'restaurant.Restaurant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='promo_codes',
        help_text='Restaurant this promo code belongs to (null for global codes)'
    )
    first_time_only = models.BooleanField(
        default=False,
        help_text='Only for first-time customers'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this promo code is currently active'
    )
    
    # Tracking
    times_used = models.PositiveIntegerField(
        default=0,
        help_text='Total number of times this promo code has been used'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Promo Code'
        verbose_name_plural = 'Promo Codes'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['restaurant', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def clean(self):
        """Validate promo code configuration."""
        if self.start_date >= self.end_date:
            raise ValidationError('End date must be after start date.')
        
        if self.discount_type == 'percentage' and (self.discount_value < 0 or self.discount_value > 100):
            raise ValidationError('Percentage discount must be between 0 and 100.')
        
        if self.discount_type == 'fixed' and self.discount_value <= 0:
            raise ValidationError('Fixed discount amount must be greater than 0.')
        
        if self.discount_type == 'free_delivery' and self.discount_value != 0:
            raise ValidationError('Free delivery discount value must be 0.')
    
    def is_valid(self, user=None, order_amount=None):
        """
        Check if promo code is valid for use.
        
        Args:
            user: User trying to use the promo code
            order_amount: Current order amount
        
        Returns:
            tuple: (is_valid, error_message)
        """
        now = timezone.now()
        
        # Check if active
        if not self.is_active:
            return False, "This promo code is not active."
        
        # Check date range
        if now < self.start_date:
            return False, "This promo code is not yet active."
        if now > self.end_date:
            return False, "This promo code has expired."
        
        # Check usage limit
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False, "This promo code has reached its usage limit."
        
        # Check minimum order amount
        if order_amount and order_amount < self.minimum_order_amount:
            return False, f"Minimum order amount of ₹{self.minimum_order_amount} required."
        
        # Check first-time only restriction
        if self.first_time_only and user:
            if Order.objects.filter(user=user).exists():
                return False, "This promo code is for first-time customers only."
        
        # Check per-user usage limit
        if self.usage_limit_per_user and user:
            user_usage_count = PromoCodeUsage.objects.filter(
                promo_code=self,
                user=user
            ).count()
            if user_usage_count >= self.usage_limit_per_user:
                return False, f"You have reached the usage limit for this promo code ({self.usage_limit_per_user} times)."
        
        return True, ""
    
    def calculate_discount(self, order_amount, delivery_charge=0):
        """
        Calculate discount amount for given order.
        
        Args:
            order_amount: Order total amount
            delivery_charge: Delivery charge amount
        
        Returns:
            tuple: (discount_amount, free_delivery)
        """
        if self.discount_type == 'percentage':
            discount = order_amount * (self.discount_value / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return discount, False
        
        elif self.discount_type == 'fixed':
            return min(self.discount_value, order_amount), False
        
        elif self.discount_type == 'free_delivery':
            return 0, True
        
        return 0, False
    
    def increment_usage(self):
        """Increment the usage count for this promo code."""
        self.times_used += 1
        self.save(update_fields=['times_used'])


class PromoCodeUsage(models.Model):
    """
    Track individual promo code usage for analytics and limits.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.CASCADE,
        related_name='usages'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='promo_code_usages'
    )
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        related_name='promo_code_usage'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Amount of discount applied'
    )
    free_delivery_applied = models.BooleanField(
        default=False,
        help_text='Whether free delivery was applied'
    )
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-used_at']
        verbose_name = 'Promo Code Usage'
        verbose_name_plural = 'Promo Code Usages'
        unique_together = ['user', 'order']  # One promo code per order
        indexes = [
            models.Index(fields=['promo_code', 'user']),
            models.Index(fields=['used_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} used {self.promo_code.code} on {self.used_at.strftime('%Y-%m-%d')}"


class SeasonalPromotion(models.Model):
    """
    Model for managing seasonal promotions and flash sales.
    
    Automatically activates promo codes based on time schedules.
    """
    
    PROMOTION_TYPES = [
        ('seasonal', 'Seasonal Promotion'),
        ('flash_sale', 'Flash Sale'),
        ('holiday', 'Holiday Special'),
        ('event', 'Special Event'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPES)
    
    # Time scheduling
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Auto-generated promo codes
    auto_generate_codes = models.BooleanField(
        default=True,
        help_text='Automatically generate promo codes for this promotion'
    )
    code_prefix = models.CharField(
        max_length=10,
        help_text='Prefix for auto-generated promo codes'
    )
    
    # Promotion settings
    discount_type = models.CharField(
        max_length=20,
        choices=PromoCode.DISCOUNT_TYPES
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usage_limit_per_code = models.PositiveIntegerField(default=100)
    
    # Targeting
    restaurants = models.ManyToManyField(
        'restaurant.Restaurant',
        blank=True,
        help_text='Restaurants included in this promotion (empty = all restaurants)'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Seasonal Promotion'
        verbose_name_plural = 'Seasonal Promotions'
    
    def __str__(self):
        return f"{self.name} ({self.get_promotion_type_display()})"
    
    def is_current(self):
        """Check if promotion is currently active."""
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
    
    def generate_promo_codes(self, count=10):
        """Generate multiple promo codes for this promotion."""
        codes = []
        for i in range(count):
            code = f"{self.code_prefix}{str(i+1).zfill(3)}"
            promo = PromoCode.objects.create(
                code=code,
                name=f"{self.name} - Code {i+1}",
                description=self.description,
                discount_type=self.discount_type,
                discount_value=self.discount_value,
                minimum_order_amount=self.minimum_order_amount,
                usage_limit=self.usage_limit_per_code,
                start_date=self.start_date,
                end_date=self.end_date,
                is_active=True
            )
            codes.append(promo)
        return codes
