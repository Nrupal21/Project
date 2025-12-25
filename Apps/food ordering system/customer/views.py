"""
Customer app views.
Handles all customer-facing functionality including menu, cart, checkout,
user profile, restaurant upgrade, and comprehensive review system.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import models
from django.db.models import Q, Avg, Count
from django.urls import reverse, reverse_lazy
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from restaurant.models import Restaurant, PendingRestaurant
from .cart import Cart
from menu.models import MenuItem, Category
from orders.models import Order, OrderItem
from .forms import (
    CheckoutForm, RestaurantUpgradeForm, RestaurantReviewForm, 
    MenuItemReviewForm, ReviewResponseForm, ReviewFlagForm, UserProfileEditForm
)
from customer.models import RestaurantReview, MenuItemReview, ReviewResponse, ReviewFlag, Wishlist, UserProfile, LoyaltyTransaction
from core.payment_utils import create_razorpay_order


def send_order_confirmation_email(user, order):
    """
    Send order confirmation email to the user after successful order placement.
    
    This function constructs and sends a detailed order confirmation email
    containing all order information including items, pricing, delivery details,
    and customer information. Follows email best practices for transactional emails.
    
    Email Contents:
    ============================================
    - Personal greeting with user's name
    - Order ID for tracking
    - Order status and delivery method
    - Total amount charged
    - Customer contact information
    - Detailed list of ordered items with quantities and prices
    - Order notes/special instructions
    - Next steps and tracking information
    - Professional closing from team
    ============================================
    
    Args:
        user (User): Django User object who placed the order, containing:
            - email: Recipient email address
            - first_name: User's first name for personalization
            - username: Fallback if first name not available
        order (Order): Order object with complete order details, including:
            - order_id: Unique UUID for order tracking
            - status: Current order status
            - delivery_method: 'delivery' or 'takeaway'
            - total_amount: Final order total
            - customer_name: Customer's full name
            - customer_phone: Contact phone number
            - customer_address: Delivery address (or None for takeaway)
            - notes: Special instructions from customer
            - items: Related OrderItem queryset
    
    Returns:
        bool: True if email sent successfully, False if error occurred
    
    Raises:
        No exceptions raised - all errors are caught and logged
    
    Email Configuration:
        - Subject: "Order Confirmation - #[order_id]"
        - From: settings.DEFAULT_FROM_EMAIL
        - To: user.email
        - Format: Plain text (HTML version can be added later)
        - Character encoding: UTF-8
    
    Note:
        - Uses Django's send_mail() function
        - fail_silently=False to catch sending errors
        - All exceptions are caught and logged
        - Returns False on any error to allow graceful degradation
        - Email failure doesn't prevent order creation
        - Consider adding HTML template version for better formatting
    """
    try:
        # Construct email subject with order ID
        subject = f'Order Confirmation - #{order.order_id}'
        
        # Construct email body with order details
        # Uses multi-line string for better readability
        message = f"""
Dear {user.first_name or user.username},

Thank you for your order! Here are your order details:

Order ID: {order.order_id}
Order Status: {order.get_status_display()}
Delivery Method: {order.get_delivery_method_display()}
Total Amount: ₹{order.total_amount}

Customer Information:
Name: {order.customer_name}
Phone: {order.customer_phone}
Address: {order.customer_address or 'Takeaway order'}

Order Items:
"""
        
        # Append each order item with details
        # Format: "- [Item Name] x[Quantity] = ₹[Subtotal]"
        for item in order.items.all():
            message += f"- {item.menu_item.name} x{item.quantity} = ₹{item.price * item.quantity}\n"
        
        # Append additional information and closing
        message += f"""
Notes: {order.notes or 'None'}

We'll process your order shortly. You can track your order status on our website.

