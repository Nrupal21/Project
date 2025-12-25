"""
Restaurant app views.
Handles restaurant dashboard, login, order management, and manager approval system.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, Avg, F, ExpressionWrapper, FloatField
from django.utils import timezone
from datetime import timedelta, date
from django.http import JsonResponse, HttpResponse
from django.db.models.functions import TruncDate, TruncMonth, ExtractHour
from django.core.serializers.json import DjangoJSONEncoder
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.paginator import Paginator
import json
import re
import csv
import io
import functools
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

# Import menu models and forms
from menu.models import MenuItem, Category
from menu.forms import MenuItemForm, CategoryForm, MenuItemBulkUpdateForm

# Import order and restaurant models
from orders.models import Order, OrderItem
from menu.models import MenuItem
from .models import Restaurant, PendingRestaurant, ManagerLoginLog, MarketingCampaign, RestaurantTable
from .forms import RestaurantLoginForm, MarketingCampaignForm

# Import notification service
from core.notifications import send_order_notification


def get_selected_restaurant(request):
    """
    Get the currently selected restaurant for a multi-restaurant owner.
    
    This function handles restaurant selection for owners with multiple restaurants:
    - Checks session for selected restaurant ID
    - Validates the restaurant belongs to the user
    - Redirects to selection page if no restaurant is selected
    - Returns the restaurant object for single-restaurant owners
    
    Args:
        request: Django HTTP request object
    
    Returns:
        Restaurant: The selected restaurant object
        
    Raises:
        Restaurant.DoesNotExist: If selected restaurant doesn't belong to user
        None: If user has no restaurants
    """
    # Get all restaurants owned by the user
    user_restaurants = Restaurant.objects.filter(owner=request.user)
    
    if not user_restaurants.exists():
        return None
    
    # If user has multiple restaurants, check for selection in session
    if user_restaurants.count() > 1:
        selected_restaurant_id = request.session.get('selected_restaurant_id')
        if selected_restaurant_id:
            try:
                return user_restaurants.get(id=selected_restaurant_id)
            except Restaurant.DoesNotExist:
                # Invalid selection - will be handled by calling view
                return None
        else:
            # No restaurant selected
            return None
    else:
        # Single restaurant owner
        return user_restaurants.first()

# Optional PDF generation - make reportlab import optional
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


# Restaurant Owner Decorator
def restaurant_owner_required(view_func):
    """
    Decorator to ensure the user is a restaurant owner and owns the specific restaurant.
    
    Args:
        view_func: The view function to wrap
    
    Returns:
        function: Wrapped view function with ownership validation
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access this page.')
            return redirect('core:login')
        
        # Check if user has a restaurant - use the correct related_name 'restaurants'
        if not hasattr(request.user, 'restaurants') or not request.user.restaurants.exists():
            messages.error(request, 'You must be a restaurant owner to access this page.')
            return redirect('customer:home')
        
        # For views that need specific restaurant ownership
        if 'restaurant_id' in kwargs:
            restaurant_id = kwargs['restaurant_id']
            if not request.user.restaurants.filter(id=restaurant_id).exists():
                messages.error(request, 'You can only manage your own restaurant.')
                return redirect('restaurant:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def get_date_range_filter(date_range):
    """
    Get start and end dates based on date range selection.
    
    Args:
        date_range (str): Date range option ('today', 'week', 'month', 'quarter', 'year')
    
    Returns:
        tuple: (start_date, end_date) datetime objects
    """
    now = timezone.now()
    
    if date_range == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif date_range == 'week':
        start_date = now - timedelta(days=7)
        end_date = now
    elif date_range == 'month':
        start_date = now - timedelta(days=30)
        end_date = now
    elif date_range == 'quarter':
        start_date = now - timedelta(days=90)
        end_date = now
    elif date_range == 'year':
        start_date = now - timedelta(days=365)
        end_date = now
    else:
        # Default to last 30 days
        start_date = now - timedelta(days=30)
        end_date = now
    
    return start_date, end_date


def generate_report_data(report_type, date_range):
    """
    Generate report data based on report type and date range.
    
    Args:
        report_type (str): Type of report ('revenue', 'orders', 'restaurants', 'users')
        date_range (str): Date range for the report
    
    Returns:
        dict: Report data with statistics and detailed records
    """
    start_date, end_date = get_date_range_filter(date_range)
    
    if report_type == 'revenue':
        # Revenue analysis report
        orders_in_range = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        daily_revenue = orders_in_range.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            revenue=Sum('total_amount'),
            order_count=Count('id')
        ).order_by('date')
        
        total_revenue = orders_in_range.aggregate(total=Sum('total_amount'))['total'] or 0
        total_orders = orders_in_range.count()
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return {
            'daily_data': list(daily_revenue),
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'avg_order_value': avg_order_value,
            'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        }
    
    elif report_type == 'orders':
        # Order statistics report
        orders_in_range = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        status_breakdown = orders_in_range.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        delivery_breakdown = orders_in_range.values('delivery_method').annotate(
            count=Count('id'),
            revenue=Sum('total_amount')
        ).order_by('-revenue')
        
        return {
            'status_breakdown': list(status_breakdown),
            'delivery_breakdown': list(delivery_breakdown),
            'total_orders': orders_in_range.count(),
            'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        }
    
    elif report_type == 'restaurants':
        # Restaurant performance report
        restaurants = Restaurant.objects.filter(is_active=True)
        
        restaurant_stats = []
        for restaurant in restaurants:
            restaurant_orders = Order.objects.filter(
                items__menu_item__restaurant=restaurant,
                created_at__gte=start_date,
                created_at__lte=end_date
            ).distinct()
            
            revenue = restaurant_orders.aggregate(total=Sum('total_amount'))['total'] or 0
            order_count = restaurant_orders.count()
            
            restaurant_stats.append({
                'name': restaurant.name,
                'owner': restaurant.owner.username if restaurant.owner else 'N/A',
                'revenue': revenue,
                'order_count': order_count,
                'avg_order_value': revenue / order_count if order_count > 0 else 0
            })
        
        restaurant_stats.sort(key=lambda x: x['revenue'], reverse=True)
        
        return {
            'restaurant_stats': restaurant_stats,
            'total_restaurants': len(restaurant_stats),
            'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        }
    
    elif report_type == 'users':
        # User activity report
        users = User.objects.all()
        
        user_stats = {
            'total_users': users.count(),
            'active_users': users.filter(last_login__gte=start_date).count(),
            'new_users': users.filter(date_joined__gte=start_date).count(),
            'restaurant_owners': Restaurant.objects.filter(is_active=True).count(),
        }
        
        # Recent user registrations
        recent_users = users.filter(
            date_joined__gte=start_date,
            date_joined__lte=end_date
        ).order_by('-date_joined')[:20]
        
        return {
            'user_stats': user_stats,
            'recent_users': [
                {
                    'username': user.username,
                    'email': user.email,
                    'date_joined': user.date_joined.strftime('%Y-%m-%d'),
                    'last_login': user.last_login.strftime('%Y-%m-%d') if user.last_login else 'Never'
                }
                for user in recent_users
            ],
            'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        }
    
    return {}


def export_csv_report(report_data, report_type):
    """
    Export report data as CSV file.
    
    Args:
        report_data (dict): Report data from generate_report_data
        report_type (str): Type of report
    
    Returns:
        HttpResponse: CSV file response
    """
    response = HttpResponse(content_type='text/csv')
    filename = f"{report_type}_report_{timezone.now().strftime('%Y%m%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    if report_type == 'revenue':
        writer.writerow(['Date', 'Revenue', 'Order Count'])
        for row in report_data['daily_data']:
            writer.writerow([row['date'], row['revenue'], row['order_count']])
        
        writer.writerow([])
        writer.writerow(['Summary'])
        writer.writerow(['Total Revenue', report_data['total_revenue']])
        writer.writerow(['Total Orders', report_data['total_orders']])
        writer.writerow(['Average Order Value', report_data['avg_order_value']])
    
    elif report_type == 'orders':
        writer.writerow(['Status', 'Count'])
        for row in report_data['status_breakdown']:
            writer.writerow([row['status'], row['count']])
        
        writer.writerow([])
        writer.writerow(['Delivery Method', 'Count', 'Revenue'])
        for row in report_data['delivery_breakdown']:
            writer.writerow([row['delivery_method'], row['count'], row['revenue']])
    
    elif report_type == 'restaurants':
        writer.writerow(['Restaurant Name', 'Owner', 'Revenue', 'Order Count', 'Average Order Value'])
        for row in report_data['restaurant_stats']:
            writer.writerow([
                row['name'], row['owner'], row['revenue'], 
                row['order_count'], row['avg_order_value']
            ])
    
    elif report_type == 'users':
        writer.writerow(['Username', 'Email', 'Date Joined', 'Last Login'])
        for row in report_data['recent_users']:
            writer.writerow([row['username'], row['email'], row['date_joined'], row['last_login']])
        
        writer.writerow([])
        writer.writerow(['Summary'])
        writer.writerow(['Total Users', report_data['user_stats']['total_users']])
        writer.writerow(['Active Users', report_data['user_stats']['active_users']])
        writer.writerow(['New Users', report_data['user_stats']['new_users']])
        writer.writerow(['Restaurant Owners', report_data['user_stats']['restaurant_owners']])
    
    return response


def send_bulk_email_campaign(target_audience, email_template, custom_message=None):
    """
    Send bulk email campaign to specified audience.
    
    Args:
        target_audience (str): Target audience group
        email_template (str): Email template type
        custom_message (str): Custom message for custom template
    
    Returns:
        dict: Results of the email campaign
    """
    # Get recipients based on target audience
    if target_audience == 'all_users':
        recipients = User.objects.filter(is_active=True, email__isnull=False)
    elif target_audience == 'restaurant_owners':
        recipients = User.objects.filter(
            restaurant__is_active=True, 
            email__isnull=False
        ).distinct()
    elif target_audience == 'active_customers':
        # Users who have placed orders
        recipients = User.objects.filter(
            order__isnull=False,
            email__isnull=False
        ).distinct()
    elif target_audience == 'inactive_users':
        # Users who haven't logged in in 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        recipients = User.objects.filter(
            last_login__lt=cutoff_date,
            email__isnull=False
        )
    else:
        recipients = User.objects.none()
    
    # Prepare email content
    subject, message = prepare_email_content(email_template, custom_message)
    
    # Send emails
    sent_count = 0
    failed_count = 0
    
    for user in recipients:
        try:
            send_mail(
                subject,
                message,
                'noreply@foodordering.com',  # From email
                [user.email],
                fail_silently=False,
            )
            sent_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Failed to send email to {user.email}: {e}")
    
    return {
        'sent_count': sent_count,
        'failed_count': failed_count,
        'total_recipients': recipients.count()
    }


def prepare_email_content(email_template, custom_message=None):
    """
    Prepare email subject and message based on template.
    
    Args:
        email_template (str): Email template type
        custom_message (str): Custom message for custom template
    
    Returns:
        tuple: (subject, message)
    """
    if email_template == 'promotion':
        subject = "🍔 Special Offer - 20% Off Your Next Order!"
        message = """Dear Customer,

We're excited to offer you a special 20% discount on your next order!
Use code: SPECIAL20

Valid for the next 7 days only.

Best regards,
The Food Ordering Team"""
    
    elif email_template == 'announcement':
        subject = "📢 Important System Announcement"
        message = """Dear User,

We have some exciting updates to share with you!
Our platform has been enhanced with new features and improvements.

Thank you for being a valued member of our community.

Best regards,
The Food Ordering Team"""
    
    elif email_template == 'survey':
        subject = "📋 We'd Love Your Feedback"
        message = """Dear Customer,

Your opinion matters to us! Please take a moment to complete our short survey
about your experience with our food ordering platform.

Your feedback helps us serve you better.

Best regards,
The Food Ordering Team"""
    
    elif email_template == 'custom' and custom_message:
        subject = "Message from Food Ordering Team"
        message = custom_message
    
    else:
        subject = "Update from Food Ordering Team"
        message = "Hello! We have an update for you from the Food Ordering Team."
    
    return subject, message


def restaurant_login(request):
    """
    Handle restaurant staff login.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered login page or redirect to dashboard
    """
    if request.user.is_authenticated:
        return redirect('restaurant:dashboard')
    
    if request.method == 'POST':
        form = RestaurantLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('restaurant:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = RestaurantLoginForm()
    
    return render(request, 'restaurant/login.html', {'form': form})


@login_required
def restaurant_logout(request):
    """
    Handle restaurant staff logout.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Redirect to customer home page
    """
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('customer:home')


@login_required
def dashboard(request):
    """
    Display comprehensive restaurant owner dashboard with detailed analytics.
    Includes sales analytics, revenue tracking, menu performance insights, and order statistics.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered dashboard page template with analytics data
    """
    # Handle restaurant selection for multi-restaurant owners
    user_restaurant = get_selected_restaurant(request)
    
    if not user_restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'You are not associated with any restaurant.')
            return redirect('customer:home')
    
    # Get date ranges for analytics
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Get date filter from request
    date_filter = request.GET.get('date_filter', 'today')
    if date_filter == 'today':
        start_date = today
    elif date_filter == 'week':
        start_date = week_ago
    elif date_filter == 'month':
        start_date = month_ago
    else:
        start_date = today
    
    # Base order queryset for the date range AND restaurant-specific filtering
    orders_in_range = Order.objects.filter(
        created_at__date__gte=start_date,
        items__menu_item__restaurant=user_restaurant
    ).distinct()
    
    # === SALES ANALYTICS ===
    # Order statistics
    total_orders_all_time = Order.objects.filter(
        items__menu_item__restaurant=user_restaurant
    ).distinct().count()
    orders_in_period = orders_in_range.count()
    orders_today = Order.objects.filter(
        created_at__date=today,
        items__menu_item__restaurant=user_restaurant
    ).distinct().count()
    
    # Order status distribution
    status_stats = orders_in_range.values('status').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('status')
    
    # Daily sales trend (last 7 days)
    daily_sales = Order.objects.filter(
        created_at__date__gte=week_ago,
        items__menu_item__restaurant=user_restaurant
    ).distinct().annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        order_count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('date')
    
    # Monthly sales trend (last 6 months)
    monthly_sales = Order.objects.filter(
        created_at__date__gte=today - timedelta(days=180),
        items__menu_item__restaurant=user_restaurant
    ).distinct().annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        order_count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('month')
    
    # === REVENUE TRACKING ===
    # Revenue calculations
    total_revenue_all_time = Order.objects.filter(
        items__menu_item__restaurant=user_restaurant
    ).distinct().aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    revenue_in_period = orders_in_range.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    revenue_today = Order.objects.filter(
        created_at__date=today,
        items__menu_item__restaurant=user_restaurant
    ).distinct().aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    revenue_yesterday = Order.objects.filter(
        created_at__date=yesterday,
        items__menu_item__restaurant=user_restaurant
    ).distinct().aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Revenue growth
    revenue_growth = 0
    if revenue_yesterday > 0:
        revenue_growth = ((revenue_today - revenue_yesterday) / revenue_yesterday) * 100
    
    # Average order value
    avg_order_value = orders_in_range.aggregate(
        avg=Avg('total_amount')
    )['avg'] or 0
    
    # Delivery method breakdown
    delivery_stats = orders_in_range.values('delivery_method').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('-revenue')
    
    # === MENU PERFORMANCE INSIGHTS ===
    # Best selling items
    best_selling_items = OrderItem.objects.filter(
        order__created_at__date__gte=start_date,
        menu_item__restaurant=user_restaurant
    ).values(
        'menu_item__id',
        'menu_item__name',
        'menu_item__price'
    ).annotate(
        total_sold=Sum('quantity'),
        revenue=ExpressionWrapper(
            F('menu_item__price') * F('total_sold'),
            output_field=FloatField()
        )
    ).order_by('-total_sold')[:10]
    
    # Worst selling items (items with sales)
    worst_selling_items = OrderItem.objects.filter(
        order__created_at__date__gte=start_date,
        menu_item__restaurant=user_restaurant,
        quantity__gt=0
    ).values(
        'menu_item__id',
        'menu_item__name',
        'menu_item__price'
    ).annotate(
        total_sold=Sum('quantity'),
        revenue=ExpressionWrapper(
            F('menu_item__price') * F('total_sold'),
            output_field=FloatField()
        )
    ).order_by('total_sold')[:10]
    
    # Category performance
    category_performance = OrderItem.objects.filter(
        order__created_at__date__gte=start_date,
        menu_item__restaurant=user_restaurant
    ).values(
        'menu_item__category__name'
    ).annotate(
        total_sold=Sum('quantity'),
        revenue=Sum(F('menu_item__price') * F('quantity'))
    ).order_by('-revenue')
    
    # Unavailable items (items that customers can't order)
    unavailable_items = MenuItem.objects.filter(
        restaurant=user_restaurant,
        is_available=False
    ).select_related('category').order_by('name')[:10]
    
    # === ORDER STATISTICS ===
    # Order completion time analysis
    delivered_orders = Order.objects.filter(
        status='delivered',
        created_at__date__gte=start_date,
        items__menu_item__restaurant=user_restaurant
    ).distinct()
    
    # Calculate average time to deliver (in hours since order creation)
    import datetime
    
    avg_completion_time = 0
    if delivered_orders.exists():
        total_time = 0
        for order in delivered_orders:
            if order.updated_at and order.created_at:
                time_diff = order.updated_at - order.created_at
                total_time += time_diff.total_seconds() / 3600  # Convert to hours
        
        avg_completion_time = total_time / delivered_orders.count()
    
    # Customer satisfaction (ratings)
    from customer.models import RestaurantReview
    recent_reviews = RestaurantReview.objects.filter(
        restaurant=user_restaurant,
        created_at__date__gte=start_date
    ).aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id')
    )
    
    # Peak hours analysis
    peak_hours = Order.objects.filter(
        created_at__date__gte=start_date,
        items__menu_item__restaurant=user_restaurant
    ).distinct().annotate(
        hour=ExtractHour('created_at')
    ).values('hour').annotate(
        order_count=Count('id')
    ).order_by('-order_count')[:6]
    
    # Recent orders for display
    recent_orders = Order.objects.filter(
        items__menu_item__restaurant=user_restaurant
    ).distinct().select_related('user').order_by('-created_at')[:10]
    
    # === PROMO CODE STATISTICS ===
    # Import promo code models
    from orders.models import PromoCode, PromoCodeUsage
    
    # Calculate promo code statistics
    now = timezone.now()
    
    # Active promo codes (current date between start and end dates)
    active_promo_codes = PromoCode.objects.filter(
        restaurant=user_restaurant,
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).count()
    
    # Total promo codes created by this restaurant
    total_promo_codes = PromoCode.objects.filter(
        restaurant=user_restaurant
    ).count()
    
    # Total redemptions/usage count
    total_redemptions = PromoCodeUsage.objects.filter(
        promo_code__restaurant=user_restaurant
    ).count()
    
    # Expiring soon promo codes (within 7 days)
    expiring_soon_date = now + timedelta(days=7)
    expiring_soon_promo_codes = PromoCode.objects.filter(
        restaurant=user_restaurant,
        is_active=True,
        end_date__gte=now,
        end_date__lte=expiring_soon_date
    ).count()
    
    # Total discount given through promo codes
    total_discount_given = PromoCodeUsage.objects.filter(
        promo_code__restaurant=user_restaurant
    ).aggregate(
        total=Sum('discount_amount')
    )['total'] or 0
    
    # === SEASONAL PROMOTION STATISTICS ===
    # Import seasonal promotion models
    from orders.models import SeasonalPromotion
    
    # Active seasonal promotions for this restaurant
    active_seasonal_promotions = SeasonalPromotion.objects.filter(
        restaurants=user_restaurant,
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).count()
    
    # Total seasonal promotions created for this restaurant
    total_seasonal_promotions = SeasonalPromotion.objects.filter(
        restaurants=user_restaurant
    ).count()
    
    # Upcoming seasonal promotions (starting in next 7 days)
    upcoming_date = now + timedelta(days=7)
    upcoming_seasonal_promotions = SeasonalPromotion.objects.filter(
        restaurants=user_restaurant,
        is_active=True,
        start_date__gt=now,
        start_date__lte=upcoming_date
    ).count()
    
    # Total promo codes generated from seasonal promotions
    # Get all seasonal promotions for this restaurant and count their generated codes
    seasonal_promotions_for_restaurant = SeasonalPromotion.objects.filter(
        restaurants=user_restaurant
    )
    
    total_seasonal_codes = 0
    for promotion in seasonal_promotions_for_restaurant:
        # Count promo codes that match this promotion's code prefix
        total_seasonal_codes += PromoCode.objects.filter(
            code__startswith=promotion.code_prefix
        ).count()
    
    # === TABLE MANAGEMENT STATISTICS (QR CODE SYSTEM) ===
    from .models import RestaurantTable
    
    # Total tables for this restaurant
    total_tables = RestaurantTable.objects.filter(
        restaurant=user_restaurant
    ).count()
    
    # Active tables (available for QR code scanning)
    active_tables = RestaurantTable.objects.filter(
        restaurant=user_restaurant,
        is_active=True
    ).count()
    
    # Inactive tables
    inactive_tables = RestaurantTable.objects.filter(
        restaurant=user_restaurant,
        is_active=False
    ).count()
    
    # Tables with QR codes generated
    tables_with_qr = RestaurantTable.objects.filter(
        restaurant=user_restaurant,
        qr_code__isnull=False
    ).exclude(qr_code='').count()
    
    # Recent tables (created in last 7 days)
    recent_tables = RestaurantTable.objects.filter(
        restaurant=user_restaurant,
        created_at__gte=week_ago
    ).count()
    
    # Get list of recent tables for display
    latest_tables = RestaurantTable.objects.filter(
        restaurant=user_restaurant
    ).order_by('-created_at')[:5]
    
    # Calculate table utilization percentage
    table_utilization = 0
    if total_tables > 0:
        table_utilization = (active_tables / total_tables) * 100
    
    # === QR CODE ORDERING STATISTICS ===
    # QR code orders for the restaurant
    qr_orders_all_time = Order.objects.filter(
        order_type='qr_code',
        items__menu_item__restaurant=user_restaurant
    ).distinct().count()
    
    qr_orders_today = Order.objects.filter(
        order_type='qr_code',
        created_at__date=today,
        items__menu_item__restaurant=user_restaurant
    ).distinct().count()
    
    qr_orders_in_period = orders_in_range.filter(order_type='qr_code').count()
    
    # QR code revenue
    qr_revenue_all_time = Order.objects.filter(
        order_type='qr_code',
        items__menu_item__restaurant=user_restaurant
    ).distinct().aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    qr_revenue_today = Order.objects.filter(
        order_type='qr_code',
        created_at__date=today,
        items__menu_item__restaurant=user_restaurant
    ).distinct().aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    qr_revenue_in_period = orders_in_range.filter(order_type='qr_code').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Staff orders (for comparison)
    staff_orders_today = Order.objects.filter(
        order_type='staff',
        created_at__date=today,
        items__menu_item__restaurant=user_restaurant
    ).distinct().count()
    
    # Active table orders (pending, accepted, preparing)
    active_table_orders = Order.objects.filter(
        is_table_order=True,
        status__in=['pending', 'accepted', 'preparing'],
        items__menu_item__restaurant=user_restaurant
    ).distinct().order_by('-created_at')
    
    # Orders needing payment completion
    orders_needing_payment = Order.objects.filter(
        is_table_order=True,
        status='delivered',
        payment_status='pending',
        items__menu_item__restaurant=user_restaurant
    ).distinct().order_by('-created_at')
    
    # Recent table orders for dashboard display
    recent_table_orders = Order.objects.filter(
        is_table_order=True,
        items__menu_item__restaurant=user_restaurant
    ).distinct().select_related('table').prefetch_related('items__menu_item').order_by('-created_at')[:5]
    
    # Table status summary (reuse from active_tables_view logic)
    tables_status_summary = []
    for table in RestaurantTable.objects.filter(restaurant=user_restaurant):
        active_orders = Order.objects.filter(
            table=table,
            status__in=['pending', 'accepted', 'preparing']
        ).distinct().count()
        
        completed_orders = Order.objects.filter(
            table=table,
            status='delivered',
            payment_status='pending'
        ).distinct().count()
        
        status = 'available'
        if active_orders > 0:
            status = 'occupied'
        if completed_orders > 0:
            status = 'needs-attention'
            
        tables_status_summary.append({
            'table': table,
            'status': status,
            'active_orders_count': active_orders,
            'needs_attention': completed_orders > 0
        })
    
    # Table status counts
    available_tables = sum(1 for t in tables_status_summary if t['status'] == 'available')
    occupied_tables = sum(1 for t in tables_status_summary if t['status'] == 'occupied')
    needs_attention_tables = sum(1 for t in tables_status_summary if t['status'] == 'needs-attention')
    
    # === POS TABLE VIEW DATA ===
    # Organize tables by sections for POS view (A/C, Non A/C, Bar)
    tables_by_section = {}
    
    # Initialize sections
    tables_by_section['ac'] = {
        'name': 'A/C',
        'tables': [],
        'available_count': 0,
        'occupied_count': 0,
        'attention_count': 0,
        'stats': {'available': 0, 'occupied': 0, 'reserved': 0, 'needs_attention': 0}
    }
    
    tables_by_section['non_ac'] = {
        'name': 'Non A/C', 
        'tables': [],
        'available_count': 0,
        'occupied_count': 0,
        'attention_count': 0,
        'stats': {'available': 0, 'occupied': 0, 'reserved': 0, 'needs_attention': 0}
    }
    
    tables_by_section['bar'] = {
        'name': 'Bar',
        'tables': [],
        'available_count': 0,
        'occupied_count': 0,
        'attention_count': 0,
        'stats': {'available': 0, 'occupied': 0, 'reserved': 0, 'needs_attention': 0}
    }
    
    # Process each table and assign to appropriate section
    for table_info in tables_status_summary:
        table = table_info['table']
        status = table_info['status']
        
        # Determine section based on table number or properties
        section_key = 'ac'  # default
        if hasattr(table, 'section'):
            section_key = table.section.lower()
        elif table.table_number.startswith('B'):
            section_key = 'bar'
        else:
            # Safe numeric conversion for table numbers
            try:
                if int(table.table_number) > 20:  # Assume higher numbers are non-AC
                    section_key = 'non_ac'
            except (ValueError, TypeError):
                # If table number is not numeric, keep default 'ac' section
                section_key = 'ac'
        
        # Ensure section exists
        if section_key not in tables_by_section:
            section_key = 'ac'
        
        # Determine status class and icons
        status_class = 'blank'
        status_icons = []
        
        if status == 'available':
            status_class = 'blank'
        elif status == 'occupied':
            status_class = 'running'
            status_icons = ['running']
        elif status == 'needs-attention':
            status_class = 'needs-attention'
            status_icons = ['payment-pending']
        
        # Get order information for active tables
        order_info = None
        if status == 'occupied':
            latest_order = Order.objects.filter(
                table=table,
                status__in=['pending', 'accepted', 'preparing']
            ).order_by('-created_at').first()
            
            if latest_order:
                order_info = {
                    'order': latest_order,
                    'customer_name': latest_order.customer_name or 'Walk-in',
                    'duration_minutes': int((timezone.now() - latest_order.created_at).total_seconds() / 60),
                    'item_count': latest_order.items.count(),
                    'total_amount': latest_order.total_amount,
                    'status_display': latest_order.get_status_display()
                }
        
        # Add table to section
        table_data = {
            'table': table,
            'status': status,
            'status_class': status_class,
            'status_icons': status_icons,
            'order_info': order_info,
            'needs_attention': status == 'needs-attention',
            'capacity': getattr(table, 'capacity', 4),
            'location': getattr(table, 'location', None)
        }
        
        tables_by_section[section_key]['tables'].append(table_data)
        
        # Update section counts
        if status == 'available':
            tables_by_section[section_key]['available_count'] += 1
            tables_by_section[section_key]['stats']['available'] += 1
        elif status == 'occupied':
            tables_by_section[section_key]['occupied_count'] += 1
            tables_by_section[section_key]['stats']['occupied'] += 1
        elif status == 'needs-attention':
            tables_by_section[section_key]['attention_count'] += 1
            tables_by_section[section_key]['stats']['needs_attention'] += 1
    
    # Calculate totals for POS view
    total_available_tables = sum(section['available_count'] for section in tables_by_section.values())
    total_occupied_tables = sum(section['occupied_count'] for section in tables_by_section.values())
    total_running_kot = Order.objects.filter(
        table__restaurant=user_restaurant,
        status__in=['accepted', 'preparing'],
        is_table_order=True
    ).distinct().count()
    
    # Convert querysets to JSON for JavaScript charts
    daily_sales_json = json.dumps(list(daily_sales), cls=DjangoJSONEncoder)
    monthly_sales_json = json.dumps(list(monthly_sales), cls=DjangoJSONEncoder)
    status_stats_json = json.dumps(list(status_stats), cls=DjangoJSONEncoder)
    delivery_stats_json = json.dumps(list(delivery_stats), cls=DjangoJSONEncoder)
    peak_hours_json = json.dumps(list(peak_hours), cls=DjangoJSONEncoder)
    
    # Context data for template
    context = {
        # Restaurant info
        'user_restaurant': user_restaurant,
        
        # Date filter info
        'date_filter': date_filter,
        'start_date': start_date,
        
        # Sales Analytics
        'total_orders_all_time': total_orders_all_time,
        'orders_in_period': orders_in_period,
        'orders_today': orders_today,
        'status_stats': status_stats,
        'daily_sales_json': daily_sales_json,
        'monthly_sales_json': monthly_sales_json,
        
        # Revenue Tracking
        'total_revenue_all_time': total_revenue_all_time,
        'revenue_in_period': revenue_in_period,
        'revenue_today': revenue_today,
        'revenue_yesterday': revenue_yesterday,
        'revenue_growth': round(revenue_growth, 2),
        'avg_order_value': round(avg_order_value, 2),
        'delivery_stats': delivery_stats,
        
        # Menu Performance
        'best_selling_items': list(best_selling_items),
        'worst_selling_items': list(worst_selling_items),
        'category_performance': list(category_performance),
        'unavailable_items': list(unavailable_items),
        
        # Order Statistics
        'avg_completion_time': round(avg_completion_time, 2),
        'recent_reviews': recent_reviews,
        'peak_hours': peak_hours,
        'recent_orders': recent_orders,
        
        # Promo Code Statistics
        'active_promo_codes': active_promo_codes,
        'total_promo_codes': total_promo_codes,
        'total_redemptions': total_redemptions,
        'expiring_soon_promo_codes': expiring_soon_promo_codes,
        'total_discount_given': round(total_discount_given, 2),
        
        # Seasonal Promotion Statistics
        'active_seasonal_promotions': active_seasonal_promotions,
        'total_seasonal_promotions': total_seasonal_promotions,
        'upcoming_seasonal_promotions': upcoming_seasonal_promotions,
        'total_seasonal_codes': total_seasonal_codes,
        
        # Table Management Statistics (QR Code System)
        'total_tables': total_tables,
        'active_tables': active_tables,
        'inactive_tables': inactive_tables,
        'tables_with_qr': tables_with_qr,
        'recent_tables': recent_tables,
        'latest_tables': latest_tables,
        'table_utilization': round(table_utilization, 2),
        
        # QR Code Ordering Statistics
        'qr_orders_all_time': qr_orders_all_time,
        'qr_orders_today': qr_orders_today,
        'qr_orders_in_period': qr_orders_in_period,
        'qr_revenue_all_time': round(qr_revenue_all_time, 2),
        'qr_revenue_today': round(qr_revenue_today, 2),
        'qr_revenue_in_period': round(qr_revenue_in_period, 2),
        'staff_orders_today': staff_orders_today,
        'active_table_orders': active_table_orders,
        'orders_needing_payment': orders_needing_payment,
        'recent_table_orders': recent_table_orders,
        'available_tables': available_tables,
        'occupied_tables': occupied_tables,
        'needs_attention_tables': needs_attention_tables,
        
        # POS Table View Data (NEW)
        'tables_by_section': tables_by_section,
        'total_available_tables': total_available_tables,
        'total_occupied_tables': total_occupied_tables,
        'total_running_kot': total_running_kot,
        'current_time': timezone.now().strftime('%H:%M:%S'),
        
        # NEW: Live Order Tracking Variables
        'active_orders_count': active_table_orders.count(),
        'pending_orders_count': Order.objects.filter(
            status='pending',
            items__menu_item__restaurant=user_restaurant
        ).distinct().count(),
        'accepted_orders_count': Order.objects.filter(
            status='accepted',
            items__menu_item__restaurant=user_restaurant
        ).distinct().count(),
        'preparing_orders_count': Order.objects.filter(
            status='preparing',
            items__menu_item__restaurant=user_restaurant
        ).distinct().count(),
        'ready_orders_count': Order.objects.filter(
            status='ready',
            items__menu_item__restaurant=user_restaurant
        ).distinct().count(),
        'delivered_orders_count': Order.objects.filter(
            status='delivered',
            items__menu_item__restaurant=user_restaurant
        ).distinct().count(),
        'recent_active_orders': active_table_orders[:5],
        
        # JSON data for charts
        'status_stats_json': status_stats_json,
        'delivery_stats_json': delivery_stats_json,
        'peak_hours_json': peak_hours_json,
    }
    
    return render(request, 'restaurant/dashboard.html', context)


@login_required
def operations_hub(request):
    """
    Unified operations hub for restaurant owners - combines all key restaurant tasks
    in one streamlined interface with tabbed navigation.
    
    Features:
    - Table operations overview
    - Active orders management
    - Menu quick access
    - QR code system
    - Quick analytics
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered operations hub template with aggregated data
    """
    # Get selected restaurant
    user_restaurant = get_selected_restaurant(request)
    
    if not user_restaurant:
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'You are not associated with any restaurant.')
            return redirect('customer:home')
    
    # Get current date/time
    today = timezone.now().date()
    now = timezone.now()
    
    # === TABLE STATISTICS ===
    # Get all tables for this restaurant
    all_tables = RestaurantTable.objects.filter(restaurant=user_restaurant)
    total_tables = all_tables.count()
    total_capacity = all_tables.aggregate(Sum('capacity'))['capacity__sum'] or 0
    
    # Get occupied tables (tables with active orders)
    occupied_tables_count = all_tables.filter(
        orders__isnull=False,
        orders__status__in=['pending', 'preparing', 'ready']
    ).distinct().count()
    
    available_tables = total_tables - occupied_tables_count
    
    # === ORDER STATISTICS ===
    # Get today's orders for this restaurant
    today_orders = Order.objects.filter(
        created_at__date=today,
        items__menu_item__restaurant=user_restaurant
    ).distinct()
    
    # Today's sales
    today_sales = today_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    today_orders_count = today_orders.count()
    
    # Average order value
    avg_order_value = today_sales / today_orders_count if today_orders_count > 0 else 0
    
    # Customer count (unique customers today)
    today_customers = today_orders.filter(user__isnull=False).values('user').distinct().count()
    
    # === MENU STATISTICS ===
    # Get menu items for this restaurant
    menu_items = MenuItem.objects.filter(restaurant=user_restaurant)
    total_menu_items = menu_items.count()
    available_items = menu_items.filter(is_available=True).count()
    categories_count = Category.objects.filter(is_active=True).count()
    
    # Popular items (placeholder - can be enhanced with actual order data)
    popular_items = menu_items.filter(is_available=True)[:5].count()
    
    # Prepare context data
    context = {
        'restaurant': user_restaurant,
        # Table statistics
        'total_tables': total_tables,
        'occupied_tables': occupied_tables_count,
        'available_tables': available_tables,
        'total_capacity': total_capacity,
        # Order statistics
        'today_orders': today_orders_count,
        'today_sales': today_sales,
        'avg_order_value': avg_order_value,
        'today_customers': today_customers,
        # Menu statistics
        'total_menu_items': total_menu_items,
        'available_items': available_items,
        'categories_count': categories_count,
        'popular_items': popular_items,
    }
    
    return render(request, 'restaurant/operations_hub.html', context)


@restaurant_owner_required
def order_detail(request, order_id):
    """
    Display detailed view of a specific order for restaurant owners.
    
    Only allows viewing orders that contain menu items from this specific restaurant.
    
    Args:
        request: Django HTTP request object
        order_id: UUID of the order
    
    Returns:
        HttpResponse: Rendered order detail page template or redirect if unauthorized
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    # Get order first
    order = get_object_or_404(Order, order_id=order_id)
    
    # Security check: ensure order has items from this restaurant
    if not order.items.filter(menu_item__restaurant=restaurant).exists():
        messages.error(request, 'You can only view orders for your restaurant.')
        return redirect('restaurant:dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Handle customer info update
        if action == 'update_customer':
            customer_name = request.POST.get('customer_name', '').strip()
            customer_phone = request.POST.get('customer_phone', '').strip()
            customer_address = request.POST.get('customer_address', '').strip()
            notes = request.POST.get('notes', '').strip()
            
            # Validation for required fields
            if not customer_name:
                messages.error(request, 'Customer name is required.')
                return redirect('restaurant:order_detail', order_id=order.order_id)
            
            # Basic phone number validation (10-15 digits, optional +)
            if customer_phone and not re.match(r'^\+?[0-9]{10,15}$', customer_phone.replace('-', '').replace(' ', '')):
                messages.error(request, 'Please enter a valid phone number (10-15 digits).')
                return redirect('restaurant:order_detail', order_id=order.order_id)
            
            # Update order with validated customer information
            order.customer_name = customer_name
            if customer_phone:
                order.customer_phone = customer_phone
            if customer_address:
                order.customer_address = customer_address
            order.notes = notes if notes else ''
            
            order.save()
            messages.success(
                request, 
                f'Customer information updated for Order #{str(order.order_id)[:8]}.'
            )
            return redirect('restaurant:order_detail', order_id=order.order_id)
        
        # Handle status update (existing functionality)
        else:
            new_status = request.POST.get('status')
            if new_status in dict(Order.STATUS_CHOICES):
                order.status = new_status
                order.save()
                messages.success(
                    request, 
                    f'Order #{str(order.order_id)[:8]} status updated to {order.get_status_display()}.'
                )
                return redirect('restaurant:order_detail', order_id=order.order_id)
    
    context = {
        'restaurant': restaurant,
        'order': order
    }
    return render(request, 'restaurant/order_detail.html', context)


@restaurant_owner_required
def order_list(request):
    """
    Display list of orders for the restaurant owner's restaurant only.
    
    Shows only orders that contain menu items from this specific restaurant.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered order list page template
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Get only orders that have menu items from this restaurant
    orders = Order.objects.filter(items__menu_item__restaurant=restaurant).distinct()
    
    # Apply status filter
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Apply search filter
    if search_query:
        orders = orders.filter(
            Q(customer_name__icontains=search_query) |
            Q(customer_phone__icontains=search_query) |
            Q(order_id__icontains=search_query)
        )
    
    orders = orders.order_by('-created_at')
    
    context = {
        'restaurant': restaurant,
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'restaurant/order_list.html', context)


@restaurant_owner_required
def update_order_status(request, order_id):
    """
    Update order status via AJAX for restaurant owners.
    
    Only allows updating orders that contain menu items from this specific restaurant.
    
    Args:
        request: Django HTTP request object
        order_id: UUID of the order to update
    
    Returns:
        JsonResponse: Success/error response with updated status
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        return JsonResponse({
            'success': False,
            'error': 'No restaurant found for your account.'
        })
    
    if request.method == 'POST':
        # Get order first
        order = get_object_or_404(Order, order_id=order_id)
        
        # Security check: ensure order has items from this restaurant
        if not order.items.filter(menu_item__restaurant=restaurant).exists():
            return JsonResponse({
                'success': False,
                'error': 'You can only update orders for your restaurant.'
            })
        
        new_status = request.POST.get('status')
        
        # Validate status
        valid_statuses = dict(Order.STATUS_CHOICES).keys()
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': 'Invalid status'
            })
        
        # Update order status
        old_status = order.status
        order.status = new_status
        order.save()
        
        # Send email and SMS notifications
        try:
            notification_results = send_order_notification(order, old_status, new_status)
            logger.info(f"Notification results for order {order.order_id}: {notification_results}")
        except Exception as e:
            logger.error(f"Failed to send notifications for order {order.order_id}: {str(e)}")
            # Continue with the response even if notifications fail
        
        # Log the change
        messages.success(
            request, 
            f'Order #{str(order.order_id)[:8]} status updated to {order.get_status_display()}.'
        )
        
        return JsonResponse({
            'success': True,
            'new_status': new_status,
            'status_display': order.get_status_display(),
            'message': f'Order status updated to {order.get_status_display()}'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })


# Manager Approval System Views
@staff_member_required
def manager_dashboard(request):
    """
    Display manager dashboard with pending restaurant applications and login activity.
    Handles admin tools operations including reporting, bulk operations, and user management.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered manager dashboard page template or file download
    """
    # Handle POST requests for admin tools
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'generate_report':
            # Handle report generation
            report_type = request.POST.get('report_type')
            date_range = request.POST.get('date_range', 'month')
            export_format = request.POST.get('format', 'csv')
            
            if not report_type:
                messages.error(request, 'Please select a report type.')
                return redirect('restaurant:manager_dashboard')
            
            # Generate report data
            report_data = generate_report_data(report_type, date_range)
            
            # Export based on format
            if export_format == 'csv':
                return export_csv_report(report_data, report_type)
            elif export_format == 'excel':
                # For now, return CSV as Excel fallback
                messages.info(request, 'Excel export coming soon. Downloading CSV instead.')
                return export_csv_report(report_data, report_type)
            elif export_format == 'pdf':
                # For now, return CSV as PDF fallback
                messages.info(request, 'PDF export coming soon. Downloading CSV instead.')
                return export_csv_report(report_data, report_type)
            
            messages.error(request, 'Invalid export format.')
            return redirect('restaurant:manager_dashboard')
        
        elif action == 'send_email_campaign':
            # Handle bulk email campaign
            target_audience = request.POST.get('target_audience')
            email_template = request.POST.get('email_template')
            custom_message = request.POST.get('custom_message', '')
            
            if not target_audience or not email_template:
                messages.error(request, 'Please select target audience and email template.')
                return redirect('restaurant:manager_dashboard')
            
            # Send email campaign
            try:
                results = send_bulk_email_campaign(target_audience, email_template, custom_message)
                messages.success(
                    request, 
                    f'Email campaign sent successfully! {results["sent_count"]} emails sent, '
                    f'{results["failed_count"]} failed out of {results["total_recipients"]} recipients.'
                )
            except Exception as e:
                messages.error(request, f'Failed to send email campaign: {str(e)}')
            
            return redirect('restaurant:manager_dashboard')
        
        elif action == 'bulk_restaurant_update':
            # Handle bulk restaurant status updates
            restaurant_action = request.POST.get('restaurant_action')
            
            if not restaurant_action:
                messages.error(request, 'Please select an action.')
                return redirect('restaurant:manager_dashboard')
            
            try:
                if restaurant_action == 'activate':
                    updated = Restaurant.objects.filter(is_active=False).update(is_active=True)
                    messages.success(request, f'Activated {updated} restaurants.')
                elif restaurant_action == 'deactivate':
                    updated = Restaurant.objects.filter(is_active=True).update(is_active=False)
                    messages.success(request, f'Deactivated {updated} restaurants.')
                elif restaurant_action == 'suspend':
                    # For suspension, we could add a suspended status field
                    messages.info(request, 'Suspension feature coming soon.')
                else:
                    messages.error(request, 'Invalid action selected.')
            except Exception as e:
                messages.error(request, f'Failed to update restaurants: {str(e)}')
            
            return redirect('restaurant:manager_dashboard')
        
        elif action == 'bulk_order_update':
            # Handle bulk order status updates
            order_action = request.POST.get('order_action')
            
            if not order_action:
                messages.error(request, 'Please select an action.')
                return redirect('restaurant:manager_dashboard')
            
            try:
                if order_action == 'cancel_old':
                    cutoff_date = timezone.now() - timedelta(days=7)
                    updated = Order.objects.filter(
                        created_at__lt=cutoff_date,
                        status__in=['pending', 'accepted']
                    ).update(status='cancelled')
                    messages.success(request, f'Cancelled {updated} old orders.')
                elif order_action == 'complete_pending':
                    updated = Order.objects.filter(
                        status='pending'
                    ).update(status='delivered')
                    messages.success(request, f'Marked {updated} pending orders as delivered.')
                elif order_action == 'reset_failed':
                    updated = Order.objects.filter(
                        status='cancelled'
                    ).update(status='pending')
                    messages.success(request, f'Reset {updated} failed orders to pending.')
                else:
                    messages.error(request, 'Invalid action selected.')
            except Exception as e:
                messages.error(request, f'Failed to update orders: {str(e)}')
            
            return redirect('restaurant:manager_dashboard')
        
        else:
            messages.error(request, 'Invalid action specified.')
            return redirect('restaurant:manager_dashboard')
    
    # GET request - display dashboard
    
    # Import User model for user management statistics
    from django.contrib.auth.models import User
    from orders.models import Order
    
    # Get pending restaurant applications
    pending_restaurants = PendingRestaurant.objects.filter(status='pending').order_by('-created_at')
    
    # Get recent approved/rejected applications
    recent_applications = PendingRestaurant.objects.filter(
        status__in=['approved', 'rejected']
    ).order_by('-processed_at')[:10]
    
    # Get recent manager login activity
    recent_logins = ManagerLoginLog.objects.select_related('user').order_by('-login_time')[:10]
    
    # Get current active sessions
    active_sessions = ManagerLoginLog.objects.filter(is_active_session=True).select_related('user').order_by('-login_time')
    
    # Admin statistics (only for superusers)
    total_users = 0
    total_orders = 0
    total_revenue = 0
    
    if request.user.is_superuser:
        total_users = User.objects.count()
        total_orders = Order.objects.count()
        total_revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
        
        # User Management Statistics
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        
        # Active users today (users who logged in today)
        active_users_today = User.objects.filter(last_login__date=today).count()
        
        # New users this month
        new_users_month = User.objects.filter(date_joined__date__gte=this_month_start).count()
        
        # User role breakdown
        superusers_count = User.objects.filter(is_superuser=True).count()
        staff_count = User.objects.filter(is_staff=True, is_superuser=False).count()
        regular_users_count = total_users - superusers_count - staff_count
        
        # Recent user registrations (last 10)
        recent_user_registrations = User.objects.order_by('-date_joined')[:10]
    else:
        # Non-superusers get limited access to user management data
        active_users_today = 0
        new_users_month = 0
        superusers_count = 0
        staff_count = 0
        regular_users_count = 0
        recent_user_registrations = User.objects.none()
    
    # Statistics
    total_pending = pending_restaurants.count()
    total_approved = PendingRestaurant.objects.filter(status='approved').count()
    total_rejected = PendingRestaurant.objects.filter(status='rejected').count()
    total_active_restaurants = Restaurant.objects.filter(is_active=True).count()
    total_active_managers = active_sessions.count()
    
    context = {
        'pending_restaurants': pending_restaurants,
        'recent_applications': recent_applications,
        'recent_logins': recent_logins,
        'active_sessions': active_sessions,
        'total_pending': total_pending,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'total_active_restaurants': total_active_restaurants,
        'total_active_managers': total_active_managers,
        'total_users': total_users,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        # User Management data
        'active_users_today': active_users_today,
        'new_users_month': new_users_month,
        'superusers_count': superusers_count,
        'staff_count': staff_count,
        'regular_users_count': regular_users_count,
        'recent_user_registrations': recent_user_registrations,
    }
    return render(request, 'restaurant/manager_dashboard.html', context)


@staff_member_required
def search_users(request):
    """
    Handle user search requests with AJAX.
    Searches users by username, email, or name with optional role filtering.
    
    Args:
        request: Django HTTP request object with GET parameters:
                - search: Search query string
                - role: Role filter ('all', 'staff', 'superuser', 'customer')
                - status: Status filter ('all', 'active', 'inactive')
    
    Returns:
        JsonResponse: Search results in JSON format with user data
    """
    search_query = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', 'all')
    status_filter = request.GET.get('status', 'all')
    
    # Start with all users
    users = User.objects.all()
    
    # Apply search filter
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Apply role filter
    if role_filter == 'staff':
        users = users.filter(is_staff=True, is_superuser=False)
    elif role_filter == 'superuser':
        users = users.filter(is_superuser=True)
    elif role_filter == 'customer':
        users = users.filter(is_staff=False, is_superuser=False)
    
    # Apply status filter
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Limit results and prepare data
    users = users[:20]  # Limit to 20 results for performance
    
    results = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email or 'No email',
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'full_name': f"{user.first_name} {user.last_name}".strip() or 'No name provided',
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'date_joined': user.date_joined.strftime('%Y-%m-%d'),
            'last_login': user.last_login.strftime('%Y-%m-%d') if user.last_login else 'Never',
            'role': 'Super Admin' if user.is_superuser else 'Staff' if user.is_staff else 'Customer',
            'status': 'Active' if user.is_active else 'Inactive'
        }
        results.append(user_data)
    
    return JsonResponse({
        'success': True,
        'count': len(results),
        'results': results
    })


@staff_member_required
def pending_restaurant_detail(request, pending_id):
    """
    Display detailed view of a pending restaurant application.
    
    Args:
        request: Django HTTP request object
        pending_id: ID of the pending restaurant application
    
    Returns:
        HttpResponse: Rendered pending restaurant detail page template
    """
    pending_restaurant = get_object_or_404(PendingRestaurant, id=pending_id, status='pending')
    
    context = {'pending_restaurant': pending_restaurant}
    return render(request, 'restaurant/pending_restaurant_detail.html', context)


@staff_member_required
def approve_restaurant(request, pending_id):
    """
    Approve a pending restaurant application.
    
    Supports both traditional POST requests and AJAX requests.
    
    Args:
        request: Django HTTP request object
        pending_id: ID of the pending restaurant application
    
    Returns:
        HttpResponse: JSON response for AJAX or redirect for traditional requests
    """
    pending_restaurant = get_object_or_404(PendingRestaurant, id=pending_id, status='pending')
    
    if request.method == 'POST':
        try:
            # Approve the application
            restaurant = pending_restaurant.approve_application(request.user)
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': f'Restaurant "{restaurant.name}" has been approved successfully!'
                })
            else:
                # Traditional request - show success message and redirect
                messages.success(
                    request,
                    f'Restaurant "{restaurant.name}" has been approved successfully! '
                    f'The owner ({restaurant.owner.username}) has been notified.'
                )
                return redirect('restaurant:manager_dashboard')
                
        except Exception as e:
            logger.error(f"Error approving restaurant {pending_id}: {str(e)}")
            
            # Handle AJAX error response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to approve restaurant. Please try again.'
                }, status=500)
            else:
                messages.error(request, 'Failed to approve restaurant. Please try again.')
                return redirect('restaurant:manager_dashboard')
    
    # GET request - show confirmation page (fallback for non-JS users)
    context = {'pending_restaurant': pending_restaurant}
    return render(request, 'restaurant/approve_restaurant.html', context)


@staff_member_required
def reject_restaurant(request, pending_id):
    """
    Reject a pending restaurant application.
    
    Supports both traditional POST requests and AJAX requests.
    
    Args:
        request: Django HTTP request object
        pending_id: ID of the pending restaurant application
    
    Returns:
        HttpResponse: JSON response for AJAX or redirect for traditional requests
    """
    pending_restaurant = get_object_or_404(PendingRestaurant, id=pending_id, status='pending')
    
    if request.method == 'POST':
        # Handle both traditional form data and JSON data
        if request.content_type == 'application/json':
            import json
            data = json.loads(request.body)
            rejection_reason = data.get('rejection_reason', '').strip()
        else:
            rejection_reason = request.POST.get('rejection_reason', '').strip()
        
        if not rejection_reason:
            # Handle AJAX error response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'Please provide a reason for rejection.'
                })
            else:
                messages.error(request, 'Please provide a reason for rejection.')
                return redirect('restaurant:reject_restaurant', pending_id=pending_id)
        
        try:
            # Reject the application
            pending_restaurant.reject_application(request.user, rejection_reason)
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': f'Restaurant application from {pending_restaurant.user.username} has been rejected.'
                })
            else:
                # Traditional request - show success message and redirect
                messages.success(
                    request,
                    f'Restaurant application from {pending_restaurant.user.username} has been rejected. '
                    f'The applicant will be notified with the provided reason.'
                )
                return redirect('restaurant:manager_dashboard')
                
        except Exception as e:
            logger.error(f"Error rejecting restaurant {pending_id}: {str(e)}")
            
            # Handle AJAX error response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to reject restaurant. Please try again.'
                }, status=500)
            else:
                messages.error(request, 'Failed to reject restaurant. Please try again.')
                return redirect('restaurant:manager_dashboard')
    
    # GET request - show rejection form (fallback for non-JS users)
    context = {'pending_restaurant': pending_restaurant}
    return render(request, 'restaurant/reject_restaurant.html', context)


@staff_member_required
def manager_restaurants_list(request):
    """
    Display list of all approved restaurants for manager oversight.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered restaurants list page template
    """
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    restaurants = Restaurant.objects.all()
    
    # Apply status filter
    if status_filter:
        restaurants = restaurants.filter(approval_status=status_filter)
    
    # Apply search filter
    if search_query:
        restaurants = restaurants.filter(
            Q(name__icontains=search_query) |
            Q(owner__username__icontains=search_query) |
            Q(cuisine_type__icontains=search_query)
        )
    
    restaurants = restaurants.order_by('-created_at')
    
    context = {
        'restaurants': restaurants,
        'approval_choices': Restaurant.APPROVAL_STATUS_CHOICES,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'restaurant/manager_restaurants_list.html', context)


@staff_member_required
def toggle_restaurant_status(request, restaurant_id):
    """
    Toggle restaurant active status (activate/deactivate).
    
    Args:
        request: Django HTTP request object
        restaurant_id: ID of the restaurant to toggle
    
    Returns:
        HttpResponse: Redirect back to restaurants list with message
    """
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    if request.method == 'POST':
        # Toggle the active status
        restaurant.is_active = not restaurant.is_active
        restaurant.save()
        
        if restaurant.is_active:
            messages.success(request, f'Restaurant "{restaurant.name}" has been activated.')
        else:
            messages.warning(request, f'Restaurant "{restaurant.name}" has been deactivated.')
            
    return redirect('restaurant:manager_restaurants_list')


# Menu Management Views
@restaurant_owner_required
def menu_management(request):
    """
    Display menu management page for restaurant owners.
    
    Shows all menu items with options to add, edit, delete, and toggle availability.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered menu management page template
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    # Get filter parameters
    category_filter = request.GET.get('category')
    availability_filter = request.GET.get('availability')
    search_query = request.GET.get('search', '').strip()
    
    # Get menu items for this restaurant
    menu_items = MenuItem.objects.filter(restaurant=restaurant).select_related('category')
    
    # Apply filters
    if category_filter:
        menu_items = menu_items.filter(category_id=category_filter)
    
    if availability_filter:
        if availability_filter == 'available':
            menu_items = menu_items.filter(is_available=True)
        elif availability_filter == 'unavailable':
            menu_items = menu_items.filter(is_available=False)
    
    if search_query:
        menu_items = menu_items.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Order by category and name
    menu_items = menu_items.order_by('category__display_order', 'category__name', 'name')
    
    # Get categories for filter dropdown
    categories = Category.objects.filter(is_active=True).order_by('display_order', 'name')
    
    # Pagination
    paginator = Paginator(menu_items, 20)  # Show 20 items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'restaurant': restaurant,
        'menu_items': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_filter,
        'availability_filter': availability_filter,
        'search_query': search_query,
    }
    
    return render(request, 'restaurant/menu_management.html', context)


