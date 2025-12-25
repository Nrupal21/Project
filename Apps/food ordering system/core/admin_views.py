"""
Admin monitoring views for comprehensive website analytics.
Provides privacy-safe aggregated statistics and monitoring capabilities.
Enhanced with real-time charts and comprehensive system-wide reporting.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Sum, Avg, Q, F, Case, When, Value, CharField
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek, TruncHour
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET
import json
import csv

# Import models for monitoring
from django.contrib.auth.models import User
from restaurant.models import Restaurant
from menu.models import MenuItem, Category
from orders.models import Order, OrderItem
from customer.models import RestaurantReview, MenuItemReview, Wishlist

# Import our analytics engine
from .system_analytics import SystemAnalytics

# Try to import Axes for security analytics
try:
    from axes.models import AccessAttempt
    AXES_AVAILABLE = True
except ImportError:
    AXES_AVAILABLE = False


@staff_member_required
def monitoring_dashboard(request):
    """
    Enhanced main monitoring dashboard with comprehensive analytics.
    Displays real-time charts and KPIs for system-wide monitoring.
    """
    analytics = SystemAnalytics()
    dashboard_data = analytics.get_comprehensive_dashboard()
    
    context = {
        'title': '📊 System Analytics Dashboard',
        'dashboard_data': dashboard_data,
        'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    return render(request, 'admin/analytics_dashboard.html', context)


@staff_member_required
@cache_page(300)
def authentication_analytics(request):
    """
    Detailed authentication and security analytics dashboard.
    Focuses on user activity, login trends, and security metrics.
    """
    analytics = SystemAnalytics()
    auth_data = analytics.get_authentication_analytics()
    
    # Additional authentication-specific metrics
    login_success_rate = 0
    if auth_data['active_users_today'] > 0:
        login_success_rate = round((auth_data['active_users_today'] / (auth_data['active_users_today'] + auth_data['failed_attempts_today'])) * 100, 1)
    
    auth_data['login_success_rate'] = login_success_rate
    
    context = {
        'title': '🔐 Authentication & Security Analytics',
        'auth_data': auth_data,
        'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    return render(request, 'admin/authentication_analytics.html', context)


@staff_member_required
def business_analytics(request):
    """
    Comprehensive business and revenue analytics dashboard.
    Shows order trends, revenue metrics, and performance indicators.
    """
    analytics = SystemAnalytics()
    business_data = analytics.get_business_analytics()
    
    # Calculate growth rates
    if business_data['revenue_today'] > 0:
        business_data['daily_growth'] = round(((business_data['revenue_today'] - (business_data['revenue_month'] / 30)) / (business_data['revenue_month'] / 30)) * 100, 1)
    else:
        business_data['daily_growth'] = 0
    
    context = {
        'title': '💰 Business & Revenue Analytics',
        'business_data': business_data,
        'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    return render(request, 'admin/business_analytics.html', context)


@staff_member_required
def restaurant_analytics(request):
    """
    Restaurant performance and inventory analytics dashboard.
    Monitors restaurant metrics, menu performance, and cuisine trends.
    Enhanced with sales trend charts from restaurant dashboard.
    """
    analytics = SystemAnalytics()
    restaurant_data = analytics.get_restaurant_analytics()
    
    # Calculate restaurant health metrics
    if restaurant_data['total_restaurants'] > 0:
        restaurant_data['activation_rate'] = round((restaurant_data['active_restaurants'] / restaurant_data['total_restaurants']) * 100, 1)
    else:
        restaurant_data['activation_rate'] = 0
    
    # Calculate inventory percentages for CSS (avoid template filters in styles)
    if restaurant_data['total_menu_items'] > 0:
        restaurant_data['available_percentage'] = round((restaurant_data['available_items'] / restaurant_data['total_menu_items']) * 100, 1)
        restaurant_data['out_of_stock_percentage'] = round((restaurant_data['out_of_stock'] / restaurant_data['total_menu_items']) * 100, 1)
    else:
        restaurant_data['available_percentage'] = 0
        restaurant_data['out_of_stock_percentage'] = 0
    
    # Generate sales trend data for charts (like restaurant dashboard)
    from orders.models import Order
    from django.db.models.functions import TruncDate
    import json
    
    # Daily sales for last 30 days
    daily_sales = Order.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        revenue=Sum('total_amount'),
        orders=Count('id')
    ).order_by('date')
    
    # Monthly sales for last 12 months
    monthly_sales = Order.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=365)
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        revenue=Sum('total_amount'),
        orders=Count('id')
    ).order_by('month')
    
    # Convert to JSON for Chart.js
    daily_sales_json = json.dumps([
        {
            'date': item['date'].strftime('%Y-%m-%d'),
            'revenue': float(item['revenue']),
            'orders': item['orders']
        } for item in daily_sales
    ])
    
    monthly_sales_json = json.dumps([
        {
            'month': item['month'].strftime('%Y-%m'),
            'revenue': float(item['revenue']),
            'orders': item['orders']
        } for item in monthly_sales
    ])
    
    context = {
        'title': '🍽️ Restaurant Performance Analytics',
        'restaurant_data': restaurant_data,
        'daily_sales_json': daily_sales_json,
        'monthly_sales_json': monthly_sales_json,
        'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    return render(request, 'admin/restaurant_analytics.html', context)


@staff_member_required
def customer_analytics(request):
    """
    Customer behavior and engagement analytics dashboard.
    Tracks reviews, ratings, wishlist activity, and customer satisfaction.
    """
    analytics = SystemAnalytics()
    customer_data = analytics.get_customer_analytics()
    
    # Calculate engagement metrics
    total_reviews = customer_data['total_restaurant_reviews'] + customer_data['total_menu_reviews']
    if total_reviews > 0:
        customer_data['engagement_rate'] = round((total_reviews / 100) * 10, 1)  # Simplified calculation
    else:
        customer_data['engagement_rate'] = 0
    
    context = {
        'title': '👥 Customer Engagement Analytics',
        'customer_data': customer_data,
        'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    return render(request, 'admin/customer_analytics.html', context)


@staff_member_required
def system_health_analytics(request):
    """
    System health and performance monitoring dashboard.
    Tracks database metrics, system performance, and operational health.
    """
    analytics = SystemAnalytics()
    health_data = analytics.get_system_health_analytics()
    
    context = {
        'title': '⚙️ System Health & Performance',
        'health_data': health_data,
        'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    return render(request, 'admin/system_health_analytics.html', context)


@staff_member_required
@require_GET
def api_real_time_stats(request):
    """
    API endpoint for real-time statistics updates.
    Returns JSON data for AJAX dashboard updates.
    """
    analytics = SystemAnalytics()
    
    # Get specific data type from request
    data_type = request.GET.get('type', 'overview')
    
    if data_type == 'authentication':
        data = analytics.get_authentication_analytics()
    elif data_type == 'business':
        data = analytics.get_business_analytics()
    elif data_type == 'restaurant':
        data = analytics.get_restaurant_analytics()
    elif data_type == 'customer':
        data = analytics.get_customer_analytics()
    elif data_type == 'health':
        data = analytics.get_system_health_analytics()
    else:
        data = analytics.get_comprehensive_dashboard()
    
    return JsonResponse({
        'success': True,
        'data': data,
        'timestamp': timezone.now().isoformat()
    })


@staff_member_required
def export_analytics_csv(request):
    """
    Export analytics data to CSV format.
    Supports different data types for targeted exports.
    """
    analytics = SystemAnalytics()
    data_type = request.GET.get('type', 'overview')
    
    response = HttpResponse(content_type='text/csv')
    filename = f'analytics_export_{data_type}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    if data_type == 'authentication':
        data = analytics.get_authentication_analytics()
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Users', data['total_users']])
        writer.writerow(['Active Users Today', data['active_users_today']])
        writer.writerow(['Active Users This Week', data['active_users_week']])
        writer.writerow(['Active Users This Month', data['active_users_month']])
        writer.writerow(['New Users Today', data['new_users_today']])
        writer.writerow(['New Users This Week', data['new_users_week']])
        writer.writerow(['New Users This Month', data['new_users_month']])
        
        # User roles
        writer.writerow([])
        writer.writerow(['User Role Distribution'])
        writer.writerow(['Role', 'Count'])
        for role in data['user_roles']:
            writer.writerow([role['role_name'], role['count']])
    
    elif data_type == 'business':
        data = analytics.get_business_analytics()
        writer.writerow(['Business Metric', 'Value'])
        writer.writerow(['Total Orders', data['total_orders']])
        writer.writerow(['Orders Today', data['orders_today']])
        writer.writerow(['Orders This Week', data['orders_week']])
        writer.writerow(['Orders This Month', data['orders_month']])
        writer.writerow(['Total Revenue', f"${data['total_revenue']:.2f}"])
        writer.writerow(['Revenue Today', f"${data['revenue_today']:.2f}"])
        writer.writerow(['Revenue This Week', f"${data['revenue_week']:.2f}"])
        writer.writerow(['Revenue This Month', f"${data['revenue_month']:.2f}"])
        writer.writerow(['Average Order Value', f"${data['avg_order_value']:.2f}"])
        
        # Top restaurants
        writer.writerow([])
        writer.writerow(['Top Performing Restaurants'])
        writer.writerow(['Restaurant', 'Orders', 'Revenue'])
        for restaurant in data['top_restaurants']:
            writer.writerow([restaurant['restaurant__name'], restaurant['orders'], f"${restaurant['revenue']:.2f}"])
    
    else:
        # Overview export
        data = analytics.get_comprehensive_dashboard()
        writer.writerow(['System Analytics Overview'])
        writer.writerow(['Generated:', data['generated_at']])
        writer.writerow([])
        
        # Authentication overview
        auth = data['authentication']
        writer.writerow(['Authentication Metrics'])
        writer.writerow(['Total Users', auth['total_users']])
        writer.writerow(['Active Users Today', auth['active_users_today']])
        writer.writerow(['New Users This Month', auth['new_users_month']])
        
        # Business overview
        business = data['business']
        writer.writerow([])
        writer.writerow(['Business Metrics'])
        writer.writerow(['Total Orders', business['total_orders']])
        writer.writerow(['Total Revenue', f"${business['total_revenue']:.2f}"])
        writer.writerow(['Orders This Month', business['orders_month']])
        
        # Restaurant overview
        restaurant = data['restaurant']
        writer.writerow([])
        writer.writerow(['Restaurant Metrics'])
        writer.writerow(['Total Restaurants', restaurant['total_restaurants']])
        writer.writerow(['Active Restaurants', restaurant['active_restaurants']])
        writer.writerow(['Total Menu Items', restaurant['total_menu_items']])
    
    return response


@staff_member_required
@cache_page(300)  # Cache for 5 minutes
def monitoring_dashboard(request):
    """
    Main monitoring dashboard with comprehensive website statistics.
    Displays aggregated data only - no sensitive user information exposed.
    """
    # Get date ranges for comparisons
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    last_year = today - timedelta(days=365)
    
    # User Statistics (Aggregated Only)
    total_users = User.objects.count()
    active_users_last_week = User.objects.filter(
        last_login__gte=last_week
    ).count()
    new_users_this_month = User.objects.filter(
        date_joined__gte=last_month
    ).count()
    
    # User role distribution (privacy-safe)
    user_roles = User.objects.annotate(
        role_name=Case(
            When(is_superuser=True, then=Value('Super Admin')),
            When(is_staff=True, then=Value('Staff')),
            When(groups__name='Restaurant Owner', then=Value('Restaurant Owner')),
            default=Value('Customer'),
            output_field=CharField(),
        )
    ).values('role_name').annotate(count=Count('id'))
    
    # Restaurant Statistics
    total_restaurants = Restaurant.objects.count()
    active_restaurants = Restaurant.objects.filter(is_active=True).count()
    pending_restaurants = Restaurant.objects.filter(is_approved=False, is_active=False).count()
    restaurants_by_cuisine = Restaurant.objects.values('cuisine_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Menu Statistics
    total_menu_items = MenuItem.objects.count()
    available_menu_items = MenuItem.objects.filter(is_available=True).count()
    menu_items_by_category = MenuItem.objects.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Order Statistics (Business Metrics)
    total_orders = Order.objects.count()
    orders_this_week = Order.objects.filter(created_at__gte=last_week).count()
    orders_this_month = Order.objects.filter(created_at__gte=last_month).count()
    
    # Revenue Statistics (Aggregated Only)
    total_revenue = Order.objects.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    revenue_this_month = Order.objects.filter(
        created_at__gte=last_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Average order value
    avg_order_value = Order.objects.aggregate(
        avg=Avg('total_amount')
    )['avg'] or 0
    
    # Review Statistics
    total_restaurant_reviews = RestaurantReview.objects.count()
    total_menu_item_reviews = MenuItemReview.objects.count()
    pending_reviews = RestaurantReview.objects.filter(
        is_flagged=True
    ).count() + MenuItemReview.objects.filter(is_flagged=True).count()
    
    # Average ratings (aggregated)
    avg_restaurant_rating = RestaurantReview.objects.aggregate(
        avg=Avg('rating')
    )['avg'] or 0
    avg_menu_item_rating = MenuItemReview.objects.aggregate(
        avg=Avg('rating')
    )['avg'] or 0
    
    # Wishlist Statistics
    total_wishlists = Wishlist.objects.count()
    popular_restaurants = Wishlist.objects.values('restaurant__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'title': 'Website Monitoring Dashboard',
        
        # User Metrics
        'total_users': total_users,
        'active_users_last_week': active_users_last_week,
        'new_users_this_month': new_users_this_month,
        'user_roles': list(user_roles),
        
        # Restaurant Metrics
        'total_restaurants': total_restaurants,
        'active_restaurants': active_restaurants,
        'pending_restaurants': pending_restaurants,
        'restaurants_by_cuisine': list(restaurants_by_cuisine),
        
        # Menu Metrics
        'total_menu_items': total_menu_items,
        'available_menu_items': available_menu_items,
        'menu_items_by_category': list(menu_items_by_category),
        
        # Order Metrics
        'total_orders': total_orders,
        'orders_this_week': orders_this_week,
        'orders_this_month': orders_this_month,
        
        # Revenue Metrics
        'total_revenue': total_revenue,
        'revenue_this_month': revenue_this_month,
        'avg_order_value': round(avg_order_value, 2),
        
        # Review Metrics
        'total_restaurant_reviews': total_restaurant_reviews,
        'total_menu_item_reviews': total_menu_item_reviews,
        'pending_reviews': pending_reviews,
        'avg_restaurant_rating': round(avg_restaurant_rating, 1),
        'avg_menu_item_rating': round(avg_menu_item_rating, 1),
        
        # Wishlist Metrics
        'total_wishlists': total_wishlists,
        'popular_restaurants': list(popular_restaurants),
        
        # System Health
        'server_time': timezone.now(),
        'database_status': 'Healthy',  # Could be enhanced with actual health checks
    }
    
    return render(request, 'admin/monitoring_dashboard.html', context)


@staff_member_required
@cache_page(600)  # Cache for 10 minutes
def analytics_trends(request):
    """
    Detailed analytics with trends and charts.
    Privacy-safe aggregated data over time periods.
    """
    # Get date range from request or default to last 30 days
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # User registration trends
    user_registrations = User.objects.filter(
        date_joined__gte=start_date
    ).annotate(
        date=TruncDate('date_joined')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Order trends
    order_trends = Order.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('date')
    
    # Review trends
    review_trends = RestaurantReview.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    context = {
        'title': 'Analytics Trends',
        'days': days,
        'user_registrations': json.dumps(list(user_registrations), default=str),
        'order_trends': json.dumps(list(order_trends), default=str),
        'review_trends': json.dumps(list(review_trends), default=str),
    }
    
    return render(request, 'admin/analytics_trends.html', context)


@staff_member_required
@cache_page(300)  # Cache for 5 minutes
def content_monitoring(request):
    """
    Content monitoring dashboard for reviews and user-generated content.
    Focuses on moderation needs and content quality metrics.
    """
    # Flagged content requiring attention
    flagged_restaurant_reviews = RestaurantReview.objects.filter(
        is_flagged=True
    ).select_related('restaurant', 'user').order_by('-created_at')
    
    flagged_menu_reviews = MenuItemReview.objects.filter(
        is_flagged=True
    ).select_related('menu_item', 'user').order_by('-created_at')
    
    # Recent reviews (last 24 hours)
    recent_reviews = RestaurantReview.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=1)
    ).count() + MenuItemReview.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=1)
    ).count()
    
    # Content quality metrics
    low_rated_reviews = RestaurantReview.objects.filter(
        rating__lte=2
    ).count() + MenuItemReview.objects.filter(rating__lte=2).count()
    
    high_rated_reviews = RestaurantReview.objects.filter(
        rating__gte=4
    ).count() + MenuItemReview.objects.filter(rating__gte=4).count()
    
    context = {
        'title': 'Content Monitoring',
        'flagged_restaurant_reviews': flagged_restaurant_reviews,
        'flagged_menu_reviews': flagged_menu_reviews,
        'recent_reviews': recent_reviews,
        'low_rated_reviews': low_rated_reviews,
        'high_rated_reviews': high_rated_reviews,
    }
    
    return render(request, 'admin/content_monitoring.html', context)


@staff_member_required
@cache_page(180)  # Cache for 3 minutes
def system_health(request):
    """
    System health monitoring dashboard.
    Shows database stats, server performance, and system metrics.
    """
    # Database statistics
    db_stats = {
        'users': User.objects.count(),
        'restaurants': Restaurant.objects.count(),
        'menu_items': MenuItem.objects.count(),
        'orders': Order.objects.count(),
        'reviews': RestaurantReview.objects.count() + MenuItemReview.objects.count(),
    }
    
    # Recent activity (last hour)
    one_hour_ago = timezone.now() - timedelta(hours=1)
    recent_activity = {
        'new_users': User.objects.filter(date_joined__gte=one_hour_ago).count(),
        'new_orders': Order.objects.filter(created_at__gte=one_hour_ago).count(),
        'new_reviews': RestaurantReview.objects.filter(
            created_at__gte=one_hour_ago
        ).count() + MenuItemReview.objects.filter(
            created_at__gte=one_hour_ago
        ).count(),
    }
    
    context = {
        'title': 'System Health',
        'db_stats': db_stats,
        'recent_activity': recent_activity,
        'server_time': timezone.now(),
        'uptime': 'N/A',  # Could be enhanced with actual uptime tracking
    }
    
    return render(request, 'admin/system_health.html', context)


@staff_member_required
@cache_page(60)  # Cache for 1 minute
def api_stats(request):
    """
    API endpoint for real-time statistics (AJAX updates).
    Returns JSON data for dashboard widgets.
    """
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    stats = {
        'current_users': User.objects.filter(
            last_login__gte=one_hour_ago
        ).count(),
        'active_orders': Order.objects.filter(
            status__in=['pending', 'processing']
        ).count(),
        'pending_reviews': RestaurantReview.objects.filter(
            is_flagged=True
        ).count() + MenuItemReview.objects.filter(is_flagged=True).count(),
        'server_time': timezone.now().isoformat(),
    }
    
    return JsonResponse(stats)
