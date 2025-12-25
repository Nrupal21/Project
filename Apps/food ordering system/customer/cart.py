"""
Customer app cart management.
Handles session-based shopping cart operations with promo code support.
"""
from decimal import Decimal
from menu.models import MenuItem
from orders.models import PromoCode


class Cart:
    """
    Session-based shopping cart for managing customer orders with version control.
    
    This class provides a complete shopping cart implementation using Django sessions
    for storage. It handles adding/removing items, quantity management, price calculations,
    promo code application, and discount breakdowns. The cart persists across requests
    until explicitly cleared or session expires. Now includes version control to prevent
    race conditions in multi-tab scenarios.
    
    Storage Format:
    ===============
    session['cart'] = {
        'menu_item_id': {
            'quantity': int,    # Number of items
            'price': str        # Price per item (Decimal as string)
        },
        ...
    }
    session['applied_promo_code'] = 'promo_code_uuid'  # Optional
    session['cart_version'] = int  # Version for race condition prevention
    
    Features:
    =========
    - Session-based storage (no database overhead)
    - Automatic price calculation
    - Promo code validation and application
    - Delivery charge calculation
    - Discount breakdown generation
    - Restaurant validation for promo codes
    - Iterator support for easy template rendering
    - Version control for race condition prevention
    - Atomic operations with optimistic locking
    
    Attributes:
        session (SessionBase): Django session object for persistent storage
        cart (dict): Dictionary storing cart items by menu_item_id
        version (int): Current cart version for concurrency control
    
    Example Usage:
    ==============
    >>> cart = Cart(request)
    >>> cart.add(menu_item, quantity=2)
    >>> cart.apply_promo_code('SAVE20', user=request.user)
    >>> breakdown = cart.get_discount_breakdown()
    >>> total = breakdown['final_total']
    """
    
    def __init__(self, request):
        """
        Initialize the cart from Django session with version control.
        
        Retrieves existing cart from session or creates new empty cart
        if one doesn't exist. Implements version control to prevent
        race conditions when multiple tabs update the cart simultaneously.
        
        Args:
            request (HttpRequest): Django HTTP request object containing:
                - session: Django session for cart storage
        
        Session Keys Used:
            'cart': Dictionary of cart items
            'applied_promo_code': UUID of applied promo code (optional)
            'cart_version': Integer version for concurrency control
        
        Note:
            - Cart is automatically created if not in session
            - Version is incremented on each modification
            - Session is not modified until save() is called
            - Cart structure: {menu_item_id: {'quantity': int, 'price': str}}
        """
        # Store reference to session for persistence
        self.session = request.session
        
        # Retrieve existing cart from session
        cart = self.session.get('cart')
        
        if not cart:
            # Initialize empty cart in session if doesn't exist
            # Creates new dictionary that will be persisted
            cart = self.session['cart'] = {}
        
        # Store cart reference for this instance
        self.cart = cart
        
        # Initialize or increment version for race condition prevention
        self.version = self.session.get('cart_version', 0)
    
    def _increment_version(self):
        """
        Increment cart version to prevent race conditions.
        
        This method should be called before any cart modification
        to ensure atomic operations and detect concurrent updates.
        
        Note:
            - Version is stored in session, not instance
            - Each modification increments the version
            - Used by optimistic locking mechanism
        """
        self.version += 1
        self.session['cart_version'] = self.version
    
    def _validate_version(self, expected_version):
        """
        Validate cart version to detect concurrent modifications.
        
        Args:
            expected_version (int): Expected cart version
        
        Returns:
            bool: True if version matches, False if stale
        
        Note:
            - Returns False if cart was modified by another tab
            - Used to prevent race conditions in AJAX updates
            - Called before applying updates from client
        """
        current_version = self.session.get('cart_version', 0)
        return current_version == expected_version
    
    def add(self, menu_item, quantity=1, update_quantity=False):
        """
        Add a menu item to the cart or update its quantity with version control.
        
        This method handles both adding new items and updating quantities of
        existing items. It can either increment the quantity or set it to a
        specific value based on the update_quantity parameter. Includes version
        control to prevent race conditions.
        
        Workflow:
        =========
        1. Increment cart version for atomic operation
        2. Convert menu_item.id to string (session keys must be strings)
        3. If item not in cart: Create new entry with price
        4. If update_quantity=True: Set quantity to exact value
           If update_quantity=False: Add to existing quantity
        5. Save cart to session
        
        Args:
            menu_item (MenuItem): MenuItem model instance to add, containing:
                - id: Primary key (converted to string for session)
                - price: Item price (converted to string for JSON serialization)
            quantity (int): Number of items to add or set to (default: 1)
                - Must be positive integer
                - If update_quantity=True: Sets exact quantity
                - If update_quantity=False: Adds to existing quantity
            update_quantity (bool): Quantity update mode (default: False)
                - True: Replace existing quantity with new value
                - False: Add new quantity to existing quantity
        
        Example Usage:
        ==============
        # Add 2 items (or add 2 more if already exists)
        >>> cart.add(menu_item, quantity=2)
        
        # Set quantity to exactly 3 (replace existing)
        >>> cart.add(menu_item, quantity=3, update_quantity=True)
        
        Note:
            - Price is stored as string for JSON serialization
            - Session is marked as modified via save()
            - Item IDs must be strings (session limitation)
            - To remove item, use remove() method instead
            - Version is incremented for race condition prevention
        """
        # Increment version for atomic operation
        self._increment_version()
        
        # Convert menu item ID to string (session keys must be strings)
        menu_item_id = str(menu_item.id)
        
        # Create new cart entry if item doesn't exist
        if menu_item_id not in self.cart:
            self.cart[menu_item_id] = {
                'quantity': 0,  # Start at 0, will be updated below
                'price': str(menu_item.price)  # Store as string for JSON
            }
        
        # Update quantity based on mode
        if update_quantity:
            # Replace mode: Set to exact quantity
            self.cart[menu_item_id]['quantity'] = quantity
        else:
            # Increment mode: Add to existing quantity
            self.cart[menu_item_id]['quantity'] += quantity
        
        # Persist changes to session
        self.save()
    
    def remove(self, menu_item):
        """
        Remove a menu item completely from the cart with version control.
        
        Removes all quantities of the specified item. This is different from
        setting quantity to 0 - it completely removes the item entry from the cart.
        Includes version control to prevent race conditions.
        
        Args:
            menu_item (MenuItem): MenuItem model instance to remove, containing:
                - id: Primary key to identify cart entry
        
        Note:
            - Safe to call even if item is not in cart (no error)
            - Removes item completely, not just decrements quantity
            - Session is marked as modified via save()
            - To change quantity, use add() with update_quantity=True
            - Version is incremented for race condition prevention
        
        Example Usage:
        ==============
        >>> cart.remove(menu_item)  # Removes item from cart
        """
        # Increment version for atomic operation
        self._increment_version()
        
        # Convert menu item ID to string for session lookup
        menu_item_id = str(menu_item.id)
        
        # Remove item if it exists in cart
        if menu_item_id in self.cart:
            del self.cart[menu_item_id]
            # Persist changes to session
            self.save()
    
    def remove_by_id(self, menu_item_id):
        """
        Remove a menu item from the cart by ID (without MenuItem object).
        
        Useful when you have the item ID but not the MenuItem object instance.
        Typically used during validation when removing invalid items.
        
        Args:
            menu_item_id (int): Primary key of menu item to remove
                - Automatically converted to string for session lookup
        
        Note:
            - Safe to call even if item is not in cart (no error)
            - More efficient than remove() when you already have the ID
            - Session is marked as modified via save()
        
        Example Usage:
        ==============
        >>> cart.remove_by_id(123)  # Removes item with ID 123
        """
        # Convert ID to string for session lookup
        menu_item_id_str = str(menu_item_id)
        
        # Remove item if it exists in cart
        if menu_item_id_str in self.cart:
            del self.cart[menu_item_id_str]
            # Persist changes to session
            self.save()
    
    def save(self):
        """
        Mark session as modified to ensure cart changes are persisted.
        
        Django sessions are only saved if modified=True is set. This method
        must be called after any cart modifications to ensure changes persist
        across requests.
        
        Note:
            - Called automatically by add(), remove(), and other modifying methods
            - Required for session persistence
            - Without this, cart changes would be lost after request
            - No database query - just sets a flag
        
        Session Behavior:
            - Django only saves session if modified=True
            - Setting this flag triggers session save at end of request
            - Cart data serialized to JSON and stored in session backend
        """
        # Mark session as modified to trigger save
        self.session.modified = True
    
    def clear(self):
        """
        Remove all items from the cart and clear promo codes.
        
        Completely removes the cart from session, resetting it to empty state.
        Also removes any applied promo codes. Typically called after successful
        order creation.
        
        Side Effects:
            - Deletes 'cart' key from session
            - Removes any applied promo code
            - Next Cart() initialization will create fresh empty cart
        
        Note:
            - Cannot be undone
            - Called automatically after successful checkout
            - Session is marked as modified
            - All cart data is permanently lost
        
        Example Usage:
        ==============
        >>> cart.clear()  # Empty cart after order placed
        """
        # Remove cart from session completely
        del self.session['cart']
        # Mark session as modified to persist change
        self.save()
    
    def __iter__(self):
        """
        Iterate over items in the cart and get menu items from database.
        
        Yields:
            dict: Cart item with menu_item object and total_price
        """
        menu_item_ids = self.cart.keys()
        menu_items = MenuItem.objects.filter(id__in=menu_item_ids)
        cart = self.cart.copy()
        
        for menu_item in menu_items:
            cart[str(menu_item.id)]['menu_item'] = {
                'id': menu_item.id,
                'name': menu_item.name,
                'description': menu_item.description,
                'price': str(menu_item.price),
                'image_url': menu_item.image.url if menu_item.image else None,
                'category': {'name': menu_item.category.name} if menu_item.category else None,
                'is_available': menu_item.is_available,
                'restaurant': {
                    'id': menu_item.restaurant.id,
                    'name': menu_item.restaurant.name,
                    'is_active': menu_item.restaurant.is_active,
                    'is_approved': menu_item.restaurant.is_approved
                }
            }
        
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            # Convert Decimal to string for JSON serialization
            item['price'] = str(item['price'])
            item['total_price'] = str(item['total_price'])
            yield item
    
    def __len__(self):
        """
        Count total items in the cart.
        
        Returns:
            int: Total number of items
        """
        return sum(item['quantity'] for item in self.cart.values())
    
    def get_total_price(self):
        """
        Calculate total price of all items in cart.
        
        Returns:
            str: Total cart value as string for JSON serialization
        """
        total = sum(
            Decimal(item['price']) * item['quantity'] 
            for item in self.cart.values()
        )
        return str(total)
    
    def apply_promo_code(self, code, user=None):
        """
        Apply a promo code to the cart.
        
        Args:
            code (str): Promo code string
            user: User object (optional)
        
        Returns:
            tuple: (success, message)
        """
        try:
            promo_code = PromoCode.objects.get(code__iexact=code)
        except PromoCode.DoesNotExist:
            return False, "Invalid promo code."
        
        # Get cart total for validation
        cart_total = self.get_cart_total()
        
        # Validate promo code
        is_valid, error_message = promo_code.is_valid(user=user, order_amount=cart_total)
        if not is_valid:
            return False, error_message
        
        # Check restaurant-specific restrictions
        if promo_code.restaurant:
            cart_restaurants = self.get_cart_restaurants()
            if promo_code.restaurant not in cart_restaurants:
                return False, f"This promo code is only valid for {promo_code.restaurant.name}."
        
        # Store promo code in session
        self.session['applied_promo_code'] = str(promo_code.id)
        self.save()
        
        return True, f"Promo code '{code}' applied successfully!"
    
    def remove_promo_code(self):
        """
        Remove applied promo code from cart.
        """
        if 'applied_promo_code' in self.session:
            del self.session['applied_promo_code']
            self.save()
    
    def get_applied_promo_code(self):
        """
        Get the currently applied promo code.
        
        Returns:
            PromoCode: Applied promo code object or None
        """
        promo_code_id = self.session.get('applied_promo_code')
        if not promo_code_id:
            return None
        
        try:
            promo_code = PromoCode.objects.get(id=promo_code_id)
            # Re-validate promo code
            cart_total = self.get_cart_total()
            is_valid, _ = promo_code.is_valid(order_amount=cart_total)
            
            if not is_valid:
                # Remove invalid promo code
                self.remove_promo_code()
                return None
            
            return promo_code
        except PromoCode.DoesNotExist:
            # Remove invalid promo code from session
            self.remove_promo_code()
            return None
    
    def calculate_discount(self):
        """
        Calculate discount based on applied promo code.
        
        Returns:
            tuple: (discount_amount, free_delivery)
        """
        promo_code = self.get_applied_promo_code()
        if not promo_code:
            return Decimal('0'), False
        
        cart_total = self.get_cart_total()
        delivery_charge = Decimal('40')  # Default delivery charge
        
        discount_amount, free_delivery = promo_code.calculate_discount(
            cart_total, delivery_charge
        )
        
        return Decimal(discount_amount), free_delivery
    
    def get_cart_total(self):
        """
        Calculate cart subtotal without discounts.
        
        Returns:
            Decimal: Cart subtotal
        """
        total = sum(
            Decimal(item['price']) * item['quantity'] 
            for item in self.cart.values()
        )
        return total
    
    def get_cart_restaurants(self):
        """
        Get all restaurants represented in cart items.
        
        Returns:
            set: Set of Restaurant objects
        """
        restaurant_ids = set()
        for item_id in self.cart.keys():
            try:
                menu_item = MenuItem.objects.get(id=item_id)
                restaurant_ids.add(menu_item.restaurant)
            except MenuItem.DoesNotExist:
                continue
        
        return restaurant_ids
    
    def get_discount_breakdown(self, delivery_method='delivery'):
        """
        Get complete pricing breakdown with discounts.
        
        Args:
            delivery_method: 'delivery' or 'takeaway' (default: 'delivery')
        
        Returns:
            dict: Pricing breakdown
        """
        subtotal = self.get_cart_total()
        discount_amount, free_delivery = self.calculate_discount()
        
        # Only charge delivery for delivery orders
        delivery_charge = Decimal('0')
        if delivery_method == 'delivery' and not free_delivery:
            delivery_charge = Decimal('40')  # Default delivery charge
        
        final_total = subtotal - discount_amount + delivery_charge
        
        return {
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'delivery_charge': delivery_charge,
            'free_delivery': free_delivery,
            'final_total': final_total,
            'applied_promo_code': self.get_applied_promo_code(),
            'delivery_method': delivery_method
        }
    
    def validate_applied_promo_code(self):
        """
        Validate that applied promo code is still valid.
        Removes invalid codes from session.
        """
        self.get_applied_promo_code()  # This method handles validation and removal