@restaurant_owner_required
def add_menu_item(request):
    """
    Add a new menu item for the restaurant.
    
    Handles form submission for creating new menu items with image upload.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered add menu item form or redirect to menu management
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            menu_item = form.save(commit=False)
            menu_item.restaurant = restaurant
            menu_item.save()
            
            messages.success(request, f'Menu item "{menu_item.name}" has been added successfully!')
            return redirect('restaurant:menu_management')
    else:
        form = MenuItemForm()
    
    context = {
        'restaurant': restaurant,
        'form': form,
        'title': 'Add New Menu Item',
        'action': 'Add',
    }
    
    return render(request, 'restaurant/menu_item_form.html', context)


@restaurant_owner_required
def edit_menu_item(request, menu_item_id):
    """
    Edit an existing menu item.
    
    Handles form submission for updating menu items with image replacement.
    
    Args:
        request: Django HTTP request object
        menu_item_id: ID of the menu item to edit
    
    Returns:
        HttpResponse: Rendered edit menu item form or redirect to menu management
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    # Get menu item and verify ownership
    menu_item = get_object_or_404(MenuItem, id=menu_item_id, restaurant=restaurant)
    
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=menu_item)
        if form.is_valid():
            # Handle image replacement
            if 'image' in request.FILES and menu_item.image:
                # Delete old image file with error handling
                try:
                    old_image_path = menu_item.image.path
                    import os
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                except (AttributeError, OSError) as e:
                    # Log error but don't fail the operation
                    print(f"Warning: Could not delete old image file: {e}")
            
            form.save()
            messages.success(request, f'Menu item "{menu_item.name}" has been updated successfully!')
            return redirect('restaurant:menu_management')
    else:
        form = MenuItemForm(instance=menu_item)
    
    context = {
        'restaurant': restaurant,
        'menu_item': menu_item,
        'form': form,
        'title': 'Edit Menu Item',
        'action': 'Update',
    }
    
    return render(request, 'restaurant/menu_item_form.html', context)