Best regards,
Tetech Food Ordering Team
"""
        
        # Send email using Django's send_mail function
        send_mail(
            subject,  # Email subject line
            message,  # Email body (plain text)
            settings.DEFAULT_FROM_EMAIL,  # From address
            [user.email],  # Recipient list
            fail_silently=False,  # Raise exception on errors
        )
        
        # Email sent successfully
        return True
        
    except Exception as e:
        # Log error for debugging and monitoring
        # Don't raise exception - allow order to complete
        print(f"Error sending order confirmation email: {e}")
        return False


def home(request):
    """
    Display the home page with featured restaurants and comprehensive search/filtering.
    
    Supports the following filtering and search options:
    - Search query: Search by restaurant name or description
    - Cuisine type: Filter by cuisine category
    - Price range: Filter by minimum order amount
    - Delivery fee: Filter by delivery cost
    - Rating: Filter by minimum rating
    - Sort options: Sort by rating, name, minimum order, or delivery fee
    
    Args:
        request: Django HTTP request object with GET parameters for filtering
    
    Returns:
        HttpResponse: Rendered home page template with filtered restaurants list
    """
    # Get base queryset of active and approved restaurants with review counts
    restaurants = Restaurant.objects.filter(is_active=True, is_approved=True).annotate(
        review_count=models.Count('reviews', distinct=True),
        avg_food_quality=Avg('reviews__food_quality'),
        avg_delivery_speed=Avg('reviews__delivery_speed'),
        avg_value_for_money=Avg('reviews__value_for_money')
    )
    
    # Get user's wishlist restaurants if authenticated
    user_wishlist_restaurants = []
    if request.user.is_authenticated:
        user_wishlist_restaurants = Wishlist.objects.filter(
            user=request.user
        ).values_list('restaurant_id', flat=True)
    
    # Get filter parameters from GET request
    search_query = request.GET.get('search', '').strip()
    cuisine_type = request.GET.get('cuisine', '')
    price_range = request.GET.get('price_range', '')
    delivery_fee = request.GET.get('delivery_fee', '')
    min_rating = request.GET.get('rating', '')
    sort_by = request.GET.get('sort', 'rating')
    
    # Apply search filter (search in name and description)
    if search_query:
        restaurants = restaurants.filter(
            models.Q(name__icontains=search_query) |
            models.Q(description__icontains=search_query)
        )
    
    # Apply cuisine type filter
    if cuisine_type:
        restaurants = restaurants.filter(cuisine_type=cuisine_type)
    
    # Apply price range filter (minimum order amount)
    if price_range:
        if price_range == 'low':
            restaurants = restaurants.filter(minimum_order__lte=100)
        elif price_range == 'medium':
            restaurants = restaurants.filter(minimum_order__gt=100, minimum_order__lte=200)
        elif price_range == 'high':
            restaurants = restaurants.filter(minimum_order__gt=200)
    
    # Apply delivery fee filter
    if delivery_fee:
        if delivery_fee == 'free':
            restaurants = restaurants.filter(delivery_fee=0)
        elif delivery_fee == 'low':
            restaurants = restaurants.filter(delivery_fee__gt=0, delivery_fee__lte=50)
        elif delivery_fee == 'medium':
            restaurants = restaurants.filter(delivery_fee__gt=50, delivery_fee__lte=100)
        elif delivery_fee == 'high':
            restaurants = restaurants.filter(delivery_fee__gt=100)
    
    # Apply rating filter
    if min_rating:
        try:
            rating_value = float(min_rating)
            restaurants = restaurants.filter(rating__gte=rating_value)
        except ValueError:
            pass
    
    # Apply sorting
    if sort_by == 'rating':
        restaurants = restaurants.order_by('-rating', 'name')
    elif sort_by == 'name':
        restaurants = restaurants.order_by('name')
    elif sort_by == 'min_order':
        restaurants = restaurants.order_by('minimum_order', 'name')
    elif sort_by == 'delivery_fee':
        restaurants = restaurants.order_by('delivery_fee', 'name')
    elif sort_by == 'newest':
        restaurants = restaurants.order_by('-created_at', 'name')
    else:
        restaurants = restaurants.order_by('-rating', 'name')
    
    # Get cuisine choices for filter dropdown
    cuisine_choices = Restaurant.CUISINE_CHOICES
    
    # Get popular menu items from all active restaurants
    # Limit to 20 items, ordered by a combination of price and availability
    popular_menu_items = MenuItem.objects.filter(
        restaurant__is_active=True,
        restaurant__is_approved=True,
        is_available=True
    ).select_related('restaurant', 'category').order_by('-price')[:20]
    
    # Debug: Print count of popular menu items
    print(f"DEBUG: Found {popular_menu_items.count()} popular menu items")
    print("DEBUG: Template should show popular dishes section")
    
    # Prepare context with filter values for template
    context = {
        'restaurants': restaurants,
        'popular_menu_items': popular_menu_items,
        'search_query': search_query,
        'selected_cuisine': cuisine_type,
        'selected_price_range': price_range,
        'selected_delivery_fee': delivery_fee,
        'selected_rating': min_rating,
        'selected_sort': sort_by,
        'cuisine_choices': cuisine_choices,
        'total_results': restaurants.count(),
        'user_wishlist_restaurants': list(user_wishlist_restaurants),
    }
    
    return render(request, 'customer/home.html', context)


def filter_results(request):
    """
    Display dedicated filter results page for restaurants with comprehensive filtering options.
    
    Supports the following filtering and search options:
    - Search query: Search by restaurant name or description
    - Cuisine type: Filter by cuisine category
    - Price range: Filter by minimum order amount
    - Delivery fee: Filter by delivery cost
    - Rating: Filter by minimum rating
    - Sort options: Sort by rating, name, minimum order, or delivery fee
    
    Args:
        request: Django HTTP request object with GET parameters for filtering
    
    Returns:
        HttpResponse: Rendered filter results page template with filtered restaurants list
    """
    # Get base queryset of active and approved restaurants with review counts
    restaurants = Restaurant.objects.filter(is_active=True, is_approved=True).annotate(
        review_count=models.Count('reviews', distinct=True),
        avg_food_quality=Avg('reviews__food_quality'),
        avg_delivery_speed=Avg('reviews__delivery_speed'),
        avg_value_for_money=Avg('reviews__value_for_money')
    )
    
    # Get user's wishlist restaurants if authenticated
    user_wishlist_restaurants = []
    if request.user.is_authenticated:
        user_wishlist_restaurants = Wishlist.objects.filter(
            user=request.user
        ).values_list('restaurant_id', flat=True)
    
    # Get filter parameters from GET request
    search_query = request.GET.get('search', '').strip()
    cuisine_type = request.GET.get('cuisine', '')
    price_range = request.GET.get('price_range', '')
    delivery_fee = request.GET.get('delivery_fee', '')
    min_rating = request.GET.get('rating', '')
    sort_by = request.GET.get('sort', 'rating')
    
    # Apply search filter (search in name and description)
    if search_query:
        restaurants = restaurants.filter(
            models.Q(name__icontains=search_query) |
            models.Q(description__icontains=search_query)
        )
    
    # Apply cuisine type filter
    if cuisine_type:
        restaurants = restaurants.filter(cuisine_type=cuisine_type)
    
    # Apply price range filter (minimum order amount)
    if price_range:
        if price_range == 'low':
            restaurants = restaurants.filter(minimum_order__lte=100)
        elif price_range == 'medium':
            restaurants = restaurants.filter(minimum_order__gt=100, minimum_order__lte=200)
        elif price_range == 'high':
            restaurants = restaurants.filter(minimum_order__gt=200)
    
    # Apply delivery fee filter
    if delivery_fee:
        if delivery_fee == 'free':
            restaurants = restaurants.filter(delivery_fee=0)
        elif delivery_fee == 'low':
            restaurants = restaurants.filter(delivery_fee__gt=0, delivery_fee__lte=50)
        elif delivery_fee == 'medium':
            restaurants = restaurants.filter(delivery_fee__gt=50, delivery_fee__lte=100)
        elif delivery_fee == 'high':
            restaurants = restaurants.filter(delivery_fee__gt=100)
    
    # Apply rating filter
    if min_rating:
        try:
            rating_value = float(min_rating)
            restaurants = restaurants.filter(rating__gte=rating_value)
        except ValueError:
            pass
    
    # Apply sorting
    if sort_by == 'rating':
        restaurants = restaurants.order_by('-rating', 'name')
    elif sort_by == 'name':
        restaurants = restaurants.order_by('name')
    elif sort_by == 'min_order':
        restaurants = restaurants.order_by('minimum_order', 'name')
    elif sort_by == 'delivery_fee':
        restaurants = restaurants.order_by('delivery_fee', 'name')
    elif sort_by == 'newest':
        restaurants = restaurants.order_by('-created_at', 'name')
    else:
        # Default sort by rating
        restaurants = restaurants.order_by('-rating', 'name')
    
    # Get cuisine choices for filter dropdown
    cuisine_choices = Restaurant.CUISINE_CHOICES
    
    # Pagination - show 12 restaurants per page
    paginator = Paginator(restaurants, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Prepare context with filter values for template
    context = {
        'restaurants': page_obj,
        'search_query': search_query,
        'selected_cuisine': cuisine_type,
        'selected_price_range': price_range,
        'selected_delivery_fee': delivery_fee,
        'selected_rating': min_rating,
        'selected_sort': sort_by,
        'cuisine_choices': cuisine_choices,
        'total_results': restaurants.count(),
        'user_wishlist_restaurants': list(user_wishlist_restaurants),
        'page_obj': page_obj,
    }
    
    return render(request, 'customer/filter_results.html', context)


def restaurant_detail(request, restaurant_id):
    """
    Display restaurant details and menu items for a specific restaurant.
    Supports filtering by category and includes reviews and wishlist status.
    
    Args:
        request: Django HTTP request object
        restaurant_id: ID of the restaurant to display
    
    Returns:
        HttpResponse: Rendered restaurant detail page template
    """
    # Get restaurant or 404 (must be active and approved)
    restaurant = get_object_or_404(Restaurant, id=restaurant_id, is_active=True, is_approved=True)
    
    # Get category filter if provided
    category_id = request.GET.get('category')
    
    # Get all categories for this restaurant
    categories = Category.objects.filter(
        items__restaurant=restaurant,
        is_active=True
    ).distinct()
    
    # Filter menu items by restaurant and optionally by category
    if category_id:
        menu_items = MenuItem.objects.filter(
            restaurant=restaurant,
            category_id=category_id,
            is_available=True
        ).select_related('category')
        selected_category = get_object_or_404(Category, id=category_id)
    else:
        menu_items = MenuItem.objects.filter(
            restaurant=restaurant,
            is_available=True
        ).select_related('category')
        selected_category = None
    
    # Get restaurant reviews with user information and aggregated ratings (only visible reviews)
    reviews = RestaurantReview.objects.filter(
        restaurant=restaurant,
        is_hidden=False
    ).select_related('user', 'order').order_by('-created_at')
    
    # Add pagination for reviews
    paginator = Paginator(reviews, 5)  # Show 5 reviews per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Calculate rating aggregates using cached properties
    avg_rating = restaurant.average_rating
    review_count = restaurant.review_count
    
    # Get detailed rating breakdown
    rating_aggregates = reviews.aggregate(
        avg_food_quality=Avg('food_quality'),
        avg_service_quality=Avg('service_quality'),
        avg_delivery_speed=Avg('delivery_speed'),
        avg_value_for_money=Avg('value_for_money')
    )
    
    # Check if user has ordered from this restaurant (for review eligibility)
    has_ordered = False
    if request.user.is_authenticated:
        has_ordered = Order.objects.filter(
            user=request.user,
            items__menu_item__restaurant=restaurant,
            status='delivered'
        ).exists()
    
    # Check if restaurant is in user's wishlist
    is_in_wishlist = False
    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(
            user=request.user,
            restaurant=restaurant
        ).exists()
    
    # Check if user has already reviewed this restaurant
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = RestaurantReview.objects.filter(
            user=request.user,
            restaurant=restaurant
        ).exists()
    
    context = {
        'restaurant': restaurant,
        'categories': categories,
        'menu_items': menu_items,
        'selected_category': selected_category,
        'reviews': page_obj,
        'page_obj': page_obj,
        'rating_aggregates': rating_aggregates,
        'has_ordered': has_ordered,
        'is_in_wishlist': is_in_wishlist,
        'user_has_reviewed': user_has_reviewed,
        'avg_rating': avg_rating,
        'review_count': review_count,
    }
    return render(request, 'customer/restaurant_detail.html', context)


def menu(request):
    """
    Display all available menu items from all restaurants.
    Supports filtering by category.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered menu page template
    """
    category_id = request.GET.get('category')
    categories = Category.objects.filter(is_active=True)
    
    if category_id:
        menu_items = MenuItem.objects.filter(
            category_id=category_id,
            is_available=True,
            restaurant__is_active=True,
            restaurant__is_approved=True
        ).select_related('restaurant', 'category')
        selected_category = get_object_or_404(Category, id=category_id)
    else:
        menu_items = MenuItem.objects.filter(
            is_available=True,
            restaurant__is_active=True,
            restaurant__is_approved=True
        ).select_related('restaurant', 'category')
        selected_category = None
    
    context = {
        'categories': categories,
        'menu_items': menu_items,
        'selected_category': selected_category,
    }
    return render(request, 'customer/menu.html', context)


@require_POST
def cart_add(request, menu_item_id):
    """
    Add a menu item to the shopping cart. Requires user login.
    
    This function handles adding items to the session-based shopping cart.
    It validates that the menu item exists, is available, and belongs to
    an active and approved restaurant before adding to cart.
    
    Workflow:
    1. Initialize cart from user's session
    2. Fetch and validate menu item (404 if not found/unavailable)
    3. Extract quantity from POST data (default: 1)
    4. Add item to cart using Cart class
    5. Display success message to user
    6. Redirect back to previous page or home
    
    Args:
        request (HttpRequest): Django HTTP request object containing:
            - POST data with 'quantity' parameter (optional, default: 1)
            - User session for cart storage
            - Referer URL for redirect
        menu_item_id (int): Primary key of the MenuItem to add
    
    Returns:
        HttpResponse: Redirect to referring page (where user clicked add to cart)
                     or home page if referer is not available
    
    Raises:
        Http404: If menu item doesn't exist or is not available/approved
    
    Note:
        - Requires user to be logged in (login_required decorator)
        - Only accepts POST requests (require_POST decorator)
        - Cart is stored in user's session for persistence
        - Multiple calls will increment quantity of existing items
    """
    # Initialize session-based cart for current user
    cart = Cart(request)
    
    # Fetch menu item with validation filters
    # Returns 404 if item doesn't exist or doesn't meet criteria
    menu_item = get_object_or_404(
        MenuItem, 
        id=menu_item_id, 
        is_available=True,  # Item must be currently available
        restaurant__is_active=True,  # Restaurant must be active
        restaurant__is_approved=True  # Restaurant must be approved by admin
    )
    
    # Extract quantity from POST data, default to 1 if not provided
    quantity = int(request.POST.get('quantity', 1))
    
    # Add item to cart (or increment quantity if already exists)
    cart.add(menu_item=menu_item, quantity=quantity)
    
    # Inform user of successful addition
    messages.success(request, f'{menu_item.name} added to cart!')
    
    # Redirect back to the page where user clicked 'Add to Cart'
    # Falls back to home page if referer is not available
    return redirect(request.META.get('HTTP_REFERER', 'customer:home'))


@require_POST
def cart_remove(request, menu_item_id):
    """
    Remove a menu item completely from the shopping cart with enhanced AJAX support.
    
    This function removes all quantities of a specific menu item from the cart.
    Unlike cart_update which can modify quantity, this function completely
    removes the item regardless of quantity. Supports both AJAX and traditional requests.
    Includes version control to prevent race conditions.
    
    Workflow:
    =========
    1. Initialize cart from user's session
    2. Validate cart version to prevent race conditions
    3. Fetch menu item to remove (404 if not found)
    4. Remove item from cart entirely
    5. Calculate updated cart totals
    6. Return JSON response for AJAX or redirect for traditional requests
    
    Args:
        request (HttpRequest): Django HTTP request object containing user session
            and AJAX headers for JSON response detection
            and 'cart_version' parameter for race condition prevention
        menu_item_id (int): Primary key of the MenuItem to remove from cart
    
    Returns:
        HttpResponse: JSON response for AJAX requests or redirect for traditional forms:
            - AJAX: {'success': bool, 'message': str, 'cart_totals': dict}
            - Traditional: Redirect to cart detail page
    
    JSON Response Format:
    =====================
    Success Response:
    {
        'success': True,
        'message': 'Item removed from cart',
        'cart_totals': {
            'subtotal': '99.99',
            'total': '139.99', 
            'discount': '20.00',
            'item_count': 2,
            'cart_version': 3
        }
    }
    
    Error Response:
    {
        'success': False,
        'message': 'Error description for user',
        'requires_refresh': true
    }
    
    Raises:
        Http404: If menu item with given ID doesn't exist
    
    Note:
        - Requires user to be logged in (login_required decorator)
        - Only accepts POST requests (require_POST decorator)
        - Removes item completely, not just decrements quantity
        - Safe to call even if item is not in cart (no error)
        - Supports both AJAX and traditional form submissions
        - Uses version control to prevent race conditions
    """
    # Initialize session-based cart
    cart = Cart(request)
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    try:
        # Validate cart version to prevent race conditions (for AJAX requests)
        if is_ajax:
            expected_version = int(request.POST.get('cart_version', 0))
            if not cart._validate_version(expected_version):
                error_msg = "Cart was updated in another tab. Please refresh and try again."
                return JsonResponse({'success': False, 'message': error_msg, 'requires_refresh': True})
        
        # Fetch menu item to be removed (validates existence)
        try:
            menu_item = get_object_or_404(MenuItem, id=menu_item_id)
        except Exception as e:
            error_msg = "Item not found"
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('customer:cart')
        
        # Store item name for success message
        item_name = menu_item.name
        
        # Remove item completely from cart (all quantities)
        cart.remove(menu_item)
        
        # Calculate updated cart totals for response
        cart_totals = {
            'subtotal': float(cart.get_cart_total()),
            'total': float(cart.get_cart_total()),  # Will be updated with discounts later
            'discount': 0.0,  # Will be calculated if promo code applied
            'item_count': len(cart),
            'cart_version': cart.version  # Include new version for client
        }
        
        # Check for applied promo code and recalculate totals
        applied_promo = cart.get_applied_promo_code()
        if applied_promo:
            discount_amount, free_delivery = cart.calculate_discount()
            cart_totals['discount'] = float(discount_amount)
            cart_totals['total'] = float(cart_totals['subtotal'] - discount_amount)
        
        success_message = f'{item_name} removed from cart.'
        
        # Return appropriate response based on request type
        if is_ajax:
            return JsonResponse({
                'success': True, 
                'message': success_message,
                'cart_totals': cart_totals
            })
        else:
            # Traditional form submission
            messages.info(request, success_message)
            return redirect('customer:cart')
            
    except Exception as e:
        # Handle unexpected errors gracefully
        error_msg = "An error occurred while removing the item. Please try again."
        
        # Log error for debugging
        print(f"Cart remove error: {str(e)}")
        
        if is_ajax:
            return JsonResponse({'success': False, 'message': error_msg})
        else:
            messages.error(request, error_msg)
            return redirect('customer:cart')


@require_POST
def cart_update(request, menu_item_id):
    """
    Update the quantity of a menu item in the cart with enhanced AJAX support.
    
    This function provides comprehensive cart updates with:
    - JSON response support for AJAX requests
    - Item availability validation
    - Stock/inventory checking
    - Cart totals calculation
    - Error handling with detailed messages
    - Version control for race condition prevention
    
    Workflow:
    =========
    1. Initialize cart from user's session
    2. Validate cart version to prevent race conditions
    3. Fetch and validate menu item (must be available and approved)
    4. Extract new quantity from POST data with validation
    5. Perform client-side validation (min/max quantities)
    6. Check item availability and stock limits
    7. If quantity > 0: Update item quantity in cart
    8. If quantity <= 0: Remove item from cart completely
    9. Calculate updated cart totals
    10. Return JSON response with success status and data
    
    Args:
        request (HttpRequest): Django HTTP request object containing:
            - POST data with 'quantity' parameter (required)
            - User session for cart storage
            - AJAX headers for JSON response detection
            - 'cart_version' parameter for race condition prevention
        menu_item_id (int): Primary key of the MenuItem to update
    
    Returns:
        HttpResponse: JSON response for AJAX requests or redirect for traditional forms:
            - AJAX: {'success': bool, 'message': str, 'cart_totals': dict}
            - Traditional: Redirect to cart detail page
    
    JSON Response Format:
    =====================
    Success Response:
    {
        'success': True,
        'message': 'Cart updated successfully!',
        'cart_totals': {
            'subtotal': '129.99',
            'total': '169.99',
            'discount': '20.00',
            'item_count': 3
        }
    }
    
    Error Response:
    {
        'success': False,
        'message': 'Error description for user'
    }
    
    Raises:
        Http404: If menu item doesn't exist or is not available/approved
    
    Note:
        - Requires user to be logged in (login_required decorator)
        - Only accepts POST requests (require_POST decorator)
        - Quantity limits: 1-99 items per product
        - Validates item availability before updating
        - Supports both AJAX and traditional form submissions
        - Includes comprehensive error handling and validation
        - Uses version control to prevent race conditions
    """
    # Initialize session-based cart
    cart = Cart(request)
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    try:
        # Validate cart version to prevent race conditions (for AJAX requests)
        if is_ajax:
            expected_version = int(request.POST.get('cart_version', 0))
            if not cart._validate_version(expected_version):
                error_msg = "Cart was updated in another tab. Please refresh and try again."
                return JsonResponse({'success': False, 'message': error_msg, 'requires_refresh': True})
        
        # Fetch menu item with validation filters
        # Ensures item is still available and restaurant is approved
        try:
            menu_item = get_object_or_404(
                MenuItem, 
                id=menu_item_id, 
                is_available=True,  # Item must be currently available
                restaurant__is_active=True,  # Restaurant must be active
                restaurant__is_approved=True  # Restaurant must be approved
            )
        except Exception as e:
            error_msg = "Item not found or no longer available"
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('customer:cart')
        
        # Extract and validate new quantity from POST data
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            error_msg = "Invalid quantity value"
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('customer:cart')
        
        # Client-side validation - quantity limits
        if quantity < 1:
            error_msg = "Quantity must be at least 1"
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('customer:cart')
        
        if quantity > 99:
            error_msg = "Maximum quantity is 99 items per product"
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('customer:cart')
        
        # Additional validation - check if item is still available
        # This handles cases where item became unavailable after page load
        if not menu_item.is_available:
            error_msg = f"{menu_item.name} is no longer available"
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('customer:cart')
        
        # Additional validation - check restaurant status
        if not menu_item.restaurant.is_active or not menu_item.restaurant.is_approved:
            error_msg = f"{menu_item.restaurant.name} is not currently accepting orders"
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('customer:cart')
        
        # Handle quantity update or removal
        if quantity > 0:
            # Update cart with new quantity (replaces old quantity)
            cart.add(menu_item=menu_item, quantity=quantity, update_quantity=True)
            success_message = 'Cart updated successfully!'
        else:
            # Quantity is 0 or negative - remove item from cart
            cart.remove(menu_item)
            success_message = f'{menu_item.name} removed from cart.'
        
        # Calculate updated cart totals for response
        cart_totals = {
            'subtotal': float(cart.get_cart_total()),
            'total': float(cart.get_cart_total()),  # Will be updated with discounts later
            'discount': 0.0,  # Will be calculated if promo code applied
            'item_count': len(cart),
            'cart_version': cart.version  # Include new version for client
        }
        
        # Check for applied promo code and recalculate totals
        applied_promo = cart.get_applied_promo_code()
        if applied_promo:
            discount_amount, free_delivery = cart.calculate_discount()
            cart_totals['discount'] = float(discount_amount)
            cart_totals['total'] = float(cart_totals['subtotal'] - discount_amount)
        
        # Return appropriate response based on request type
        if is_ajax:
            return JsonResponse({
                'success': True, 
                'message': success_message,
                'cart_totals': cart_totals
            })
        else:
            # Traditional form submission
            messages.success(request, success_message)
            return redirect('customer:cart')
            
    except Exception as e:
        # Handle unexpected errors gracefully
        error_msg = "An error occurred while updating your cart. Please try again."
        
        # Log error for debugging
        print(f"Cart update error: {str(e)}")
        
        if is_ajax:
            return JsonResponse({'success': False, 'message': error_msg})
        else:
            messages.error(request, error_msg)
            return redirect('customer:cart')


def cart_detail(request):
    """
    Display the shopping cart with all items and pricing. Requires user login.
    
    This view renders the cart page showing all items, quantities, prices,
    and allows users to apply promo codes or proceed to checkout.
    Supports auto-applying promo codes via URL parameter for marketing campaigns.
    
    Workflow:
    1. Initialize cart from user's session
    2. Check for 'promo' URL parameter (for auto-apply campaigns)
    3. If promo code provided: Attempt to apply it to cart
    4. Display success/error message based on promo code validation
    5. Render cart template with all cart data and pricing
    
    URL Parameters:
        promo (optional): Promo code to automatically apply to cart
                         Example: /cart/?promo=SAVE20
    
    Args:
        request (HttpRequest): Django HTTP request object containing:
            - User session with cart data
            - Optional GET parameter 'promo' for auto-apply
            - Authenticated user for promo code validation
    
    Returns:
        HttpResponse: Rendered 'customer/cart.html' template with context:
            - cart: Cart object with all items and methods
            - Applied promo code information (if any)
            - Price breakdowns and totals
    
    Template Context:
        cart (Cart): Shopping cart object containing:
            - All cart items with quantities and prices
            - Applied promo code (if any)
            - Discount calculations
            - Total price calculations
    
    Note:
        - Requires user to be logged in (login_required decorator)
        - Promo code is converted to uppercase for consistency
        - Failed promo code application shows error but doesn't stop page load
        - Cart shows progress indicator for checkout flow
        - Includes promo code application form via AJAX
    """
    # Initialize session-based cart with all items and pricing
    cart = Cart(request)
    
    # Handle auto-apply promo code from marketing campaigns
    # URL format: /cart/?promo=SAVE20
    promo_code_param = request.GET.get('promo')
    if promo_code_param:
        try:
            # Apply the promo code to cart using string code
            # Converts to uppercase for case-insensitive matching
            success, message = cart.apply_promo_code(
                promo_code_param.upper(), 
                user=request.user
            )
            
            # Display appropriate message based on validation result
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
                
        except Exception as e:
            # Handle unexpected errors during promo code application
            messages.error(request, f'Error applying promo code: {str(e)}')
    
    # Render cart page with cart object
    # Template has access to cart items, pricing, and AJAX promo code form
    return render(request, 'customer/cart.html', {'cart': cart})


@login_required
@require_POST
def cart_remove_promo(request):
    """
    Remove applied promo code from cart and redirect back.
    
    This view removes any currently applied promo code from the cart
    and redirects back to the referring page (cart or checkout).
    
    Args:
        request (HttpRequest): Django HTTP request object containing:
            - User session with cart
            - POST data (if any)
            - GET/POST 'next' parameter for redirect
    
    Returns:
        HttpResponseRedirect: Redirect back to referring page with success message
    
    Note:
        - Requires user to be logged in (login_required decorator)
        - Only accepts POST requests (@require_POST decorator)
        - Uses Cart.remove_promo_code() to clear the promo code
        - Supports 'next' parameter for custom redirect
        - Shows success message via Django messages framework
    """
    # Initialize cart from session
    cart = Cart(request)
    
    try:
        # Remove promo code from cart
        cart.remove_promo_code()
        messages.success(request, 'Promo code removed successfully.')
        
    except Exception as e:
        # Handle unexpected errors during promo code removal
        messages.error(request, f'Error removing promo code: {str(e)}')
    
    # Check for next parameter to redirect back to checkout
    next_url = request.POST.get('next', request.GET.get('next'))
    if next_url and 'checkout' in next_url:
        return redirect(next_url)
    # Redirect back to cart page by default
    return redirect('customer:cart')


@require_POST
def apply_promo_code(request):
    """
    Handle promo code application via POST request from cart page.
    
    This view processes promo code submissions from the cart form,
    validates the code, applies it to the cart, and redirects back
    to the cart page with appropriate success/error messages.
    
    Args:
        request (HttpRequest): Django HTTP request object containing:
            - POST data with 'promo_code' field
            - User session with cart
            - Authenticated user for validation
    
    Returns:
        HttpResponseRedirect: Redirect back to cart page with messages
    
    Form Data Expected:
        promo_code (str): Promo code string entered by user
    
    Note:
        - Requires user to be logged in (login_required decorator)
        - Only accepts POST requests (@require_POST decorator)
        - Uses Cart.apply_promo_code() for validation and application
        - Shows success/error messages via Django messages framework
        - Redirects back to cart regardless of success/failure
    """
    # Initialize cart from session
    cart = Cart(request)
    
    # Get promo code from form submission
    promo_code = request.POST.get('promo_code', '').strip()
    
    if not promo_code:
        messages.error(request, 'Please enter a promo code.')
        # Check for next parameter to redirect back to checkout
        next_url = request.POST.get('next', request.GET.get('next'))
        if next_url and 'checkout' in next_url:
            return redirect(next_url)
        return redirect('customer:cart')
    
    try:
        # Apply promo code to cart
        # Cart.apply_promo_code() handles validation and application
        success, message = cart.apply_promo_code(
            promo_code.upper(),  # Convert to uppercase for consistency
            user=request.user
        )
        
        # Display appropriate message
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
            
    except Exception as e:
        # Handle unexpected errors during promo code application
        messages.error(request, f'Error applying promo code: {str(e)}')
    
    # Check for next parameter to redirect back to checkout
    next_url = request.POST.get('next', request.GET.get('next'))
    if next_url and 'checkout' in next_url:
        return redirect(next_url)
    # Redirect back to cart page
    return redirect('customer:cart')


@login_required
def checkout(request):
    """
    Handle the checkout process and order creation. Requires user login.
    
    This is the final step in the cart-to-checkout workflow. It validates cart contents,
    collects delivery information, applies discounts, creates the order record, and
    sends confirmation emails. Supports both delivery and takeaway options.
    
    Complete Workflow:
    ============================================
    GET Request (Show Checkout Form):
    1. Initialize cart from session
    2. Validate cart is not empty
    3. Validate all items are still available and approved
    4. Remove any invalid items and redirect to cart if found
    5. Initialize checkout form
    6. Calculate pricing breakdown with delivery method
    7. Render checkout template with form and pricing
    
    POST Request (Process Order):
    1. Validate submitted checkout form
    2. Extract delivery method (delivery/takeaway)
    3. Calculate final pricing with discounts
    4. Create Order record in database
    5. Create OrderItem records for each cart item
    6. Track promo code usage if applied
    7. Send order confirmation email
    8. Clear cart from session
    9. Redirect to order success page
    ============================================
    
    Args:
        request (HttpRequest): Django HTTP request object containing:
            - User session with cart data
            - Authenticated user for order creation
            - POST data with checkout form (if submitting order)
    
    Returns:
        HttpResponse: 
            - GET: Rendered 'customer/checkout.html' with form and pricing
            - POST (valid): Redirect to order success page
            - POST (invalid): Re-render checkout form with errors
            - Empty cart: Redirect to home page
            - Invalid items: Redirect to cart page for review
    
    Template Context (GET request):
        form (CheckoutForm): Form for customer information:
            - delivery_method: Delivery or takeaway selection
            - customer_name: Full name for delivery
            - customer_phone: Contact phone number
            - customer_address: Delivery address (required for delivery)
            - notes: Optional order instructions
        cart (Cart): Shopping cart with all items
        breakdown (dict): Complete pricing breakdown:
            - subtotal: Cart total before discounts
            - discount_amount: Discount from promo code
            - delivery_charge: Delivery fee (or 0 for takeaway)
            - free_delivery: Boolean for free delivery promo
            - final_total: Total after all adjustments
            - applied_promo_code: PromoCode object if applied
            - delivery_method: Selected delivery method
    
    Validation Steps:
        1. Cart must not be empty
        2. All items must be available
        3. All restaurants must be active and approved
        4. Form data must be valid
        5. Address required for delivery orders
    
    Order Creation:
        - Generates unique order_id (UUID)
        - Stores customer information
        - Saves pricing breakdown
        - Links to applied promo code
        - Creates OrderItem for each cart item
        - Tracks promo code usage for analytics
    
    Email Notification:
        - Sends order confirmation to customer
        - Includes order details, items, and pricing
        - Gracefully handles email failures
    
    Note:
        - Requires user to be logged in (login_required decorator)
        - Cart is cleared after successful order creation
        - Promo code usage is tracked and incremented
        - Order total includes all discounts and delivery charges
        - Failed email doesn't prevent order creation
    """
    # Initialize session-based cart
    cart = Cart(request)
    
    # Validation Step 1: Check if cart is empty
    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty!')
        return redirect('customer:home')
    
    # Validation Step 2: Validate all cart items are still valid
    # Check that items are available and from approved restaurants
    invalid_items = []
    for item in cart:
        menu_item = item['menu_item']
        if not (menu_item['is_available'] and 
                menu_item['restaurant']['is_active'] and 
                menu_item['restaurant']['is_approved']):
            invalid_items.append(menu_item['name'])
    
    # If invalid items found, remove them and redirect to cart
    if invalid_items:
        # Remove each invalid item from cart
        for item in cart:
            menu_item = item['menu_item']
            if not (menu_item['is_available'] and 
                    menu_item['restaurant']['is_active'] and 
                    menu_item['restaurant']['is_approved']):
                cart.remove_by_id(menu_item['id'])
        
        # Inform user which items were removed
        messages.error(
            request, 
            f'The following items were removed from your cart because they are no longer available: {", ".join(invalid_items)}. '
            'Please review your cart before checkout.'
        )
        return redirect('customer:cart')
    
    # Initialize delivery method for pricing calculations
    # Default to 'delivery', updated from form if POST request
    delivery_method = 'delivery'
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            delivery_method = form.cleaned_data['delivery_method']
    else:
        form = CheckoutForm()
    
    # ============================================
    # LOYALTY POINTS REDEMPTION LOGIC
    # ============================================
    # Get user's current points balance
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'full_name': request.user.username}
    )
    available_points = user_profile.points_balance
    
    # Handle points redemption from POST request
    points_to_redeem = 0
    points_discount = 0
    
    if request.method == 'POST' and form.is_valid():
        points_to_redeem = int(request.POST.get('points_to_redeem', 0))
        
        # Validate points redemption
        if points_to_redeem > 0:
            # Maximum redemption: 50% of order subtotal or available points, whichever is lower
            max_redemption = min(
                available_points,
                int(breakdown['subtotal'] * 0.5),  # Max 50% of subtotal
                1000  # Maximum 1000 points per order
            )
            
            if points_to_redeem > max_redemption:
                points_to_redeem = max_redemption
                messages.info(request, f'Points redemption limited to {max_redemption} points (50% of order total)')
            
            points_discount = points_to_redeem  # 1 point = ₹1 discount
    
    # Calculate complete pricing breakdown based on delivery method
    # Includes subtotal, discounts, delivery charges, and final total
    breakdown = cart.get_discount_breakdown(delivery_method=delivery_method)
    
    # Apply points discount if applicable
    if points_discount > 0:
        breakdown['points_discount'] = points_discount
        breakdown['points_used'] = points_to_redeem
        breakdown['final_total'] = max(0, breakdown['final_total'] - points_discount)
    
    # Calculate maximum points allowed for display
    from decimal import Decimal
    max_points_allowed = min(
        available_points,
        int(breakdown['subtotal'] * Decimal('0.5')),  # Max 50% of subtotal using Decimal
        1000  # Maximum 1000 points per order
    )
    
    # Handle POST request - Process order submission
    if request.method == 'POST':
        if form.is_valid():
            # ============================================
            # ORDER CREATION PROCESS
            # ============================================
            
            # Step 1: Get applied promo code from cart session
            applied_promo_code = cart.get_applied_promo_code()
            
            # Step 2: Get payment method from form
            payment_method = form.cleaned_data.get('payment_method', 'cod')
            
            # Step 3: Create points redemption transaction if applicable
            if points_to_redeem > 0:
                from django.db import transaction
                try:
                    # ATOMIC TRANSACTION: Prevent race conditions and ensure consistency
                    with transaction.atomic():
                        # Re-fetch user profile with select_for_update to lock the row
                        user_profile = UserProfile.objects.select_for_update().get(user=request.user)
                        
                        # Double-check available points (prevents race conditions)
                        if user_profile.points_balance >= points_to_redeem:
                            # Create redemption transaction
                            new_balance = user_profile.points_balance - points_to_redeem
                            LoyaltyTransaction.objects.create(
                                user=request.user,
                                transaction_type='redeemed',
                                points=-points_to_redeem,  # Negative for redemption
                                balance_after=new_balance,
                                description=f'Points redeemed for order #{order.order_id}',
                            )
                            
                            # Update user profile balance
                            user_profile.points_balance = new_balance
                            user_profile.save()
                            
                            print(f"Points redemption successful: {points_to_redeem} points deducted for order #{order.order_id}")
                        else:
                            # Insufficient points - this shouldn't happen with proper validation
                            points_to_redeem = 0
                            points_discount = 0
                            messages.warning(request, 'Insufficient points available. Points discount not applied.')
                    
                except Exception as e:
                    # Log error but don't fail the order
                    print(f"Failed to process points redemption: {e}")
                    import traceback
                    traceback.print_exc()
                    points_to_redeem = 0
                    points_discount = 0
                    messages.error(request, 'Points redemption failed. Please contact support.')
            
            # Step 3: Create main Order record with all details
            # SECURITY NOTE: Django's CSRF token protection prevents manipulation
            # of form data during submission. All form data is validated server-side.
            # Client-side sanitization in JavaScript provides additional protection
            # but server-side validation is the authoritative security layer.
            order = Order.objects.create(
                user=request.user,  # Link order to authenticated user
                customer_name=form.cleaned_data['customer_name'],
                customer_phone=form.cleaned_data['customer_phone'],
                customer_address=form.cleaned_data.get('customer_address', ''),  # Empty for takeaway
                delivery_method=form.cleaned_data['delivery_method'],  # 'delivery' or 'takeaway'
                delivery_time=form.cleaned_data.get('delivery_time', 'asap'),  # New field with default
                total_amount=breakdown['final_total'],  # Final total after all discounts
                promo_code=applied_promo_code,  # Foreign key to PromoCode (or None)
                discount_amount=breakdown['discount_amount'],  # Amount discounted
                delivery_charge=breakdown['delivery_charge'],  # Delivery fee (0 for takeaway)
                free_delivery_applied=breakdown['free_delivery'],  # Boolean flag
                notes=form.cleaned_data.get('notes', ''),  # Optional customer notes
                payment_method=payment_method,  # 'cod' or 'online'
                payment_status='pending'  # Initial payment status
            )
            
            # Step 3: Create OrderItem records for each cart item
            # This preserves item details at time of order (price, quantity)
            items_created = 0
            items_failed = 0
            for item in cart:
                try:
                    # Get actual MenuItem object from database
                    menu_item = MenuItem.objects.get(id=item['menu_item']['id'])
                    
                    # Create OrderItem record
                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        quantity=item['quantity'],
                        price=item['price']  # Price at time of order (for historical accuracy)
                    )
                    items_created += 1
                except Exception as e:
                    items_failed += 1
                    # Log error for debugging but continue processing
                    print(f"Failed to create OrderItem for item {item['menu_item']['id']}: {e}")
            
            # Log order creation summary
            print(f"Order {order.order_id}: {items_created} items created, {items_failed} failed")
            
            # Step 4: Track promo code usage if applied
            if applied_promo_code:
                from orders.models import PromoCodeUsage
                
                # Increment global usage counter on promo code
                applied_promo_code.increment_usage()
                
                # Create usage record for analytics and per-user limits
                PromoCodeUsage.objects.create(
                    promo_code=applied_promo_code,
                    user=request.user,
                    order=order,
                    discount_amount=breakdown['discount_amount'],
                    free_delivery_applied=breakdown['free_delivery']
                )
            
            # Step 5: Handle payment method flow
            # Online payments are disabled - only COD is allowed
            if payment_method == 'online':
                # Online payments have been disabled
                # Add error message and prevent order creation
                messages.error(request, 'Online payments are currently disabled. Please select Cash on Delivery.')
                order.delete()  # Clean up the created order
                return redirect('customer:checkout')
                # ============================================
                # ONLINE PAYMENT FLOW WITH RAZORPAY
                # ============================================
                try:
                    # Create Razorpay order for payment processing
                    razorpay_order = create_razorpay_order(
                        amount=order.total_amount,
                        order_id=order.order_id,
                        receipt_id=f"receipt_{order.order_id}"
                    )
                    
                    # Save Razorpay order ID to database
                    order.razorpay_order_id = razorpay_order['id']
                    order.payment_status = 'processing'
                    order.save()
                    
                    # Store order ID in session for payment page
                    request.session['pending_order_id'] = str(order.order_id)
                    
                    # Redirect to payment page with Razorpay checkout
                    # Cart remains intact until payment is confirmed
                    return redirect('customer:process_payment', order_id=order.order_id)
                    
                except Exception as e:
                    # Payment gateway error - delete order and show error
                    import traceback
                    print("=" * 60)
                    print("PAYMENT GATEWAY ERROR - DETAILED DEBUG INFO:")
                    print(f"Error: {e}")
                    print(f"Error Type: {type(e).__name__}")
                    print("Full Traceback:")
                    traceback.print_exc()
                    print("=" * 60)
                    order.delete()  # Remove order if payment setup fails
                    messages.error(request, 'Payment gateway error. Please try again or use Cash on Delivery.')
                    return redirect('customer:checkout')
            else:
                # ============================================
                # CASH ON DELIVERY FLOW
                # ============================================
                # Mark payment as pending for COD orders
                order.payment_status = 'pending'
                order.save()
                
                # ============================================
                # AWARD LOYALTY POINTS FOR COD
                # ============================================
                try:
                    from django.utils import timezone
                    from datetime import timedelta
                    
                    # Calculate points: 1 point per ₹10 spent (minimum 10 points)
                    points_earned = max(10, int(order.total_amount / 10))
                    
                    # Get or create user profile
                    user_profile, created = UserProfile.objects.get_or_create(
                        user=request.user,
                        defaults={'full_name': request.user.username}
                    )
                    
                    # Calculate new balance
                    new_balance = user_profile.points_balance + points_earned
                    
                    # Create loyalty transaction
                    LoyaltyTransaction.objects.create(
                        user=request.user,
                        transaction_type='earned',
                        points=points_earned,
                        balance_after=new_balance,
                        order=order,
                        description=f'Points earned from COD order #{order.order_id}',
                        expires_at=timezone.now() + timedelta(days=365)  # Points expire in 1 year
                    )
                    
                    # Update user profile balance
                    user_profile.points_balance = new_balance
                    user_profile.save()
                    
                    print(f"Loyalty points awarded for COD: {points_earned} points to {request.user.username}")
                    
                except Exception as e:
                    # Log error but don't fail the order
                    print(f"Failed to award loyalty points for COD: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Send order confirmation email
                try:
                    send_order_confirmation_email(request.user, order)
                    messages.success(request, 'Order placed successfully! Confirmation email sent.')
                except Exception as e:
                    # Log email error but don't fail the order
                    print(f"Email sending failed: {e}")
                    messages.success(request, 'Order placed successfully! (Email confirmation failed)')
                
                # Clear cart from session
                cart.clear()
                
                # Redirect to order success page
                return redirect('customer:order_success', order_id=order.order_id)
    else:
        # GET request - Show empty checkout form
        form = CheckoutForm()
    
    context = {
        'form': form,
        'cart': cart,
        'breakdown': breakdown,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,  # For payment integration
        # Loyalty points context
        'available_points': available_points,
        'max_points_allowed': max_points_allowed,
    }
    return render(request, 'customer/checkout.html', context)


@login_required
def order_history(request):
    """
    Display the order history for the logged-in user.
    
    Shows all past orders with their details, status, and items.
    Includes pagination for better performance.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered order history page template
    """
    # Get orders for the current user, ordered by creation date (newest first)
    orders = Order.objects.filter(user=request.user).prefetch_related('items__menu_item').order_by('-created_at')
    
    # Pagination - show 10 orders per page
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'orders': page_obj,
    }
    return render(request, 'customer/order_history.html', context)


@login_required
def order_tracking(request, order_id):
    """
    Display order tracking page for customers.
    
    Shows detailed order information with status timeline and
    real-time tracking of order progress.
    
    Args:
        request: Django HTTP request object
        order_id: UUID of the order to track
    
    Returns:
        HttpResponse: Rendered order tracking page template
    """
    # Get order that belongs to the current user
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Define order status timeline with descriptions
    status_timeline = {
        'pending': {
            'title': 'Order Received',
            'description': 'Your order has been received and is being reviewed',
            'icon': '📝',
            'completed': order.status != 'pending'
        },
        'accepted': {
            'title': 'Order Accepted',
            'description': 'Restaurant has accepted your order and started preparation',
            'icon': '✅',
            'completed': order.status not in ['pending']
        },
        'preparing': {
            'title': 'Preparing Food',
            'description': 'Your delicious food is being prepared with care',
            'icon': '👨‍🍳',
            'completed': order.status in ['out_for_delivery', 'delivered']
        },
        'out_for_delivery': {
            'title': 'Out for Delivery',
            'description': 'Your order is on its way to your location',
            'icon': '🚚',
            'completed': order.status == 'delivered'
        },
        'delivered': {
            'title': 'Delivered',
            'description': 'Your order has been successfully delivered',
            'icon': '🎉',
            'completed': order.status == 'delivered'
        }
    }
    
    context = {
        'order': order,
        'status_timeline': status_timeline,
        'current_status': order.status,
    }
    return render(request, 'customer/order_tracking.html', context)


def order_success(request, order_id):
    """
    Display order confirmation page.
    
    Args:
        request: Django HTTP request object
        order_id: UUID of the created order
    
    Returns:
        HttpResponse: Rendered order success page template
    """
    order = get_object_or_404(Order, order_id=order_id)
    context = {'order': order}
    return render(request, 'customer/order_success.html', context)


@login_required
def user_profile(request):
    """
    Display user profile page with restaurant upgrade option and profile editing.
    
    Shows user information, allows profile editing, displays status of pending
    applications, and provides dashboard statistics for quick access.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        HttpResponse: Rendered user profile page with edit functionality
    """
    # Check if user is already a restaurant owner
    is_restaurant_owner = request.user.groups.filter(name='Restaurant Owner').exists()
    
    # Get user's restaurants
    user_restaurants = Restaurant.objects.filter(owner=request.user)
    
    # Get pending restaurant applications
    pending_applications = PendingRestaurant.objects.filter(
        user=request.user,
        status='pending'
    )
    
    # Get rejected applications
    rejected_applications = PendingRestaurant.objects.filter(
        user=request.user,
        status='rejected'
    )
    
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'full_name': request.user.username}
    )
    
    # Get dashboard statistics
    thirty_days_ago = timezone.now() - timedelta(days=30)
    order_stats = Order.objects.filter(user=request.user).aggregate(
        total_orders=models.Count('id'),
        total_spent=models.Sum('total_amount'),
        recent_orders=models.Count('id', filter=models.Q(created_at__gte=thirty_days_ago))
    )
    
    # Get recent orders for quick access
    recent_orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Get wishlist count
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    
    # Get review count
    review_count = RestaurantReview.objects.filter(user=request.user).count()
    
    # Initialize forms
    upgrade_form = RestaurantUpgradeForm()
    profile_form = UserProfileEditForm(instance=user_profile)
    
    # Handle profile edit form submission
    if request.method == 'POST' and 'edit_profile' in request.POST:
        profile_form = UserProfileEditForm(
            request.POST, 
            request.FILES, 
            instance=user_profile
        )
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('customer:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    
    # ============================================
    # NEW PROFILE ANALYTICS
    # ============================================
    # Get favorite/most ordered items
    favorite_items = MenuItem.objects.filter(
        orderitem__order__user=request.user
    ).annotate(
        order_count=models.Count('orderitem')
    ).order_by('-order_count')[:5]
    
    # Get spending analytics by month (last 6 months)
    from django.db.models.functions import TruncMonth
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_spending = Order.objects.filter(
        user=request.user,
        created_at__gte=six_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=models.Sum('total_amount'),
        count=models.Count('id')
    ).order_by('month')
    
    # Get order status breakdown
    order_status_breakdown = Order.objects.filter(
        user=request.user
    ).values('status').annotate(
        count=models.Count('id')
    ).order_by('-count')
    
    # Get delivery vs takeaway stats
    delivery_stats = Order.objects.filter(
        user=request.user
    ).values('delivery_method').annotate(
        count=models.Count('id'),
        total_spent=models.Sum('total_amount')
    )
    
    # Get most ordered restaurants
    favorite_restaurants = Restaurant.objects.filter(
        menu_items__orderitem__order__user=request.user
    ).annotate(
        order_count=models.Count('menu_items__orderitem__order', distinct=True),
        total_spent=models.Sum('menu_items__orderitem__order__total_amount', distinct=True)
    ).order_by('-order_count')[:5]
    
    # Get saved addresses count (using address from previous orders)
    saved_addresses = Order.objects.filter(
        user=request.user,
        customer_address__isnull=False
    ).values('customer_address').distinct()[:5]
    
    # ============================================
    # LOYALTY POINTS DATA
    # ============================================
    # Get recent loyalty transactions
    recent_transactions = LoyaltyTransaction.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]
    
    # Calculate points earned this month
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_points_earned = LoyaltyTransaction.objects.filter(
        user=request.user,
        transaction_type='earned',
        created_at__gte=current_month
    ).aggregate(total=models.Sum('points'))['total'] or 0
    
    # Calculate points redeemed this month
    monthly_points_redeemed = abs(LoyaltyTransaction.objects.filter(
        user=request.user,
        transaction_type='redeemed',
        created_at__gte=current_month
    ).aggregate(total=models.Sum('points'))['total'] or 0)
    
    # Get points expiring soon (within 30 days)
    thirty_days_from_now = timezone.now() + timedelta(days=30)
    expiring_points = LoyaltyTransaction.objects.filter(
        user=request.user,
        transaction_type='earned',
        expires_at__lte=thirty_days_from_now,
        expires_at__gt=timezone.now()
    ).aggregate(total=models.Sum('points'))['total'] or 0
    
    context = {
        'user': request.user,
        'user_profile': user_profile,
        'is_restaurant_owner': is_restaurant_owner,
        'user_restaurants': user_restaurants,
        'pending_applications': pending_applications,
        'rejected_applications': rejected_applications,
        'upgrade_form': upgrade_form,
        'profile_form': profile_form,
        # Dashboard statistics
        'order_stats': order_stats,
        'recent_orders': recent_orders,
        'wishlist_count': wishlist_count,
        'review_count': review_count,
        # NEW: Enhanced analytics
        'favorite_items': favorite_items,
        'monthly_spending': list(monthly_spending),
        'order_status_breakdown': order_status_breakdown,
        'delivery_stats': delivery_stats,
        'favorite_restaurants': favorite_restaurants,
        'saved_addresses': saved_addresses,
        # NEW: Loyalty points data
        'recent_transactions': recent_transactions,
        'monthly_points_earned': monthly_points_earned,
        'monthly_points_redeemed': monthly_points_redeemed,
        'expiring_points': expiring_points,
    }
    
    return render(request, 'customer/profile.html', context)


@login_required
def restaurant_upgrade(request):
    """
    Handle restaurant upgrade application from customer profile.
    
    Processes restaurant upgrade applications and creates pending
    restaurant records for manager approval.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        HttpResponse: Redirect to profile page with success/error messages
    """
    if request.method == 'POST':
        form = RestaurantUpgradeForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Check if user already has a pending application
            existing_pending = PendingRestaurant.objects.filter(
                user=request.user,
                status='pending'
            ).exists()
            
            if existing_pending:
                messages.error(
                    request, 
                    'You already have a pending restaurant application. '
                    'Please wait for it to be processed.'
                )
                return redirect('customer:profile')
            
            # Create pending restaurant application
            pending_restaurant = PendingRestaurant.objects.create(
                user=request.user,
                restaurant_name=form.cleaned_data['restaurant_name'],
                description=form.cleaned_data['description'],
                address=form.cleaned_data['address'],
                phone=form.cleaned_data['phone'],
                email=form.cleaned_data.get('restaurant_email'),
                cuisine_type=form.cleaned_data['cuisine_type'],
                image=form.cleaned_data.get('image'),
                opening_time=form.cleaned_data['opening_time'],
                closing_time=form.cleaned_data['closing_time'],
                minimum_order=form.cleaned_data['minimum_order'],
                delivery_fee=form.cleaned_data['delivery_fee'],
                status='pending'
            )
            
            messages.success(
                request,
                f'Restaurant application for "{pending_restaurant.restaurant_name}" '
                'has been submitted successfully! Our team will review your application '
                'and you will be notified once it is approved.'
            )
            
            return redirect('customer:profile')
        else:
            messages.error(
                request,
                'Please correct the errors below and try again.'
            )
    else:
        form = RestaurantUpgradeForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'customer/restaurant_upgrade.html', context)


@login_required
@require_POST
def toggle_wishlist(request, restaurant_id):
    """
    Toggle restaurant in user's wishlist (add/remove).
    
    Args:
        request: Django HTTP request object
        restaurant_id: ID of the restaurant to toggle
    
    Returns:
        HttpResponse: Redirect back to referring page with message
    """
    restaurant = get_object_or_404(Restaurant, id=restaurant_id, is_active=True, is_approved=True)
    
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        restaurant=restaurant
    )
    
    if not created:
        # Item already existed, so remove it
        wishlist_item.delete()
        messages.success(request, f'{restaurant.name} removed from your favorites!')
    else:
        # Item was newly created
        messages.success(request, f'{restaurant.name} added to your favorites!')
    
    return redirect(request.META.get('HTTP_REFERER', 'customer:home'))


@login_required
def my_wishlist(request):
    """
    Display user's wishlist of favorite restaurants.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered wishlist page template
    """
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('restaurant').order_by('-created_at')
    
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'customer/my_wishlist.html', context)


@login_required
def submit_review(request, restaurant_id):
    """
    Submit a review for a restaurant.
    
    Args:
        request: Django HTTP request object
        restaurant_id: ID of the restaurant to review
    
    Returns:
        HttpResponse: Rendered review submission form or redirect
    """
    restaurant = get_object_or_404(Restaurant, id=restaurant_id, is_active=True, is_approved=True)
    
    # Check if user has ordered from this restaurant
    has_ordered = Order.objects.filter(
        user=request.user,
        items__menu_item__restaurant=restaurant,
        status='delivered'
    ).exists()
    
    # Check if user already reviewed this restaurant
    existing_review = RestaurantReview.objects.filter(
        user=request.user,
        restaurant=restaurant
    ).first()
    
    if request.method == 'POST':
        if existing_review:
            messages.warning(request, 'You have already reviewed this restaurant!')
            return redirect('customer:restaurant_detail', restaurant_id=restaurant_id)
        
        try:
            rating = int(request.POST.get('rating', 0))
            food_quality = int(request.POST.get('food_quality', rating))
            delivery_speed = int(request.POST.get('delivery_speed', rating))
            value_for_money = int(request.POST.get('value_for_money', rating))
            title = request.POST.get('title', '').strip()
            comment = request.POST.get('comment', '').strip()
            
            if not (1 <= rating <= 5):
                messages.error(request, 'Please select a rating between 1 and 5 stars.')
                return redirect('customer:submit_review', restaurant_id=restaurant_id)
            
            if not title or not comment:
                messages.error(request, 'Please provide both a title and comment for your review.')
                return redirect('customer:submit_review', restaurant_id=restaurant_id)
            
            # Get the most recent delivered order from this restaurant
            recent_order = Order.objects.filter(
                user=request.user,
                items__menu_item__restaurant=restaurant,
                status='delivered'
            ).order_by('-created_at').first()
            
            review = RestaurantReview.objects.create(
                user=request.user,
                restaurant=restaurant,
                order=recent_order,
                rating=rating,
                food_quality=food_quality,
                delivery_speed=delivery_speed,
                value_for_money=value_for_money,
                title=title,
                comment=comment
            )
            
            # Update restaurant rating
            restaurant.update_rating()
            
            messages.success(request, 'Thank you for your review! It has been submitted successfully.')
            return redirect('customer:restaurant_detail', restaurant_id=restaurant_id)
            
        except Exception as e:
            messages.error(request, f'Error submitting review: {str(e)}')
            return redirect('customer:submit_review', restaurant_id=restaurant_id)
    
    context = {
        'restaurant': restaurant,
        'has_ordered': has_ordered,
        'existing_review': existing_review,
    }
    return render(request, 'customer/submit_review.html', context)


@login_required
def my_reviews(request):
    """
    Display user's submitted reviews.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered reviews page template
    """
    reviews = RestaurantReview.objects.filter(
        user=request.user
    ).select_related('restaurant').order_by('-created_at')
    
    context = {
        'reviews': reviews,
    }
    return render(request, 'customer/my_reviews.html', context)


@login_required
def order_history(request):
    """
    Display comprehensive order history with filters.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered order history page template
    """
    # Get all user orders
    orders = Order.objects.filter(user=request.user).select_related('user').prefetch_related('items__menu_item')
    
    # Apply status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Apply date sorting
    sort_by = request.GET.get('sort', 'recent')
    if sort_by == 'recent':
        orders = orders.order_by('-created_at')
    elif sort_by == 'oldest':
        orders = orders.order_by('created_at')
    elif sort_by == 'amount_high':
        orders = orders.order_by('-total_amount')
    elif sort_by == 'amount_low':
        orders = orders.order_by('total_amount')
    
    # Pagination
    paginator = Paginator(orders, 10)  # 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    total_orders = orders.count()
    total_spent = sum(order.total_amount for order in orders)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'order_status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'customer/order_history.html', context)


@login_required
def order_tracking(request, order_id):
    """
    Display detailed order tracking with timeline.
    
    Args:
        request: Django HTTP request object
        order_id: UUID of the order to track
    
    Returns:
        HttpResponse: Rendered order tracking page template
    """
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Define order status timeline
    status_timeline = [
        {'status': 'pending', 'label': 'Order Placed', 'icon': 'check-circle'},
        {'status': 'accepted', 'label': 'Order Accepted', 'icon': 'clipboard-check'},
        {'status': 'preparing', 'label': 'Preparing', 'icon': 'fire'},
        {'status': 'out_for_delivery', 'label': 'Out for Delivery', 'icon': 'truck'},
        {'status': 'delivered', 'label': 'Delivered', 'icon': 'check-circle'},
    ]
    
    # Mark completed statuses
    status_order = ['pending', 'accepted', 'preparing', 'out_for_delivery', 'delivered']
    try:
        current_index = status_order.index(order.status)
    except ValueError:
        current_index = 0
    
    for i, status_item in enumerate(status_timeline):
        status_item['completed'] = i <= current_index
        status_item['active'] = i == current_index
    
    context = {
        'order': order,
        'status_timeline': status_timeline,
    }
    return render(request, 'customer/order_tracking.html', context)


# ==================== REVIEW SYSTEM VIEWS ====================

@login_required
def create_restaurant_review(request, order_id):
    """
    Create a restaurant review for a delivered order.
    
    Args:
        request: Django HTTP request object
        order_id: UUID of the order to review
    
    Returns:
        HttpResponse: Rendered review creation page or redirect after submission
    """
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Check if order is delivered and eligible for review
    if order.status != 'delivered':
        messages.error(request, 'You can only review delivered orders.')
        return redirect('customer:order_history')
    
    # Check if review already exists
    existing_review = RestaurantReview.objects.filter(
        user=request.user, 
        order=order, 
        restaurant=order.restaurant
    ).first()
    
    if existing_review:
        messages.info(request, 'You have already reviewed this order.')
        return redirect('customer:edit_restaurant_review', review_id=existing_review.id)
    
    if request.method == 'POST':
        form = RestaurantReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.restaurant = order.restaurant
            review.order = order
            review.is_verified_purchase = True
            review.save()
            
            messages.success(request, 'Your restaurant review has been submitted successfully!')
            return redirect('customer:my_reviews')
    else:
        form = RestaurantReviewForm()
    
    context = {
        'form': form,
        'order': order,
        'restaurant': order.restaurant,
    }
    return render(request, 'customer/create_restaurant_review.html', context)


@login_required
def edit_restaurant_review(request, review_id):
    """
    Edit an existing restaurant review.
    
    Args:
        request: Django HTTP request object
        review_id: ID of the review to edit
    
    Returns:
        HttpResponse: Rendered review editing page or redirect after submission
    """
    review = get_object_or_404(RestaurantReview, id=review_id, user=request.user)
    
    # Check if review is still editable (within 7 days)
    if not review.is_editable:
        messages.error(request, 'This review can no longer be edited (7-day limit exceeded).')
        return redirect('customer:my_reviews')
    
    if request.method == 'POST':
        form = RestaurantReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your review has been updated successfully!')
            return redirect('customer:my_reviews')
    else:
        form = RestaurantReviewForm(instance=review)
    
    context = {
        'form': form,
        'review': review,
        'order': review.order,
        'restaurant': review.restaurant,
    }
    return render(request, 'customer/edit_restaurant_review.html', context)


@login_required
def create_menu_item_review(request, order_id, menu_item_id):
    """
    Create a menu item review for a delivered order.
    
    Args:
        request: Django HTTP request object
        order_id: UUID of the order containing the menu item
        menu_item_id: ID of the menu item to review
    
    Returns:
        HttpResponse: Rendered review creation page or redirect after submission
    """
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    
    # Check if order is delivered and eligible for review
    if order.status != 'delivered':
        messages.error(request, 'You can only review items from delivered orders.')
        return redirect('customer:order_history')
    
    # Verify menu item was in the order
    if not order.items.filter(menu_item=menu_item).exists():
        messages.error(request, 'This menu item was not in your order.')
        return redirect('customer:order_history')
    
    # Check if review already exists
    existing_review = MenuItemReview.objects.filter(
        user=request.user, 
        order=order, 
        menu_item=menu_item
    ).first()
    
    if existing_review:
        messages.info(request, 'You have already reviewed this menu item.')
        return redirect('customer:edit_menu_item_review', review_id=existing_review.id)
    
    if request.method == 'POST':
        form = MenuItemReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.menu_item = menu_item
            review.order = order
            review.save()
            
            messages.success(request, 'Your menu item review has been submitted successfully!')
            return redirect('customer:my_reviews')
    else:
        form = MenuItemReviewForm()
    
    context = {
        'form': form,
        'order': order,
        'menu_item': menu_item,
        'restaurant': menu_item.restaurant,
    }
    return render(request, 'customer/create_menu_item_review.html', context)


@login_required
def edit_menu_item_review(request, review_id):
    """
    Edit an existing menu item review.
    
    Args:
        request: Django HTTP request object
        review_id: ID of the review to edit
    
    Returns:
        HttpResponse: Rendered review editing page or redirect after submission
    """
    review = get_object_or_404(MenuItemReview, id=review_id, user=request.user)
    
    # Check if review is still editable (within 7 days)
    if not review.is_editable:
        messages.error(request, 'This review can no longer be edited (7-day limit exceeded).')
        return redirect('customer:my_reviews')
    
    if request.method == 'POST':
        form = MenuItemReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your review has been updated successfully!')
            return redirect('customer:my_reviews')
    else:
        form = MenuItemReviewForm(instance=review)
    
    context = {
        'form': form,
        'review': review,
        'order': review.order,
        'menu_item': review.menu_item,
    }
    return render(request, 'customer/edit_menu_item_review.html', context)


@login_required
def my_reviews(request):
    """
    Display the user's review history with filtering and pagination.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered user reviews page template
    """
    # Get user's restaurant and menu item reviews
    restaurant_reviews = RestaurantReview.objects.filter(user=request.user).select_related('restaurant', 'order')
    menu_item_reviews = MenuItemReview.objects.filter(user=request.user).select_related('menu_item', 'order', 'menu_item__restaurant')
    
    # Filter parameters
    rating_filter = request.GET.get('rating', '')
    review_type = request.GET.get('type', 'all')
    
    # Apply filters
    if rating_filter:
        try:
            rating = int(rating_filter)
            restaurant_reviews = restaurant_reviews.filter(rating=rating)
            menu_item_reviews = menu_item_reviews.filter(rating=rating)
        except ValueError:
            pass
    
    # Pagination
    restaurant_paginator = Paginator(restaurant_reviews, 5)
    menu_item_paginator = Paginator(menu_item_reviews, 5)
    
    restaurant_page = request.GET.get('restaurant_page', 1)
    menu_item_page = request.GET.get('menu_item_page', 1)
    
    restaurant_reviews_page = restaurant_paginator.get_page(restaurant_page)
    menu_item_reviews_page = menu_item_paginator.get_page(menu_item_page)
    
    context = {
        'restaurant_reviews': restaurant_reviews_page,
        'menu_item_reviews': menu_item_reviews_page,
        'rating_filter': rating_filter,
        'review_type': review_type,
    }
    return render(request, 'customer/my_reviews.html', context)


@login_required
def delete_review(request, review_type, review_id):
    """
    Delete a user's review (restaurant or menu item).
    
    Args:
        request: Django HTTP request object
        review_type: Type of review ('restaurant' or 'menu_item')
        review_id: ID of the review to delete
    
    Returns:
        HttpResponse: Redirect after deletion
    """
    if request.method == 'POST':
        if review_type == 'restaurant':
            review = get_object_or_404(RestaurantReview, id=review_id, user=request.user)
        elif review_type == 'menu_item':
            review = get_object_or_404(MenuItemReview, id=review_id, user=request.user)
        else:
            messages.error(request, 'Invalid review type.')
            return redirect('customer:my_reviews')
        
        # Check if review is still editable (within 7 days)
        if not review.is_editable:
            messages.error(request, 'This review can no longer be deleted (7-day limit exceeded).')
            return redirect('customer:my_reviews')
        
        review.delete()
        messages.success(request, 'Your review has been deleted successfully.')
    
    return redirect('customer:my_reviews')


@login_required
def flag_review(request, review_type, review_id):
    """
    Flag a review for moderation.
    
    Args:
        request: Django HTTP request object
        review_type: Type of review ('restaurant' or 'menu_item')
        review_id: ID of the review to flag
    
    Returns:
        HttpResponse: Rendered flag form page or redirect after submission
    """
    if review_type == 'restaurant':
        review = get_object_or_404(RestaurantReview, id=review_id)
    elif review_type == 'menu_item':
        review = get_object_or_404(MenuItemReview, id=review_id)
    else:
        messages.error(request, 'Invalid review type.')
        return redirect('customer:home')
    
    # Check if user already flagged this review
    existing_flag = ReviewFlag.objects.filter(
        flagged_by=request.user,
        **{f'{review_type}_review': review}
    ).first()
    
    if existing_flag:
        messages.info(request, 'You have already flagged this review.')
        return redirect('customer:review_detail', review_type=review_type, review_id=review_id)
    
    if request.method == 'POST':
        form = ReviewFlagForm(request.POST)
        if form.is_valid():
            flag = form.save(commit=False)
            flag.flagged_by = request.user
            if review_type == 'restaurant':
                flag.restaurant_review = review
            else:
                flag.menu_item_review = review
            flag.save()
            
            # Auto-flag the review
            review.is_flagged = True
            review.save()
            
            messages.success(request, 'Review has been flagged for moderation.')
            return redirect('customer:review_detail', review_type=review_type, review_id=review_id)
    else:
        form = ReviewFlagForm()
    
    context = {
        'form': form,
        'review': review,
        'review_type': review_type,
    }
    return render(request, 'customer/flag_review.html', context)


def review_detail(request, review_type, review_id):
    """
    Display detailed review with responses and moderation status.
    
    Args:
        request: Django HTTP request object
        review_type: Type of review ('restaurant' or 'menu_item')
        review_id: ID of the review to display
    
    Returns:
        HttpResponse: Rendered review detail page template
    """
    if review_type == 'restaurant':
        review = get_object_or_404(RestaurantReview.objects.select_related('user', 'restaurant', 'order'), id=review_id)
    elif review_type == 'menu_item':
        review = get_object_or_404(MenuItemReview.objects.select_related('user', 'menu_item', 'order', 'menu_item__restaurant'), id=review_id)
    else:
        messages.error(request, 'Invalid review type.')
        return redirect('customer:home')
    
    # Get responses and flags
    responses = review.responses.filter(is_public=True).select_related('responder')
    flags = review.flags.select_related('flagged_by')
    
    # Check if current user can edit/respond
    can_edit = (request.user.is_authenticated and 
                review.user == request.user and 
                review.is_editable)
    
    can_respond = (request.user.is_authenticated and 
                   ((review_type == 'restaurant' and review.restaurant.owner == request.user) or
                    (review_type == 'menu_item' and review.menu_item.restaurant.owner == request.user)))
    
    context = {
        'review': review,
        'review_type': review_type,
        'responses': responses,
        'flags': flags,
        'can_edit': can_edit,
        'can_respond': can_respond,
    }
    return render(request, 'customer/review_detail.html', context)


@login_required
def create_review_response(request, review_type, review_id):
    """
    Create a response to a review (for restaurant owners).
    
    Args:
        request: Django HTTP request object
        review_type: Type of review ('restaurant' or 'menu_item')
        review_id: ID of the review to respond to
    
    Returns:
        HttpResponse: Rendered response form page or redirect after submission
    """
    if review_type == 'restaurant':
        review = get_object_or_404(RestaurantReview, id=review_id)
        restaurant = review.restaurant
    elif review_type == 'menu_item':
        review = get_object_or_404(MenuItemReview, id=review_id)
        restaurant = review.menu_item.restaurant
    else:
        messages.error(request, 'Invalid review type.')
        return redirect('customer:home')
    
    # Check if user is the restaurant owner
    if restaurant.owner != request.user:
        return HttpResponseForbidden("You don't have permission to respond to this review.")
    
    if request.method == 'POST':
        form = ReviewResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.responder = request.user
            if review_type == 'restaurant':
                response.restaurant_review = review
            else:
                response.menu_item_review = review
            response.save()
            
            messages.success(request, 'Your response has been submitted successfully!')
            return redirect('customer:review_detail', review_type=review_type, review_id=review_id)
    else:
        form = ReviewResponseForm()
    
    context = {
        'form': form,
        'review': review,
        'review_type': review_type,
        'restaurant': restaurant,
    }
    return render(request, 'customer/create_review_response.html', context)


@login_required
def process_payment(request, order_id):
    """
    Display Razorpay payment page for online payment processing.
    
    This view renders the payment interface with Razorpay checkout integration.
    Customer can complete payment using UPI, cards, wallets, or net banking.
    
    Workflow:
    1. Fetch order details and verify it belongs to current user
    2. Verify order has Razorpay order ID
    3. Render payment page with Razorpay checkout script
    4. Customer completes payment on Razorpay interface
    5. Razorpay redirects to verify_payment endpoint
    
    Args:
        request: Django HTTP request object
        order_id: UUID of the order to process payment for
    
    Returns:
        HttpResponse: Rendered payment page with Razorpay integration
    
    Raises:
        Http404: If order doesn't exist or doesn't belong to user
    
    Security:
        - Login required decorator ensures authentication
        - Order ownership verified (user must own the order)
        - Razorpay order ID required to proceed
    
    Note:
        - Payment page uses Razorpay Checkout script
        - Supports multiple payment methods (UPI, cards, wallets)
        - Cart remains intact until payment is verified
        - Failed payments can be retried
    """
    # Fetch order and verify ownership
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Verify order has Razorpay order ID
    if not order.razorpay_order_id:
        messages.error(request, 'Invalid payment session. Please try again.')
        return redirect('customer:checkout')
    
    # Verify order is in correct state for payment
    if order.payment_status not in ['pending', 'processing']:
        messages.info(request, 'This order has already been processed.')
        return redirect('customer:order_success', order_id=order.order_id)
    
    context = {
        'order': order,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'razorpay_order_id': order.razorpay_order_id,
        'amount_in_paise': int(order.total_amount * 100),  # Convert to paise
    }
    return render(request, 'customer/process_payment.html', context)


@login_required
@require_POST
def verify_payment(request):
    """
    Verify Razorpay payment and update order status.
    
    This is the callback endpoint called after payment completion.
    It verifies the payment signature to ensure authenticity and
    updates order status accordingly.
    
    Security Process:
    1. Extract payment details from POST data
    2. Verify payment signature using HMAC-SHA256
    3. Fetch order and verify ownership
    4. Update order with payment details
    5. Mark payment as completed
    6. Send confirmation email
    7. Clear cart
    
    POST Parameters:
        razorpay_payment_id: Payment ID from Razorpay
        razorpay_order_id: Order ID from Razorpay
        razorpay_signature: Payment signature for verification
        order_id: Our internal order UUID
    
    Returns:
        JsonResponse: Success/failure status with redirect URL
    
    Security:
        - CSRF protection via @require_POST decorator
        - Payment signature verification (critical)
        - Order ownership verification
        - All payment details logged for auditing
    
    Note:
        - Returns JSON for AJAX handling
        - Signature verification is mandatory
        - Failed verification doesn't delete order
        - Customer can retry payment
    """
    try:
        from core.payment_utils import verify_razorpay_payment
        
        # Extract payment details from POST data
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        order_id = request.POST.get('order_id')
        
        # Validate all required fields are present
        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature, order_id]):
            return JsonResponse({
                'success': False,
                'error': 'Missing payment verification data'
            }, status=400)
        
        # Fetch order and verify ownership
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
        
        # Verify payment signature (CRITICAL SECURITY CHECK)
        is_valid = verify_razorpay_payment(
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        )
        
        if is_valid:
            # ============================================
            # PAYMENT SUCCESSFUL - Update Order
            # ============================================
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.payment_status = 'completed'
            order.save()
            
            # ============================================
            # AWARD LOYALTY POINTS
            # ============================================
            try:
                from django.utils import timezone
                from datetime import timedelta
                
                # Calculate points: 1 point per ₹10 spent (minimum 10 points)
                points_earned = max(10, int(order.total_amount / 10))
                
                # Get or create user profile
                user_profile, created = UserProfile.objects.get_or_create(
                    user=request.user,
                    defaults={'full_name': request.user.username}
                )
                
                # Calculate new balance
                new_balance = user_profile.points_balance + points_earned
                
                # Create loyalty transaction
                LoyaltyTransaction.objects.create(
                    user=request.user,
                    transaction_type='earned',
                    points=points_earned,
                    balance_after=new_balance,
                    order=order,
                    description=f'Points earned from order #{order.order_id}',
                    expires_at=timezone.now() + timedelta(days=365)  # Points expire in 1 year
                )
                
                # Update user profile balance
                user_profile.points_balance = new_balance
                user_profile.save()
                
                print(f"Loyalty points awarded: {points_earned} points to {request.user.username}")
                
            except Exception as e:
                # Log error but don't fail the payment
                print(f"Failed to award loyalty points: {e}")
                import traceback
                traceback.print_exc()
            
            # Send order confirmation email
            try:
                send_order_confirmation_email(request.user, order)
            except Exception as e:
                print(f"Email sending failed after payment: {e}")
            
            # Clear cart from session
            cart = Cart(request)
            cart.clear()
            
            # Return success response
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('customer:order_success', kwargs={'order_id': order.order_id}),
                'message': 'Payment verified successfully!'
            })
        else:
            # ============================================
            # PAYMENT VERIFICATION FAILED
            # ============================================
            order.payment_status = 'failed'
            order.save()
            
            return JsonResponse({
                'success': False,
                'error': 'Payment verification failed. Please contact support.',
                'redirect_url': reverse('customer:checkout')
            }, status=400)
            
    except Exception as e:
        print(f"Error verifying payment: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while processing your payment.',
            'redirect_url': reverse('customer:checkout')
        }, status=500)


def table_menu(request, uuid):
    """
    Display restaurant menu for a specific table via QR code scan.
    
    This view is accessed when customers scan a QR code on a restaurant table.
    It shows the menu items for that specific restaurant in a mobile-optimized
    format, allowing customers to browse and add items to their cart.
    
    Args:
        request: Django HTTP request object
        uuid: Unique identifier from the QR code (table UUID)
    
    Returns:
        HttpResponse: Rendered table menu page or 404 if table not found
    """
    from restaurant.models import RestaurantTable
    from menu.models import Category, MenuItem
    from django.db.models import Count
    
    # Get the table by UUID
    table = RestaurantTable.get_table_by_uuid(uuid)
    
    if not table:
        # Table not found or inactive
        return render(request, 'customer/table_not_found.html', {
            'message': 'Invalid QR code or table is not active.'
        }, status=404)
    
    restaurant = table.restaurant
    
    # Check if restaurant is active and approved
    if not restaurant.is_active or not restaurant.is_approved:
        return render(request, 'customer/restaurant_unavailable.html', {
            'restaurant': restaurant,
            'message': 'This restaurant is currently unavailable.'
        })
    
    # Get category filter if provided
    category_id = request.GET.get('category')
    search_query = request.GET.get('search', '').strip()
    
    # Get all categories for this restaurant that have available items
    categories = Category.objects.filter(
        items__restaurant=restaurant,
        items__is_available=True,
        is_active=True
    ).annotate(
        item_count=Count('items')
    ).distinct().order_by('display_order', 'name')
    
    # Build menu items query
    menu_items = MenuItem.objects.filter(
        restaurant=restaurant,
        is_available=True
    ).select_related('category')
    
    # Apply category filter
    if category_id:
        menu_items = menu_items.filter(category_id=category_id)
        selected_category = Category.objects.filter(id=category_id).first()
    else:
        selected_category = None
    
    # Apply search filter
    if search_query:
        menu_items = menu_items.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Order menu items
    menu_items = menu_items.order_by('category__display_order', 'category__name', 'name')
    
    # Get cart item count for display (works for both logged-in and guest users)
    from customer.cart import Cart
    cart = Cart(request)
    cart_count = len(cart)
    
    # Check if restaurant is currently open
    is_open = restaurant.is_open()
    
    context = {
        'table': table,
        'restaurant': restaurant,
        'categories': categories,
        'menu_items': menu_items,
        'selected_category': selected_category,
        'search_query': search_query,
        'cart_count': cart_count,
        'is_open': is_open,
        'is_table_view': True,  # Flag to indicate this is table view
    }
    
    return render(request, 'customer/table_menu.html', context)


@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def guest_checkout(request, uuid):
    """
    Handle guest checkout for QR table ordering.
    
    This view allows customers to place orders without login and receive
    their bill via email or SMS. It processes the cart items, creates an
    order with guest contact information, and triggers bill delivery.
    
    Args:
        request: Django HTTP request object
        uuid: Unique identifier for the restaurant table
    
    Returns:
        HttpResponse: Guest checkout page or redirect after order placement
    """
    from restaurant.models import RestaurantTable
    from .cart import Cart
    from .forms import GuestCheckoutForm
    
    # Get the table by UUID
    table = RestaurantTable.get_table_by_uuid(uuid)
    if not table:
        return render(request, 'customer/table_not_found.html', {
            'message': 'Invalid QR code or table is not active.'
        }, status=404)
    
    restaurant = table.restaurant
    
    # Check if restaurant is active and approved
    if not restaurant.is_active or not restaurant.is_approved:
        return render(request, 'customer/restaurant_unavailable.html', {
            'restaurant': restaurant,
            'message': 'This restaurant is currently unavailable.'
        })
    
    # Get cart and check if it has items
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty. Please add items to your order.')
        return redirect('customer:table_menu', uuid=uuid)
    
    # Prevent duplicate orders within 5 minutes using session-based cache
    if not request.session.session_key:
        request.session.create()  # Create session if it doesn't exist
    cache_key = f'guest_order_{request.session.session_key}_{table.id}'
    if cache.get(cache_key):
        messages.error(request, 'Please wait before placing another order. You can place a new order in 5 minutes.')
        return redirect('customer:table_menu', uuid=uuid)
    
    # Validate all cart items belong to this restaurant and are still available
    unavailable_items = []
    for item in cart:
        try:
            menu_item = item['menu_item']
            if menu_item.restaurant != restaurant:
                messages.error(request, 'Your cart contains items from a different restaurant.')
                cart.clear()
                return redirect('customer:table_menu', uuid=uuid)
            if not menu_item.is_available:
                unavailable_items.append(menu_item.name)
        except MenuItem.DoesNotExist:
            messages.error(request, 'Some items in your cart are no longer available.')
            cart.clear()
            return redirect('customer:table_menu', uuid=uuid)
    
    if unavailable_items:
        messages.warning(request, f'The following items are no longer available: {", ".join(unavailable_items)}. Please remove them from your cart.')
        return redirect('customer:table_menu', uuid=uuid)
    
    if request.method == 'POST':
        form = GuestCheckoutForm(request.POST)
        if form.is_valid():
            # Create order with guest information
            order = create_guest_order(request, table, cart, form)
            
            # Set cache to prevent duplicate orders for 5 minutes
            cache_key = f'guest_order_{request.session.session_key}_{table.id}'
            cache.set(cache_key, True, 300)  # 5 minutes cooldown
            
            # Clear cart after successful order creation
            cart.clear()
            
            # Send bill via email/SMS
            send_guest_bill(order, form)
            
            messages.success(request, 
                f'Order placed successfully! Your bill will be sent to you shortly. '
                f'Order ID: {str(order.order_id)[:8]}'
            )
            
            return redirect('customer:guest_order_success', uuid=uuid, order_id=order.order_id)
    else:
        form = GuestCheckoutForm()
    
    context = {
        'table': table,
        'restaurant': restaurant,
        'cart': cart,
        'form': form,
        'cart_total': cart.get_total_price(),
        'cart_count': len(cart),
    }
    
    return render(request, 'customer/guest_checkout.html', context)


def create_guest_order(request, table, cart, form):
    """
    Create an order for a guest customer with bill delivery information.
    
    This function creates an Order instance with guest contact details,
    processes all cart items into order items, and sets up the order
    for QR table ordering workflow.
    
    Args:
        request: Django HTTP request object
        table: RestaurantTable instance
        cart: Cart instance with items
        form: Validated GuestCheckoutForm instance
    
    Returns:
        Order: Created order instance with guest information
    """
    from orders.models import Order, OrderItem
    
    # Get delivery information from form
    delivery_info = form.get_delivery_info()
    
    # Create order with guest information
    order = Order.objects.create(
        user=None,  # Guest order - no user
        table=table,
        order_type='qr_code',
        is_table_order=True,
        customer_name=delivery_info['name'],
        customer_phone=delivery_info['phone'] or 'N/A',
        customer_address='',  # Not applicable for table orders
        guest_email=delivery_info['email'],
        guest_phone=delivery_info['phone'],
        delivery_method='dine_in',  # Table orders are dine-in
        total_amount=cart.get_total_price(),
        status='pending',
        notes=form.cleaned_data.get('notes', '')
    )
    
    # Create order items from cart
    for item in cart:
        OrderItem.objects.create(
            order=order,
            menu_item=item['menu_item'],
            quantity=item['quantity'],
            price=item['price'],
            subtotal=item['subtotal']
        )
    
    return order


def send_guest_bill(order, form):
    """
    Send bill PDF to guest customer via email and/or SMS.
    
    This function generates a PDF bill and sends it to the guest
    customer based on their selected delivery preferences.
    
    Args:
        order: Order instance with guest information
        form: Validated GuestCheckoutForm with delivery preferences
    
    Returns:
        bool: True if bill was sent successfully, False otherwise
    """
    from django.core.mail import EmailMessage
    from django.conf import settings
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    
    delivery_info = form.get_delivery_info()
    
    try:
        # Generate PDF bill
        pdf_buffer = generate_bill_pdf(order)
        
        # Send via email if requested
        if delivery_info['email']:
            email = EmailMessage(
                subject=f'Your Restaurant Bill - Order #{str(order.order_id)[:8]}',
                body=f'''
                Dear {delivery_info['name']},
                
                Thank you for dining with us! Your bill is attached as a PDF.
                
                Order Details:
                - Order ID: {str(order.order_id)[:8]}
                - Table: {order.table.table_number}
                - Restaurant: {order.table.restaurant.name}
                - Total Amount: ₹{order.total_amount}
                
                We hope you enjoyed your meal!
                
                Best regards,
                {order.table.restaurant.name}
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[delivery_info['email']]
            )
            
            # Attach PDF if generated successfully, otherwise send plain text bill
            if pdf_buffer and pdf_buffer.getbuffer().nbytes > 0:
                email.attach(f'bill_{order.order_id}.pdf', pdf_buffer.getvalue(), 'application/pdf')
            else:
                # Fallback: add plain text bill to email body
                email.body += f'''
                
                ==================== BILL DETAILS ====================
                
                Order Items:
                {chr(10).join([f"- {item.menu_item.name} x{item.quantity}: ₹{item.subtotal}" for item in order.items.all()])}
                
                Total Amount: ₹{order.total_amount}
                
                ==================== END BILL ====================
                '''
            
            email.send()
        
        # Send via SMS if requested (placeholder - would need SMS service integration)
        if delivery_info['phone']:
            # SMS integration would go here
            # For now, we'll just log that SMS would be sent
            print(f"SMS would be sent to {delivery_info['phone']} with bill link")
        
        return True
        
    except Exception as e:
        print(f"Error sending guest bill: {e}")
        
        # Fallback: try to send plain text email if PDF generation failed
        try:
            if delivery_info['email']:
                plain_text_bill = f'''
                Dear {delivery_info['name']},
                
                Thank you for dining with us! Please find your bill details below:
                
                Order ID: {str(order.order_id)[:8]}
                Table: {order.table.table_number}
                Restaurant: {order.table.restaurant.name}
                Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}
                
                Order Items:
                {chr(10).join([f"- {item.menu_item.name} x{item.quantity}: ₹{item.subtotal}" for item in order.items.all()])}
                
                Total Amount: ₹{order.total_amount}
                
                We hope you enjoyed your meal!
                
                Best regards,
                {order.table.restaurant.name}
                '''
                
                send_mail(
                    subject=f'Your Restaurant Bill - Order #{str(order.order_id)[:8]}',
                    message=plain_text_bill,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[delivery_info['email']],
                    fail_silently=False
                )
                return True
        except Exception as fallback_error:
            print(f"Fallback email also failed: {fallback_error}")
        
        return False


def generate_bill_pdf(order):
    """
    Generate a PDF bill for the order.
    
    This function creates a professional PDF bill with order details,
    itemized list, and pricing information suitable for customer delivery.
    
    Args:
        order: Order instance to generate bill for
    
    Returns:
        BytesIO: PDF buffer containing the generated bill
    """
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 20)
    p.drawString(inch, height - inch, "RESTAURANT BILL")
    
    # Restaurant info
    p.setFont("Helvetica", 12)
    p.drawString(inch, height - 1.5*inch, f"Restaurant: {order.table.restaurant.name}")
    p.drawString(inch, height - 1.7*inch, f"Table: {order.table.table_number}")
    p.drawString(inch, height - 1.9*inch, f"Order ID: {str(order.order_id)[:8]}")
    p.drawString(inch, height - 2.1*inch, f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}")
    
    # Customer info
    p.drawString(inch, height - 2.5*inch, f"Customer: {order.customer_name}")
    if order.guest_email:
        p.drawString(inch, height - 2.7*inch, f"Email: {order.guest_email}")
    if order.guest_phone:
        p.drawString(inch, height - 2.9*inch, f"Phone: {order.guest_phone}")
    
    # Line separator
    p.line(inch, height - 3.2*inch, width - inch, height - 3.2*inch)
    
    # Items header
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 3.5*inch, "Item")
    p.drawString(width - 4*inch, height - 3.5*inch, "Qty")
    p.drawString(width - 3*inch, height - 3.5*inch, "Price")
    p.drawString(width - inch, height - 3.5*inch, "Total")
    
    # Items
    y_position = height - 3.8*inch
    p.setFont("Helvetica", 10)
    
    for item in order.items.all():
        item_name = item.menu_item.name[:30]  # Truncate long names
        p.drawString(inch, y_position, item_name)
        p.drawString(width - 4*inch, y_position, str(item.quantity))
        p.drawString(width - 3*inch, y_position, f"₹{item.price}")
        p.drawString(width - inch, y_position, f"₹{item.subtotal}")
        y_position -= 0.3*inch
    
    # Line separator
    p.line(inch, y_position - 0.2*inch, width - inch, y_position - 0.2*inch)
    
    # Total
    p.setFont("Helvetica-Bold", 14)
    p.drawString(width - 2*inch, y_position - 0.6*inch, f"Total: ₹{order.total_amount}")
    
    # Footer
    p.setFont("Helvetica", 10)
    p.drawString(inch, inch, "Thank you for dining with us!")
    
    p.save()
    buffer.seek(0)
    return buffer


def guest_order_success(request, uuid, order_id):
    """
    Display success page after guest order placement.
    
    This view shows a confirmation page to guest customers after
    they successfully place an order via QR code scanning.
    
    Args:
        request: Django HTTP request object
        uuid: Unique identifier for the restaurant table
        order_id: UUID of the created order
    
    Returns:
        HttpResponse: Order success confirmation page
    """
    from restaurant.models import RestaurantTable
    from orders.models import Order
    
    # Get the table and order
    table = RestaurantTable.get_table_by_uuid(uuid)
    order = get_object_or_404(Order, order_id=order_id)
    
    context = {
        'table': table,
        'order': order,
        'restaurant': table.restaurant,
    }
    
    return render(request, 'customer/guest_order_success.html', context)