@restaurant_owner_required
def delete_menu_item(request, menu_item_id):
    """
    Delete a menu item.
    
    Handles menu item deletion with confirmation.
    
    Args:
        request: Django HTTP request object
        menu_item_id: ID of the menu item to delete
    
    Returns:
        HttpResponse: Redirect to menu management with confirmation message
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    # Get menu item and verify ownership
    menu_item = get_object_or_404(MenuItem, id=menu_item_id, restaurant=restaurant)
    
    if request.method == 'POST':
        item_name = menu_item.name
        
        # Delete image file with error handling
        if menu_item.image:
            try:
                import os
                if os.path.exists(menu_item.image.path):
                    os.remove(menu_item.image.path)
            except (AttributeError, OSError) as e:
                # Log error but don't fail the operation
                print(f"Warning: Could not delete image file: {e}")
        
        menu_item.delete()
        messages.success(request, f'Menu item "{item_name}" has been deleted successfully!')
        
    return redirect('restaurant:menu_management')


@restaurant_owner_required
def toggle_menu_item_availability(request, menu_item_id):
    """
    Toggle the availability status of a menu item.
    
    Quick toggle for stock management without full page reload.
    
    Args:
        request: Django HTTP request object
        menu_item_id: ID of the menu item to toggle
    
    Returns:
        JsonResponse: JSON response with updated status
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        return JsonResponse({'success': False, 'message': 'No restaurant found.'})
    
    # Get menu item and verify ownership
    menu_item = get_object_or_404(MenuItem, id=menu_item_id, restaurant=restaurant)
    
    if request.method == 'POST':
        menu_item.is_available = not menu_item.is_available
        menu_item.save()
        
        status_text = 'available' if menu_item.is_available else 'unavailable'
        status_color = 'green' if menu_item.is_available else 'red'
        
        return JsonResponse({
            'success': True,
            'is_available': menu_item.is_available,
            'status_text': status_text,
            'status_color': status_color,
            'message': f'"{menu_item.name}" is now {status_text}.'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@restaurant_owner_required
def bulk_update_availability(request):
    """
    Bulk update availability for multiple menu items.
    
    Handles bulk availability changes from the menu management page.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Redirect to menu management with confirmation message
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    if request.method == 'POST':
        # Get all menu items for this restaurant
        menu_items = MenuItem.objects.filter(restaurant=restaurant)
        
        # Create form with current menu items
        form = MenuItemBulkUpdateForm(menu_items, request.POST)
        
        if form.is_valid():
            updated_count = 0
            
            # Update each menu item based on form data
            for item in menu_items:
                field_name = f'item_{item.id}'
                new_availability = form.cleaned_data.get(field_name, False)
                
                if item.is_available != new_availability:
                    item.is_available = new_availability
                    item.save()
                    updated_count += 1
            
            if updated_count > 0:
                messages.success(request, f'Updated availability for {updated_count} menu items.')
            else:
                messages.info(request, 'No changes made to menu item availability.')
        
    return redirect('restaurant:menu_management')


# Category Management Views
@restaurant_owner_required
def category_management(request):
    """
    Display category management page for restaurant owners.
    
    Shows only categories that have menu items for this specific restaurant,
    making the management interface more relevant and focused.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered category management page template
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    # Get only categories that have menu items from this restaurant
    categories = Category.objects.filter(
        items__restaurant=restaurant
    ).distinct().order_by('display_order', 'name')
    
    # Annotate categories with menu item count for this restaurant
    categories = categories.annotate(
        menu_item_count=Count('items', filter=Q(items__restaurant=restaurant))
    )
    
    context = {
        'restaurant': restaurant,
        'categories': categories,
    }
    
    return render(request, 'restaurant/category_management.html', context)


@restaurant_owner_required
def add_category(request):
    """
    Add a new food category.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered add category form or redirect to category management
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" has been added successfully!')
            return redirect('restaurant:category_management')
    else:
        form = CategoryForm()
    
    context = {
        'restaurant': restaurant,
        'form': form,
        'title': 'Add New Category',
        'action': 'Add',
    }
    
    return render(request, 'restaurant/category_form.html', context)


@restaurant_owner_required
def edit_category(request, category_id):
    """
    Edit an existing food category.
    
    Args:
        request: Django HTTP request object
        category_id: ID of the category to edit
    
    Returns:
        HttpResponse: Rendered edit category form or redirect to category management
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    # Get category
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" has been updated successfully!')
            return redirect('restaurant:category_management')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'restaurant': restaurant,
        'category': category,
        'form': form,
        'title': 'Edit Category',
        'action': 'Update',
    }
    
    return render(request, 'restaurant/category_form.html', context)


@restaurant_owner_required
def delete_category(request, category_id):
    """
    Delete a food category.
    
    Handles category deletion with confirmation and validation.
    Only allows deletion if category has no menu items.
    
    Args:
        request: Django HTTP request object
        category_id: ID of the category to delete
    
    Returns:
        HttpResponse: Redirect to category management with confirmation message
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    # Get category
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        # Check if category has menu items
        if category.items.exists():
            messages.error(request, f'Cannot delete category "{category.name}" because it contains menu items.')
        else:
            category_name = category.name
            category.delete()
            messages.success(request, f'Category "{category_name}" has been deleted successfully!')
        
    return redirect('restaurant:category_management')


# MARKETING CAMPAIGN VIEWS

@restaurant_owner_required
def campaign_list(request):
    """
    Display list of all marketing campaigns for the restaurant owner.
    
    Shows campaign statistics, status, and allows management of campaigns.
    Only displays campaigns belonging to the user's restaurant.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered campaign list page template
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('customer:home')
    
    # Get all campaigns for this restaurant
    campaigns = MarketingCampaign.objects.filter(
        restaurant=restaurant
    ).order_by('-created_at')
    
    # Calculate statistics for each campaign
    campaign_stats = []
    for campaign in campaigns:
        stats = campaign.get_campaign_stats()
        campaign_stats.append({
            'campaign': campaign,
            'stats': stats
        })
    
    # Calculate total reach across all campaigns
    total_reach = sum(stat['stats']['target_count'] for stat in campaign_stats)
    
    context = {
        'restaurant': restaurant,
        'campaign_stats': campaign_stats,
        'total_reach': total_reach,
        'total_campaigns': campaigns.count(),
        'active_campaigns': campaigns.filter(status__in=['draft', 'scheduled', 'sending']).count(),
        'sent_campaigns': campaigns.filter(status='sent').count(),
    }
    
    return render(request, 'restaurant/campaign_list.html', context)


@restaurant_owner_required
def campaign_create(request):
    """
    Create a new marketing campaign.
    
    Handles form submission for creating promotional email campaigns
    with customer targeting and scheduling options.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered campaign creation form or redirect to campaign list
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('customer:home')
    
    if request.method == 'POST':
        form = MarketingCampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.restaurant = restaurant
            campaign.created_by = request.user
            campaign.save()
            
            messages.success(request, f'Campaign "{campaign.name}" has been created successfully!')
            return redirect('restaurant:campaign_detail', campaign_id=campaign.id)
    else:
        form = MarketingCampaignForm()
    
    context = {
        'restaurant': restaurant,
        'form': form,
        'title': 'Create Marketing Campaign',
        'action': 'Create',
    }
    
    return render(request, 'restaurant/campaign_form.html', context)


@restaurant_owner_required
def campaign_detail(request, campaign_id):
    """
    Display detailed view of a specific marketing campaign.
    
    Shows campaign statistics, recipient list, and allows sending or preview.
    Only allows access to campaigns belonging to the user's restaurant.
    
    Args:
        request: Django HTTP request object
        campaign_id: ID of the campaign to view
    
    Returns:
        HttpResponse: Rendered campaign detail page template
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('customer:home')
    
    # Get campaign with security check
    campaign = get_object_or_404(MarketingCampaign, id=campaign_id, restaurant=restaurant)
    
    # Get campaign statistics
    stats = campaign.get_campaign_stats()
    
    # Get recipients with pagination
    recipients = campaign.recipients.all().order_by('-created_at')
    paginator = Paginator(recipients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get target customers count
    target_customers = campaign.get_target_customers()
    
    context = {
        'restaurant': restaurant,
        'campaign': campaign,
        'stats': stats,
        'recipients': page_obj,
        'target_customers_count': target_customers.count(),
        'can_send': campaign.status == 'draft',
        'can_edit': campaign.status == 'draft',
    }
    
    return render(request, 'restaurant/campaign_detail.html', context)


@restaurant_owner_required
def campaign_update(request, campaign_id):
    """
    Update an existing marketing campaign.
    
    Only allows editing draft campaigns belonging to the user's restaurant.
    
    Args:
        request: Django HTTP request object
        campaign_id: ID of the campaign to update
    
    Returns:
        HttpResponse: Rendered campaign edit form or redirect to campaign detail
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('customer:home')
    
    # Get campaign with security check
    campaign = get_object_or_404(MarketingCampaign, id=campaign_id, restaurant=restaurant)
    
    # Only allow editing draft campaigns
    if campaign.status != 'draft':
        messages.error(request, 'Only draft campaigns can be edited.')
        return redirect('restaurant:campaign_detail', campaign_id=campaign.id)
    
    if request.method == 'POST':
        form = MarketingCampaignForm(request.POST, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, f'Campaign "{campaign.name}" has been updated successfully!')
            return redirect('restaurant:campaign_detail', campaign_id=campaign.id)
    else:
        form = MarketingCampaignForm(instance=campaign)
    
    context = {
        'restaurant': restaurant,
        'campaign': campaign,
        'form': form,
        'title': 'Edit Marketing Campaign',
        'action': 'Update',
    }
    
    return render(request, 'restaurant/campaign_form.html', context)


@restaurant_owner_required
def campaign_delete(request, campaign_id):
    """
    Delete a marketing campaign.
    
    Only allows deletion of draft campaigns belonging to the user's restaurant.
    
    Args:
        request: Django HTTP request object
        campaign_id: ID of the campaign to delete
    
    Returns:
        HttpResponse: Redirect to campaign list with confirmation message
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('customer:home')
    
    # Get campaign with security check
    campaign = get_object_or_404(MarketingCampaign, id=campaign_id, restaurant=restaurant)
    
    # Only allow deletion of draft campaigns
    if campaign.status != 'draft':
        messages.error(request, 'Only draft campaigns can be deleted.')
        return redirect('restaurant:campaign_detail', campaign_id=campaign.id)
    
    if request.method == 'POST':
        campaign_name = campaign.name
        campaign.delete()
        messages.success(request, f'Campaign "{campaign_name}" has been deleted successfully!')
    
    return redirect('restaurant:campaign_list')


@restaurant_owner_required
def campaign_preview(request, campaign_id):
    """
    Preview a marketing campaign email.
    
    Renders the actual email template with sample data so restaurant owners
    can see exactly what customers will receive.
    
    Args:
        request: Django HTTP request object
        campaign_id: ID of the campaign to preview
    
    Returns:
        HttpResponse: Rendered email preview page
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('customer:home')
    
    # Get campaign with security check
    campaign = get_object_or_404(MarketingCampaign, id=campaign_id, restaurant=restaurant)
    
    # Prepare sample context for preview
    context = {
        'restaurant': campaign.restaurant,
        'campaign_name': campaign.name,
        'custom_message': campaign.message,
        'site_name': 'Food Ordering System',
        'site_url': 'https://tetech.in/',
        'site_domain': 'tetech.in',
        'current_year': timezone.now().year,
        'user': request.user,  # Sample user for personalization
        'first_name': request.user.first_name or 'John',
        'username': request.user.username,
    }
    
    # Render the email template
    try:
        from django.template.loader import render_to_string
        email_content = render_to_string(campaign.template, context)
    except Exception as e:
        messages.error(request, f'Error rendering email template: {str(e)}')
        return redirect('restaurant:campaign_detail', campaign_id=campaign.id)
    
    context = {
        'restaurant': restaurant,
        'campaign': campaign,
        'email_content': email_content,
    }
    
    return render(request, 'restaurant/campaign_preview.html', context)


@restaurant_owner_required
def campaign_send(request, campaign_id):
    """
    Send a marketing campaign to target customers.
    
    Triggers the email sending process and updates campaign status.
    Only allows sending draft campaigns belonging to the user's restaurant.
    
    Args:
        request: Django HTTP request object
        campaign_id: ID of the campaign to send
    
    Returns:
        HttpResponse: Redirect to campaign detail with results message
    """
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('customer:home')
    
    # Get campaign with security check
    campaign = get_object_or_404(MarketingCampaign, id=campaign_id, restaurant=restaurant)
    
    # Only allow sending draft campaigns
    if campaign.status != 'draft':
        messages.error(request, 'Only draft campaigns can be sent.')
        return redirect('restaurant:campaign_detail', campaign_id=campaign.id)
    
    if request.method == 'POST':
        try:
            # Send the campaign
            results = campaign.send_campaign()
            
            # Show success message with results
            messages.success(
                request,
                f'Campaign "{campaign.name}" sent successfully! '
                f'{results["sent"]} emails sent, {results["failed"]} failed.'
            )
            
        except Exception as e:
            messages.error(
                request,
                f'Failed to send campaign: {str(e)}'
            )
    
    return redirect('restaurant:campaign_detail', campaign_id=campaign.id)


@login_required
def select_restaurant(request):
    """
    Display restaurant selection page for owners with multiple restaurants.
    Allows restaurant owners to choose which restaurant to manage.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered restaurant selection page template
    """
    # Get all restaurants owned by the user
    user_restaurants = Restaurant.objects.filter(owner=request.user)
    
    if not user_restaurants.exists():
        messages.error(request, 'You are not associated with any restaurant.')
        return redirect('customer:home')
    
    # If only one restaurant, select it automatically and redirect to dashboard
    if user_restaurants.count() == 1:
        restaurant = user_restaurants.first()
        request.session['selected_restaurant_id'] = restaurant.id
        return redirect('restaurant:dashboard')
    
    # Get today's orders for each restaurant to show stats
    today = timezone.now().date()
    restaurants_with_stats = []
    
    for restaurant in user_restaurants:
        orders_today = Order.objects.filter(
            created_at__date=today,
            items__menu_item__restaurant=restaurant
        ).distinct().count()
        
        restaurants_with_stats.append({
            'restaurant': restaurant,
            'orders_today': orders_today
        })
    
    context = {
        'restaurants_with_stats': restaurants_with_stats,
        'title': 'Select Restaurant'
    }
    
    return render(request, 'restaurant/select_restaurant.html', context)


@login_required
def set_restaurant(request, restaurant_id):
    """
    Set the selected restaurant in session and redirect to dashboard.
    
    Args:
        request: Django HTTP request object
        restaurant_id: ID of the restaurant to select
    
    Returns:
        HttpResponse: Redirect to restaurant dashboard
    """
    # Verify the restaurant belongs to the user
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id, owner=request.user)
        request.session['selected_restaurant_id'] = restaurant.id
        messages.success(request, f'Now managing: {restaurant.name}')
        return redirect('restaurant:dashboard')
    except Restaurant.DoesNotExist:
        messages.error(request, 'Invalid restaurant selection.')
        return redirect('restaurant:select_restaurant')


# ==================== TABLE MANAGEMENT VIEWS ====================

@restaurant_owner_required
def table_management(request):
    """
    Display table management page for restaurant owners.
    
    Shows all tables for the restaurant with options to add, edit, delete,
    and download QR codes.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered table management page template
    """
    from .models import RestaurantTable
    
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    # Get all tables for this restaurant
    tables = RestaurantTable.objects.filter(restaurant=restaurant).order_by('table_number')
    
    # Get filter parameters
    status_filter = request.GET.get('status')
    
    # Apply status filter
    if status_filter == 'active':
        tables = tables.filter(is_active=True)
    elif status_filter == 'inactive':
        tables = tables.filter(is_active=False)
    
    # Get statistics
    total_tables = tables.count()
    active_tables = tables.filter(is_active=True).count()
    inactive_tables = tables.filter(is_active=False).count()
    
    # === QR CODE ORDERING INTEGRATION ===
    # Use optimized queries with annotations to prevent N+1 issues
    from django.db.models import Q, Count, Sum, Case, When, IntegerField
    from orders.models import Order
    
    # Get all tables with order statistics in a single query
    tables_with_stats = tables.annotate(
        # Count active orders (pending, accepted, preparing)
        active_orders_count=Count(
            'orders',
            filter=Q(
                orders__status__in=['pending', 'accepted', 'preparing'],
                orders__items__menu_item__restaurant=restaurant
            ),
            distinct=True
        ),
        # Count orders needing payment completion
        payment_pending_count=Count(
            'orders',
            filter=Q(
                orders__status='delivered',
                orders__payment_status='pending',
                orders__items__menu_item__restaurant=restaurant
            ),
            distinct=True
        ),
        # Count total orders
        total_orders_count=Count(
            'orders',
            filter=Q(
                orders__items__menu_item__restaurant=restaurant
            ),
            distinct=True
        ),
        # Calculate total revenue
        total_revenue=Sum(
            'orders__total_amount',
            filter=Q(
                orders__items__menu_item__restaurant=restaurant
            ),
            distinct=True
        )
    )
    
    # Handle filtering
    status_filter = request.GET.get('status')
    qr_filter = request.GET.get('qr_filter')
    
    # Apply table status filtering
    if status_filter == 'available':
        tables_with_stats = tables_with_stats.filter(active_orders_count=0, payment_pending_count=0)
    elif status_filter == 'occupied':
        tables_with_stats = tables_with_stats.filter(active_orders_count__gt=0, payment_pending_count=0)
    elif status_filter == 'needs-attention':
        tables_with_stats = tables_with_stats.filter(payment_pending_count__gt=0)
    elif status_filter == 'active':
        tables_with_stats = tables_with_stats.filter(is_active=True)
    elif status_filter == 'inactive':
        tables_with_stats = tables_with_stats.filter(is_active=False)
    
    # Apply QR code filtering
    if qr_filter == 'generated':
        tables_with_stats = tables_with_stats.filter(qr_code__isnull=False).exclude(qr_code='')
    elif qr_filter == 'pending':
        tables_with_stats = tables_with_stats.filter(Q(qr_code__isnull=True) | Q(qr_code=''))
    
    # Build the final data structure
    tables_with_status = []
    for table in tables_with_stats:
        # Determine table status based on annotated values
        table_status = 'available'
        if table.payment_pending_count > 0:
            table_status = 'needs-attention'
        elif table.active_orders_count > 0:
            table_status = 'occupied'
        
        # Handle None values for revenue
        total_revenue = table.total_revenue or 0
        avg_revenue = total_revenue / table.total_orders_count if table.total_orders_count > 0 else 0
        
        tables_with_status.append({
            'table': table,
            'status': table_status,
            'active_orders_count': table.active_orders_count,
            'payment_pending_count': table.payment_pending_count,
            'total_orders_count': table.total_orders_count,
            'total_revenue': total_revenue,
            'avg_revenue_per_order': avg_revenue,
        })
    
    # Calculate overall statistics from the filtered queryset
    available_tables = sum(1 for t in tables_with_status if t['status'] == 'available')
    occupied_tables = sum(1 for t in tables_with_status if t['status'] == 'occupied')
    needs_attention_tables = sum(1 for t in tables_with_status if t['status'] == 'needs-attention')
    
    # Get QR code statistics from filtered queryset
    tables_with_qr = tables_with_stats.filter(qr_code__isnull=False).exclude(qr_code='').count()
    
    # Get recent table orders for quick reference
    recent_table_orders = Order.objects.filter(
        is_table_order=True,
        items__menu_item__restaurant=restaurant
    ).distinct().select_related('table').order_by('-created_at')[:10]
    
    context = {
        'restaurant': restaurant,
        'tables': tables,
        'tables_with_status': tables_with_status,
        'total_tables': total_tables,
        'active_tables': active_tables,
        'inactive_tables': inactive_tables,
        'available_tables': available_tables,
        'occupied_tables': occupied_tables,
        'needs_attention_tables': needs_attention_tables,
        'tables_with_qr': tables_with_qr,
        'recent_table_orders': recent_table_orders,
        'status_filter': status_filter,
    }
    
    return render(request, 'restaurant/table_management.html', context)


@restaurant_owner_required
def add_table(request):
    """
    Add a new table for the restaurant.
    
    Handles form submission for creating new tables with QR code generation.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered add table form or redirect to table management
    """
    from .models import RestaurantTable
    from .forms import RestaurantTableForm
    
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    if request.method == 'POST':
        form = RestaurantTableForm(request.POST)
        if form.is_valid():
            table = form.save(commit=False)
            table.restaurant = restaurant
            table.save()
            
            messages.success(
                request, 
                f'Table "{table.table_number}" has been created successfully! QR code generated.'
            )
            return redirect('restaurant:table_management')
    else:
        form = RestaurantTableForm()
    
    context = {
        'restaurant': restaurant,
        'form': form,
        'title': 'Add New Table',
        'action': 'Add',
    }
    
    return render(request, 'restaurant/table_form.html', context)


@restaurant_owner_required
def edit_table(request, table_id):
    """
    Edit an existing table.
    
    Handles form submission for updating table details.
    
    Args:
        request: Django HTTP request object
        table_id: ID of the table to edit
    
    Returns:
        HttpResponse: Rendered edit table form or redirect to table management
    """
    from .models import RestaurantTable
    from .forms import RestaurantTableForm
    
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    # Get table and verify ownership
    table = get_object_or_404(RestaurantTable, id=table_id, restaurant=restaurant)
    
    if request.method == 'POST':
        form = RestaurantTableForm(request.POST, instance=table)
        if form.is_valid():
            form.save()
            messages.success(request, f'Table "{table.table_number}" has been updated successfully!')
            return redirect('restaurant:table_management')
    else:
        form = RestaurantTableForm(instance=table)
    
    context = {
        'restaurant': restaurant,
        'table': table,
        'form': form,
        'title': 'Edit Table',
        'action': 'Update',
    }
    
    return render(request, 'restaurant/table_form.html', context)


@restaurant_owner_required
def delete_table(request, table_id):
    """
    Delete a table.
    
    Handles table deletion with confirmation.
    
    Args:
        request: Django HTTP request object
        table_id: ID of the table to delete
    
    Returns:
        HttpResponse: Redirect to table management with confirmation message
    """
    from .models import RestaurantTable
    
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    # Get table and verify ownership
    table = get_object_or_404(RestaurantTable, id=table_id, restaurant=restaurant)
    
    if request.method == 'POST':
        table_number = table.table_number
        
        # Delete QR code file with error handling
        if table.qr_code:
            try:
                import os
                if os.path.exists(table.qr_code.path):
                    os.remove(table.qr_code.path)
            except (AttributeError, OSError) as e:
                # Log error but don't fail the operation
                print(f"Warning: Could not delete QR code file: {e}")
        
        table.delete()
        messages.success(request, f'Table "{table_number}" has been deleted successfully!')
    
    return redirect('restaurant:table_management')


@restaurant_owner_required
def toggle_table_status(request, table_id):
    """
    Toggle the active status of a table.
    
    Quick toggle for table availability without full page reload.
    
    Args:
        request: Django HTTP request object
        table_id: ID of the table to toggle
    
    Returns:
        JsonResponse: JSON response with updated status
    """
    from .models import RestaurantTable
    
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        return JsonResponse({'success': False, 'message': 'No restaurant found.'})
    
    # Get table and verify ownership
    table = get_object_or_404(RestaurantTable, id=table_id, restaurant=restaurant)
    
    if request.method == 'POST':
        table.is_active = not table.is_active
        table.save()
        
        status_text = 'active' if table.is_active else 'inactive'
        status_color = 'green' if table.is_active else 'red'
        
        return JsonResponse({
            'success': True,
            'is_active': table.is_active,
            'status_text': status_text,
            'status_color': status_color,
            'message': f'Table "{table.table_number}" is now {status_text}.'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@restaurant_owner_required
def download_table_qr(request, table_id):
    """
    Download QR code for a specific table.
    
    Serves the QR code image as a downloadable file.
    
    Args:
        request: Django HTTP request object
        table_id: ID of the table
    
    Returns:
        HttpResponse: QR code image file download
    """
    from .models import RestaurantTable
    from django.http import FileResponse
    
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('restaurant:table_management')
    
    # Get table and verify ownership
    table = get_object_or_404(RestaurantTable, id=table_id, restaurant=restaurant)
    
    if not table.qr_code:
        messages.error(request, 'QR code not found for this table.')
        return redirect('restaurant:table_management')
    
    # Serve the QR code file
    try:
        response = FileResponse(table.qr_code.open('rb'), content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="table_{table.table_number}_qr.png"'
        return response
    except Exception as e:
        messages.error(request, f'Error downloading QR code: {str(e)}')
        return redirect('restaurant:table_management')


@restaurant_owner_required
def regenerate_table_qr(request, table_id):
    """
    Regenerate QR code for a specific table.
    
    Deletes old QR code and generates a new one.
    
    Args:
        request: Django HTTP request object
        table_id: ID of the table
    
    Returns:
        HttpResponse: Redirect to table management with message
    """
    from .models import RestaurantTable
    
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('restaurant:table_management')
    
    # Get table and verify ownership
    table = get_object_or_404(RestaurantTable, id=table_id, restaurant=restaurant)
    
    if request.method == 'POST':
        try:
            if table.regenerate_qr_code():
                messages.success(request, f'QR code for table "{table.table_number}" regenerated successfully!')
            else:
                messages.error(request, 'Failed to regenerate QR code. Please try again.')
        except Exception as e:
            messages.error(request, f'Error regenerating QR code: {str(e)}')
    
    return redirect('restaurant:table_management')


@restaurant_owner_required
def generate_missing_qr_codes(request):
    """
    Generate QR codes for all tables that don't have one.
    
    This function scans all tables for the current restaurant and generates
    QR codes for any tables that are missing them. Useful for bulk operations
    or fixing tables that failed to generate QR codes during creation.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Redirect to table management with success/error message
    """
    from .models import RestaurantTable
    
    # Get the user's restaurant using helper function
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        # Check if user has multiple restaurants and needs to select one
        user_restaurants = Restaurant.objects.filter(owner=request.user)
        if user_restaurants.count() > 1:
            return redirect('restaurant:select_restaurant')
        else:
            messages.error(request, 'No restaurant found for your account.')
            return redirect('customer:home')
    
    # Get all tables without QR codes
    tables_without_qr = RestaurantTable.objects.filter(
        restaurant=restaurant,
        qr_code__isnull=True
    ) | RestaurantTable.objects.filter(
        restaurant=restaurant,
        qr_code=''
    )
    
    if not tables_without_qr.exists():
        messages.info(request, 'All tables already have QR codes!')
        return redirect('restaurant:table_management')
    
    # Generate QR codes for tables
    success_count = 0
    failed_tables = []
    
    for table in tables_without_qr:
        try:
            if table.generate_qr_code():
                success_count += 1
            else:
                failed_tables.append(table.table_number)
        except Exception as e:
            failed_tables.append(table.table_number)
            print(f"Error generating QR code for table {table.table_number}: {str(e)}")
    
    # Show appropriate message
    if success_count > 0:
        messages.success(
            request,
            f'Successfully generated {success_count} QR code(s)!'
        )
    
    if failed_tables:
        messages.warning(
            request,
            f'Failed to generate QR codes for tables: {", ".join(failed_tables)}'
        )
    
    return redirect('restaurant:table_management')


# ============================================================================
# QR CODE ORDERING SYSTEM VIEWS
# Comprehensive views for managing table orders, printing receipts and bills
# ============================================================================

@restaurant_owner_required
def print_kitchen_receipt(request, order_id):
    """
    Print kitchen receipt for an order.
    
    This view generates a print-optimized kitchen receipt showing order details
    for kitchen staff. Includes table number, items, quantities, and special
    instructions.
    
    Workflow:
    =========
    1. Retrieve order by ID
    2. Verify restaurant ownership
    3. Load order items with details
    4. Render print-optimized template
    5. Auto-print on page load (via JavaScript)
    
    Args:
        request: Django HTTP request object
        order_id: UUID of the order
    
    Returns:
        HttpResponse: Rendered kitchen receipt template
    
    Template Context:
        order: Order instance with all details
        items: OrderItem queryset
        restaurant: Restaurant instance
        print_time: Current timestamp
    """
    from orders.models import Order
    
    # Get the user's restaurant
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('restaurant:dashboard')
    
    # Get order and verify it belongs to this restaurant
    order = get_object_or_404(Order, order_id=order_id)
    
    # Verify order belongs to restaurant (check via order items)
    if not order.items.filter(menu_item__restaurant=restaurant).exists():
        messages.error(request, 'This order does not belong to your restaurant.')
        return redirect('restaurant:order_list')
    
    # Get all order items with related data
    order_items = order.items.select_related('menu_item').all()
    
    context = {
        'order': order,
        'items': order_items,
        'restaurant': restaurant,
        'print_time': timezone.now(),
        'title': f'Kitchen Receipt - Order #{str(order.order_id)[:8]}',
    }
    
    return render(request, 'restaurant/kitchen_receipt.html', context)


@restaurant_owner_required
def print_final_bill(request, order_id):
    """
    Print final bill for customer.
    
    This view generates a detailed customer bill with itemized list, totals,
    discounts, taxes, and payment information. Print-optimized for thermal
    printers or standard printers.
    
    Workflow:
    =========
    1. Retrieve order by ID
    2. Verify restaurant ownership
    3. Calculate all totals and breakdowns
    4. Format payment and discount information
    5. Render print-optimized bill template
    6. Auto-print on page load
    
    Args:
        request: Django HTTP request object
        order_id: UUID of the order
    
    Returns:
        HttpResponse: Rendered final bill template
    
    Template Context:
        order: Order instance
        items: OrderItem queryset
        restaurant: Restaurant instance
        subtotal: Order subtotal before discounts
        tax_amount: Calculated tax amount
        grand_total: Final total amount
        print_time: Current timestamp
    """
    from orders.models import Order
    from decimal import Decimal
    
    # Get the user's restaurant
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('restaurant:dashboard')
    
    # Get order and verify ownership
    order = get_object_or_404(Order, order_id=order_id)
    
    # Verify order belongs to restaurant
    if not order.items.filter(menu_item__restaurant=restaurant).exists():
        messages.error(request, 'This order does not belong to your restaurant.')
        return redirect('restaurant:order_list')
    
    # Get all order items
    order_items = order.items.select_related('menu_item').all()
    
    # Calculate totals
    subtotal = sum(item.menu_item.price * item.quantity for item in order_items)
    tax_rate = Decimal('0.05')  # 5% tax
    tax_amount = subtotal * tax_rate
    grand_total = subtotal + tax_amount - order.discount_amount + order.delivery_charge
    
    context = {
        'order': order,
        'items': order_items,
        'restaurant': restaurant,
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'tax_rate': tax_rate * 100,  # Convert to percentage
        'grand_total': grand_total,
        'print_time': timezone.now(),
        'title': f'Final Bill - Order #{str(order.order_id)[:8]}',
    }
    
    return render(request, 'restaurant/final_bill.html', context)


@restaurant_owner_required
def add_items_to_order(request, order_id):
    """
    Add items to an existing order.
    
    Allows restaurant staff to add additional items to an active order.
    Useful when customers request more items after initial order placement.
    Updates order total automatically and logs modifications.
    
    Workflow:
    =========
    1. Retrieve order by ID
    2. Verify order is still active (not cancelled/delivered)
    3. Display menu items for selection
    4. Process item additions
    5. Update order total
    6. Log modification with staff member info
    7. Redirect back to order detail
    
    Args:
        request: Django HTTP request object
        order_id: UUID of the order
    
    Returns:
        HttpResponse: Rendered add items form or redirect after submission
    
    POST Data:
        menu_items: List of menu item IDs to add
        quantities: Corresponding quantities for each item
        notes: Optional notes for added items
    """
    from orders.models import Order, OrderItem
    from menu.models import MenuItem
    
    # Get the user's restaurant
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('restaurant:dashboard')
    
    # Get order and verify ownership
    order = get_object_or_404(Order, order_id=order_id)
    
    # Verify order belongs to restaurant
    if not order.items.filter(menu_item__restaurant=restaurant).exists():
        messages.error(request, 'This order does not belong to your restaurant.')
        return redirect('restaurant:order_list')
    
    # Check if order can be modified
    if order.status in ['delivered', 'cancelled']:
        messages.error(request, f'Cannot add items to {order.status} orders.')
        return redirect('restaurant:order_detail', order_id=order.order_id)
    
    if request.method == 'POST':
        # Get selected items and quantities
        item_ids = request.POST.getlist('menu_items[]')
        quantities = request.POST.getlist('quantities[]')
        notes = request.POST.get('notes', '')
        
        if not item_ids:
            messages.error(request, 'Please select at least one item to add.')
            return redirect('restaurant:add_items_to_order', order_id=order.order_id)
        
        # Add items to order
        items_added = 0
        total_added = Decimal('0.00')
        
        for item_id, quantity in zip(item_ids, quantities):
            try:
                menu_item = MenuItem.objects.get(id=item_id, restaurant=restaurant)
                qty = int(quantity)
                
                if qty > 0:
                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        quantity=qty,
                        price=menu_item.price
                    )
                    
                    items_added += 1
                    total_added += menu_item.price * qty
                    
            except (MenuItem.DoesNotExist, ValueError):
                continue
        
        # Update order total and notes
        if items_added > 0:
            order.total_amount += total_added
            
            # Add notes to order if provided
            if notes:
                if order.notes:
                    order.notes += f"\n\nAdditional items: {notes}"
                else:
                    order.notes = f"Additional items: {notes}"
            
            order.save()
            
            messages.success(
                request,
                f'Successfully added {items_added} item(s) to the order. '
                f'Total increased by ₹{total_added}.'
            )
        else:
            messages.error(request, 'No valid items were added.')
        
        return redirect('restaurant:order_detail', order_id=order.order_id)
    
    # GET request - show add items form
    # Get available menu items
    menu_items = MenuItem.objects.filter(
        restaurant=restaurant,
        is_available=True
    ).select_related('category').order_by('category__name', 'name')
    
    # Group items by category
    from itertools import groupby
    items_by_category = {}
    for category, items in groupby(menu_items, key=lambda x: x.category):
        items_by_category[category] = list(items)
    
    context = {
        'order': order,
        'restaurant': restaurant,
        'items_by_category': items_by_category,
        'title': f'Add Items to Order #{str(order.order_id)[:8]}',
    }
    
    return render(request, 'restaurant/add_items_to_order.html', context)


@restaurant_owner_required
def create_table_order(request, table_id):
    """
    Create a new order for a specific table.
    
    Allows restaurant staff to place orders on behalf of customers sitting
    at tables. Creates dine-in or staff orders linked to the table.
    
    Workflow:
    =========
    1. Retrieve table by ID
    2. Verify table belongs to restaurant
    3. Display menu for item selection
    4. Build cart with selected items
    5. Process order submission
    6. Link order to table
    7. Mark as staff order type
    8. Optionally print kitchen receipt
    
    Args:
        request: Django HTTP request object
        table_id: ID of the restaurant table
    
    Returns:
        HttpResponse: Rendered order form or redirect after submission
    
    POST Data:
        customer_name: Customer name (optional for dine-in)
        customer_phone: Phone number (optional)
        items: List of menu items with quantities
        notes: Special instructions
        print_kitchen: Whether to print kitchen receipt immediately
    """
    from restaurant.models import RestaurantTable
    from orders.models import Order, OrderItem
    from menu.models import MenuItem
    from decimal import Decimal
    
    # Get the user's restaurant
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('restaurant:dashboard')
    
    # Get table and verify ownership
    table = get_object_or_404(RestaurantTable, id=table_id, restaurant=restaurant)
    
    if not table.is_active:
        messages.error(request, f'Table {table.table_number} is currently inactive.')
        return redirect('restaurant:table_management')
    
    if request.method == 'POST':
        # Get order details
        customer_name = request.POST.get('customer_name', f'Table {table.table_number}')
        customer_phone = request.POST.get('customer_phone', 'N/A')
        notes = request.POST.get('notes', '')
        item_ids = request.POST.getlist('menu_items[]')
        quantities = request.POST.getlist('quantities[]')
        print_kitchen = request.POST.get('print_kitchen') == 'on'
        
        if not item_ids:
            messages.error(request, 'Please select at least one item.')
            return redirect('restaurant:create_table_order', table_id=table.id)
        
        # Calculate total
        total_amount = Decimal('0.00')
        order_items_data = []
        
        for item_id, quantity in zip(item_ids, quantities):
            try:
                menu_item = MenuItem.objects.get(id=item_id, restaurant=restaurant)
                qty = int(quantity)
                
                if qty > 0:
                    item_total = menu_item.price * qty
                    total_amount += item_total
                    order_items_data.append({
                        'menu_item': menu_item,
                        'quantity': qty,
                        'price': menu_item.price
                    })
                    
            except (MenuItem.DoesNotExist, ValueError):
                continue
        
        if not order_items_data:
            messages.error(request, 'No valid items selected.')
            return redirect('restaurant:create_table_order', table_id=table.id)
        
        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            table=table,
            order_type='staff',
            is_table_order=True,
            customer_name=customer_name,
            customer_phone=customer_phone,
            delivery_method='dine_in',
            total_amount=total_amount,
            status='accepted',  # Staff orders are pre-accepted
            notes=notes,
            payment_method='cod',
            payment_status='pending'
        )
        
        # Create order items
        for item_data in order_items_data:
            OrderItem.objects.create(
                order=order,
                menu_item=item_data['menu_item'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
        
        messages.success(
            request,
            f'Order created successfully for Table {table.table_number}! '
            f'Order ID: #{str(order.order_id)[:8]}'
        )
        
        # Redirect to kitchen receipt if requested
        if print_kitchen:
            return redirect('restaurant:print_kitchen_receipt', order_id=order.order_id)
        else:
            return redirect('restaurant:order_detail', order_id=order.order_id)
    
    # GET request - show order form
    # Get available menu items
    menu_items = MenuItem.objects.filter(
        restaurant=restaurant,
        is_available=True
    ).select_related('category').order_by('category__name', 'name')
    
    # Group items by category
    from itertools import groupby
    items_by_category = {}
    for category, items in groupby(menu_items, key=lambda x: x.category):
        items_by_category[category] = list(items)
    
    context = {
        'table': table,
        'restaurant': restaurant,
        'items_by_category': items_by_category,
        'title': f'Create Order for Table {table.table_number}',
    }
    
    return render(request, 'restaurant/create_table_order.html', context)


@restaurant_owner_required
def table_orders_list(request):
    """
    View all table-based orders (QR code and dine-in orders).
    
    Displays a filtered list of orders placed through QR codes or by staff
    for tables. Allows filtering by status, table, and date range.
    
    Features:
    =========
    - Filter by order status
    - Filter by table number
    - Filter by date range
    - Search by order ID or customer name
    - Quick actions: Print, Add Items, Complete
    - Real-time status updates
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered table orders list template
    
    GET Parameters:
        status: Filter by order status
        table: Filter by table ID
        date_from: Start date for filtering
        date_to: End date for filtering
        search: Search term for order ID or customer name
    """
    from orders.models import Order
    from restaurant.models import RestaurantTable
    from django.db.models import Q
    
    # Get the user's restaurant
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('restaurant:dashboard')
    
    # Get all table orders for this restaurant
    orders = Order.objects.filter(
        items__menu_item__restaurant=restaurant,
        is_table_order=True
    ).distinct().select_related('table', 'user').prefetch_related('items__menu_item')
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    table_filter = request.GET.get('table')
    if table_filter:
        orders = orders.filter(table_id=table_filter)
    
    date_from = request.GET.get('date_from')
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            Q(order_id__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(customer_phone__icontains=search)
        )
    
    # Order by most recent first
    orders = orders.order_by('-created_at')
    
    # Calculate statistics for the current filtered queryset
    active_orders_count = orders.filter(
        status__in=['pending', 'accepted', 'preparing', 'serving']
    ).count()
    
    qr_orders_count = orders.filter(order_type='qr_code').count()
    staff_orders_count = orders.filter(order_type='staff').count()
    
    # Pagination
    paginator = Paginator(orders, 20)  # 20 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all tables for filter dropdown
    tables = RestaurantTable.objects.filter(restaurant=restaurant).order_by('table_number')
    
    # Get order status choices
    status_choices = Order.STATUS_CHOICES
    
    context = {
        'orders': page_obj,
        'restaurant': restaurant,
        'tables': tables,
        'status_choices': status_choices,
        'current_status': status_filter,
        'current_table': table_filter,
        'title': 'Table Orders',
        'active_orders_count': active_orders_count,
        'qr_orders_count': qr_orders_count,
        'staff_orders_count': staff_orders_count,
    }
    
    return render(request, 'restaurant/table_orders_list.html', context)


@restaurant_owner_required
def table_layout_view(request):
    """
    Display restaurant tables in an enhanced visual floor plan layout with real-time data.
    
    Shows tables organized by sections (A/C, Non A/C, Bar) with comprehensive information:
    - Real-time order status and details
    - Customer information and order duration
    - Total amounts and item counts
    - Visual status indicators with color coding
    - Interactive features for order management
    
    Features:
    =========
    - Enhanced data queries with select_related/prefetch_related for performance
    - Real-time order information (duration, total, customer details)
    - Visual status indicators (available, occupied, needs attention)
    - Section-wise organization with statistics
    - Responsive design support with Tailwind CSS
    - Interactive table cards with quick actions
    
    Args:
        request: HttpRequest object containing user session and request data
        
    Returns:
        HttpResponse: Rendered enhanced table layout page with comprehensive data
        
    Database Optimization:
    =====================
    Uses efficient queries with:
    - select_related for restaurant and customer relationships
    - prefetch_related for order items to avoid N+1 queries
    - annotate for calculated fields (order duration, totals)
    - Database-level filtering for active orders
    
    Template Context:
    =================
    Provides comprehensive data including:
    - tables_by_section: Grouped tables with enhanced status information
    - restaurant: Current restaurant object
    - title: Page title
    - total_stats: Overall restaurant statistics
    - section_stats: Detailed section-wise statistics
    """
    # Get selected restaurant for multi-restaurant owners
    restaurant = get_selected_restaurant(request)
    
    # Enhanced query with optimized database access
    # Get all active tables with related restaurant data
    tables = RestaurantTable.objects.filter(
        restaurant=restaurant,
        is_active=True
    ).select_related(
        'restaurant'
    ).order_by('section', 'table_number')
    
    # Initialize data structures for enhanced table information
    tables_with_status = []
    section_stats = {
        'ac': {'total': 0, 'available': 0, 'occupied': 0, 'reserved': 0, 'needs_attention': 0},
        'non_ac': {'total': 0, 'available': 0, 'occupied': 0, 'reserved': 0, 'needs_attention': 0},
        'bar': {'total': 0, 'available': 0, 'occupied': 0, 'reserved': 0, 'needs_attention': 0}
    }
    
    # Process each table with enhanced data collection
    for table in tables:
        # Enhanced order query with optimized relationships
        # Get active orders with user and item details for comprehensive display
        active_orders = Order.objects.filter(
            table=table,
            status__in=['pending', 'accepted', 'preparing', 'serving', 'out_for_delivery', 'ready']
        ).select_related(
            'user'
        ).prefetch_related(
            'items', 'items__menu_item'
        ).order_by('-created_at')
        
        # Get completed orders that need attention (payment pending)
        completed_orders = Order.objects.filter(
            table=table,
            status='ready',
            payment_status__in=['pending', 'failed']
        ).select_related(
            'user'
        ).prefetch_related(
            'items'
        )
        
        # Enhanced table status determination with comprehensive logic
        table_status = 'available'
        status_class = 'available'
        status_icons = []
        order_info = None
        needs_attention = False
        
        if active_orders.exists():
            # Get the most recent active order for primary status display
            current_order = active_orders.first()
            table_status = 'occupied'
            status_class = 'occupied'
            
            # Calculate order duration for time tracking
            order_duration = None
            if current_order.created_at:
                from datetime import datetime
                now = timezone.now()
                duration = now - current_order.created_at
                order_duration = int(duration.total_seconds() / 60)  # Duration in minutes
            
            # Calculate order total and item count for display
            order_total = current_order.total_amount or 0
            item_count = current_order.items.count() if current_order.items.exists() else 0
            
            # Determine status icons based on order workflow
            if current_order.status in ['pending', 'accepted']:
                status_icons.append('running')  # Order is active and being processed
            elif current_order.status == 'preparing':
                status_icons.append('kot')  # Kitchen Order Ticket active
            elif current_order.status == 'serving':
                status_icons.append('serving')  # Food is being served to customers
            elif current_order.status in ['out_for_delivery', 'ready']:
                status_icons.append('printed')  # Order ready for service
            
            # Check payment status for comprehensive status tracking
            if hasattr(current_order, 'payment_status'):
                if current_order.payment_status == 'completed':
                    status_icons.append('paid')
                    table_status = 'reserved'
                    status_class = 'reserved'
                elif current_order.payment_status in ['pending', 'failed']:
                    needs_attention = True
            
            # Create comprehensive order information object
            order_info = {
                'order': current_order,
                'duration_minutes': order_duration,
                'total_amount': order_total,
                'item_count': item_count,
                'customer_name': current_order.user.get_full_name() or current_order.user.username,
                'status_display': current_order.get_status_display(),
                'payment_status': getattr(current_order, 'payment_status', None),
                'created_time': current_order.created_at.strftime('%H:%M') if current_order.created_at else None,
                'items_preview': list(current_order.items.values_list('menu_item__name', flat=True)[:3])
            }
        
        elif completed_orders.exists():
            # Table needs attention for payment completion
            table_status = 'needs_attention'
            status_class = 'needs-attention'
            status_icons.append('payment-pending')
            needs_attention = True
            
            # Get completed order info for attention display
            completed_order = completed_orders.first()
            order_info = {
                'order': completed_order,
                'total_amount': completed_order.total_amount or 0,
                'customer_name': completed_order.user.get_full_name() or completed_order.user.username,
                'payment_status': completed_order.payment_status,
                'needs_payment': True
            }
        
        # Update section statistics with comprehensive tracking
        section_stats[table.section]['total'] += 1
        section_stats[table.section][table_status] += 1
        if needs_attention:
            section_stats[table.section]['needs_attention'] += 1
        
        # Create enhanced table data object with comprehensive information
        table_data = {
            'table': table,
            'status': table_status,
            'status_class': status_class,
            'status_icons': status_icons,
            'order_info': order_info,
            'active_orders': active_orders,
            'active_orders_count': active_orders.count(),
            'completed_orders': completed_orders,
            'needs_attention': needs_attention,
            'capacity': table.capacity,
            'location': table.location_description,
            'qr_code_url': table.get_qr_code_url() if hasattr(table, 'get_qr_code_url') else None
        }
        
        tables_with_status.append(table_data)
    
    # Group tables by section for organized template rendering
    tables_by_section = {}
    section_names = {
        'ac': 'A/C Section',
        'non_ac': 'Non A/C Section', 
        'bar': 'Bar Area'
    }
    
    for section_key, section_name in section_names.items():
        section_tables = [t for t in tables_with_status if t['table'].section == section_key]
        tables_by_section[section_key] = {
            'name': section_name,
            'tables': section_tables,
            'stats': section_stats[section_key],
            'available_count': len([t for t in section_tables if t['status'] == 'available']),
            'occupied_count': len([t for t in section_tables if t['status'] == 'occupied']),
            'attention_count': len([t for t in section_tables if t['needs_attention']])
        }
    
    # Calculate comprehensive overall statistics
    total_stats = {
        'total': len(tables_with_status),
        'available': sum(section_stats[s]['available'] for s in section_stats),
        'occupied': sum(section_stats[s]['occupied'] for s in section_stats),
        'reserved': sum(section_stats[s]['reserved'] for s in section_stats),
        'needs_attention': sum(section_stats[s]['needs_attention'] for s in section_stats)
    }
    
    # Prepare comprehensive context for template rendering
    context = {
        'tables_by_section': tables_by_section,
        'restaurant': restaurant,
        'title': 'Restaurant Table Layout - Real-time Status',
        'total_stats': total_stats,
        'section_stats': section_stats,
        'total_tables': total_stats['total'],
        'available_tables': total_stats['available'],
        'occupied_tables': total_stats['occupied'],
        'reserved_tables': total_stats['reserved'],
        'tables_needing_attention': total_stats['needs_attention'],
        'current_time': timezone.now().strftime('%H:%M:%S'),
        'current_date': timezone.now().strftime('%Y-%m-%d'),
        # Enhanced data for interactive features
        'has_active_orders': any(t['active_orders_count'] > 0 for t in tables_with_status),
        'total_active_orders': sum(t['active_orders_count'] for t in tables_with_status),
        'total_revenue_today': sum(
            t['order_info']['total_amount'] for t in tables_with_status 
            if t['order_info'] and t['order_info'].get('order', None) and 
            t['order_info']['order'].created_at.date() == timezone.now().date()
        )
    }
    
    return render(request, 'restaurant/table_layout.html', context)


@restaurant_owner_required
def table_selection_view(request):
    """
    Display restaurant tables in card layout for staff to select and place orders.
    
    Shows all active tables with their current status (available/occupied),
    capacity, and location. Each table card is clickable to start a new order.
    
    Args:
        request: HttpRequest object
        
    Returns:
        HttpResponse: Rendered table selection page
    """
    # Get selected restaurant
    restaurant = get_selected_restaurant(request)
    
    # Get all active tables for this restaurant
    tables = RestaurantTable.objects.filter(
        restaurant=restaurant,
        is_active=True
    ).order_by('table_number')
    
    # Annotate each table with its current status
    tables_with_status = []
    for table in tables:
        # Check if table has active orders (not delivered or cancelled)
        active_orders = Order.objects.filter(
            table=table,
            status__in=['pending', 'accepted', 'preparing', 'serving', 'out_for_delivery']
        )
        
        table_status = 'available' if not active_orders.exists() else 'occupied'
        current_order = active_orders.first() if active_orders.exists() else None
        
        tables_with_status.append({
            'table': table,
            'status': table_status,
            'current_order': current_order,
            'active_orders_count': active_orders.count()
        })
    
    context = {
        'tables_with_status': tables_with_status,
        'restaurant': restaurant,
        'title': 'Select Table for Order',
        'total_tables': len(tables_with_status),
        'available_tables': len([t for t in tables_with_status if t['status'] == 'available']),
        'occupied_tables': len([t for t in tables_with_status if t['status'] == 'occupied']),
    }
    
    return render(request, 'restaurant/table_selection.html', context)


@restaurant_owner_required
def table_status_ajax(request):
    """
    AJAX endpoint to fetch real-time table status updates.
    
    Returns JSON data with current table status, active orders,
    and last updated timestamp for auto-refresh functionality.
    
    Args:
        request: Django HTTP request object (must be AJAX)
    
    Returns:
        JsonResponse: JSON with table status data or error message
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    # Get selected restaurant
    restaurant = get_selected_restaurant(request)
    
    # Get all active tables with their current status
    tables = RestaurantTable.objects.filter(
        restaurant=restaurant,
        is_active=True
    ).order_by('table_number')
    
    # Prepare table status data
    tables_data = []
    for table in tables:
        # Check if table has active orders
        active_orders = Order.objects.filter(
            table=table,
            status__in=['pending', 'accepted', 'preparing', 'out_for_delivery']
        )
        
        current_order = active_orders.first() if active_orders.exists() else None
        
        table_data = {
            'table_id': str(table.id),
            'table_number': table.table_number,
            'capacity': table.capacity,
            'location_description': table.location_description or '',
            'status': 'available' if not active_orders.exists() else 'occupied',
            'active_orders_count': active_orders.count()
        }
        
        # Add order details if table is occupied
        if current_order:
            table_data.update({
                'order_id': str(current_order.order_id),
                'customer_name': current_order.customer_name or 'Guest',
                'customer_phone': current_order.customer_phone or 'N/A',
                'order_status': current_order.get_status_display(),
                'order_status_code': current_order.status
            })
        
        tables_data.append(table_data)
    
    # Calculate statistics
    total_tables = len(tables_data)
    available_tables = len([t for t in tables_data if t['status'] == 'available'])
    occupied_tables = len([t for t in tables_data if t['status'] == 'occupied'])
    
    response_data = {
        'tables': tables_data,
        'statistics': {
            'total_tables': total_tables,
            'available_tables': available_tables,
            'occupied_tables': occupied_tables
        },
        'last_updated': timezone.now().isoformat(),
        'restaurant': {
            'name': restaurant.name,
            'id': str(restaurant.id)
        }
    }
    
    return JsonResponse(response_data)


@restaurant_owner_required
def floor_plan_ajax(request):
    """
    AJAX endpoint to fetch floor plan view HTML.
    
    Returns HTML fragment for visual table layout view
    that can be loaded dynamically without page refresh.
    
    Args:
        request: Django HTTP request object (must be AJAX)
    
    Returns:
        JsonResponse: JSON with HTML content or error message
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    # Get selected restaurant
    restaurant = get_selected_restaurant(request)
    
    # Get all active tables
    tables = RestaurantTable.objects.filter(
        restaurant=restaurant,
        is_active=True
    ).order_by('table_number')
    
    # Get table status for floor plan
    tables_with_status = []
    for table in tables:
        active_orders = Order.objects.filter(
            table=table,
            status__in=['pending', 'accepted', 'preparing', 'out_for_delivery']
        )
        
        table_status = 'available' if not active_orders.exists() else 'occupied'
        current_order = active_orders.first() if active_orders.exists() else None
        
        tables_with_status.append({
            'table': table,
            'status': table_status,
            'current_order': current_order,
            'active_orders_count': active_orders.count()
        })
    
    # Render floor plan template fragment using existing table_layout template
    from django.template.loader import render_to_string
    html_content = render_to_string('restaurant/table_layout.html', {
        'tables_with_status': tables_with_status,
        'restaurant': restaurant
    }, request=request)
    
    return JsonResponse({
        'html': html_content,
        'last_updated': timezone.now().isoformat()
    })


@restaurant_owner_required
def active_tables_view(request):
    """
    View all active tables with their current order status.
    
    Displays a visual board showing all restaurant tables with their status:
    - Available (no active orders)
    - Occupied (has active orders)
    - Needs attention (order ready/completed)
    
    Features:
    =========
    - Visual table status board
    - Quick access to create orders
    - View active orders for each table
    - Mark tables as needing service
    - Real-time updates
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered active tables board template
    """
    from restaurant.models import RestaurantTable
    from orders.models import Order
    from django.db.models import Count, Q, Max
    
    # Get the user's restaurant
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('restaurant:dashboard')
    
    # Get all active tables
    tables = RestaurantTable.objects.filter(
        restaurant=restaurant,
        is_active=True
    ).order_by('table_number')
    
    # Annotate tables with order information
    tables_with_orders = []
    for table in tables:
        # Get active orders for this table
        active_orders = Order.objects.filter(
            table=table,
            status__in=['pending', 'accepted', 'preparing']
        ).order_by('-created_at')
        
        # Get completed orders waiting for payment
        completed_orders = Order.objects.filter(
            table=table,
            status='delivered',
            payment_status='pending'
        )
        
        table_data = {
            'table': table,
            'active_orders': active_orders,
            'completed_orders': completed_orders,
            'status': 'available' if not active_orders.exists() else 'occupied',
            'needs_attention': completed_orders.exists(),
        }
        
        tables_with_orders.append(table_data)
    
    context = {
        'tables_data': tables_with_orders,
        'restaurant': restaurant,
        'title': 'Active Tables Board',
    }
    
    return render(request, 'restaurant/active_tables.html', context)


@restaurant_owner_required  
def mark_order_complete(request, order_id):
    """
    Mark an order as complete.
    
    Updates order status to 'delivered' and marks payment as completed.
    Used when customer has paid and the order is fully serviced.
    
    Args:
        request: Django HTTP request object
        order_id: UUID of the order
    
    Returns:
        HttpResponse: Redirect to order list or detail page
    """
    from orders.models import Order
    
    # Get the user's restaurant
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        messages.error(request, 'No restaurant found for your account.')
        return redirect('restaurant:dashboard')
    
    # Get order and verify ownership
    order = get_object_or_404(Order, order_id=order_id)
    
    # Verify order belongs to restaurant
    if not order.items.filter(menu_item__restaurant=restaurant).exists():
        messages.error(request, 'This order does not belong to your restaurant.')
        return redirect('restaurant:order_list')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', order.payment_method)
        
        # Update order status
        order.status = 'delivered'
        order.payment_status = 'completed'
        order.payment_method = payment_method
        order.save()
        
        messages.success(
            request,
            f'Order #{str(order.order_id)[:8]} marked as complete!'
        )
        
        return redirect('restaurant:table_orders_list')
    
    context = {
        'order': order,
        'restaurant': restaurant,
        'title': f'Complete Order #{str(order.order_id)[:8]}',
    }
    
    return render(request, 'restaurant/mark_order_complete.html', context)


@restaurant_owner_required
def get_table_status_api(request):
    """
    API endpoint to get real-time table status data.
    
    Returns JSON data with current status of all tables including:
    - Table availability status
    - Active orders information
    - Customer details
    - Order duration
    - Total amounts
    
    This endpoint is used by the POS Table View for real-time updates.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        JsonResponse: JSON data with table statuses organized by section
    """
    from restaurant.models import RestaurantTable
    from orders.models import Order
    
    # Get the user's restaurant
    restaurant = get_selected_restaurant(request)
    
    if not restaurant:
        return JsonResponse({'error': 'No restaurant found'}, status=400)
    
    # Initialize response data structure
    response_data = {
        'sections': {
            'ac': {'tables': [], 'available_count': 0, 'occupied_count': 0, 'attention_count': 0},
            'non_ac': {'tables': [], 'available_count': 0, 'occupied_count': 0, 'attention_count': 0},
            'bar': {'tables': [], 'available_count': 0, 'occupied_count': 0, 'attention_count': 0},
        },
        'totals': {
            'available': 0,
            'occupied': 0,
            'running_kot': 0,
        },
        'timestamp': timezone.now().strftime('%H:%M:%S')
    }
    
    # Get all tables for the restaurant
    tables = RestaurantTable.objects.filter(
        restaurant=restaurant,
        is_active=True
    ).order_by('table_number')
    
    # Process each table
    for table in tables:
        # Check for active orders
        active_orders = Order.objects.filter(
            table=table,
            status__in=['pending', 'accepted', 'preparing']
        ).distinct().count()
        
        # Check for completed orders needing payment
        completed_orders = Order.objects.filter(
            table=table,
            status='delivered',
            payment_status='pending'
        ).distinct().count()
        
        # Determine table status
        status = 'available'
        status_class = 'blank'
        status_icons = []
        
        if active_orders > 0:
            status = 'occupied'
            status_class = 'running'
            status_icons = ['running']
        elif completed_orders > 0:
            status = 'needs-attention'
            status_class = 'needs-attention'
            status_icons = ['payment-pending']
        
        # Get order information for occupied tables
        order_info = None
        if status == 'occupied':
            latest_order = Order.objects.filter(
                table=table,
                status__in=['pending', 'accepted', 'preparing']
            ).order_by('-created_at').first()
            
            if latest_order:
                duration_minutes = int((timezone.now() - latest_order.created_at).total_seconds() / 60)
                order_info = {
                    'order_id': str(latest_order.order_id),
                    'customer_name': latest_order.customer_name or 'Walk-in',
                    'duration_minutes': duration_minutes,
                    'item_count': latest_order.items.count(),
                    'total_amount': float(latest_order.total_amount),
                    'status': latest_order.status,
                    'status_display': latest_order.get_status_display()
                }
        
        # Determine section
        section_key = 'ac'  # default
        if hasattr(table, 'section'):
            section_key = table.section.lower()
        elif table.table_number.startswith('B'):
            section_key = 'bar'
        else:
            try:
                if int(table.table_number) > 20:
                    section_key = 'non_ac'
            except (ValueError, TypeError):
                section_key = 'ac'
        
        # Ensure section exists
        if section_key not in response_data['sections']:
            section_key = 'ac'
        
        # Build table data
        table_data = {
            'table_number': table.table_number,
            'table_id': table.id,
            'status': status,
            'status_class': status_class,
            'status_icons': status_icons,
            'order_info': order_info,
            'capacity': getattr(table, 'capacity', 4),
            'location': getattr(table, 'location', None),
        }
        
        # Add to section
        response_data['sections'][section_key]['tables'].append(table_data)
        
        # Update counts
        if status == 'available':
            response_data['sections'][section_key]['available_count'] += 1
            response_data['totals']['available'] += 1
        elif status == 'occupied':
            response_data['sections'][section_key]['occupied_count'] += 1
            response_data['totals']['occupied'] += 1
        elif status == 'needs-attention':
            response_data['sections'][section_key]['attention_count'] += 1
    
    # Calculate running KOT count
    response_data['totals']['running_kot'] = Order.objects.filter(
        table__restaurant=restaurant,
        status__in=['accepted', 'preparing'],
        is_table_order=True
    ).distinct().count()
    
    return JsonResponse(response_data)
