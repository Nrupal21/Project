"""
Customer app URL configuration.
Maps URLs to customer-facing views including profile and restaurant upgrade.
"""
from django.urls import path
from . import views

app_name = 'customer'

# URL patterns for customer-facing pages
urlpatterns = [
    # Home page - displays restaurants
    path('', views.home, name='home'),
    
    # Filter results page - dedicated page for filtered restaurants
    path('restaurants/', views.filter_results, name='filter_results'),
    
    # User profile and restaurant upgrade
    path('profile/', views.user_profile, name='profile'),
    path('restaurant-upgrade/', views.restaurant_upgrade, name='restaurant_upgrade'),
    
    # Restaurant detail page - displays menu for specific restaurant
    path('restaurant/<int:restaurant_id>/', views.restaurant_detail, name='restaurant_detail'),
    
    # Menu page - displays all menu items
    path('menu/', views.menu, name='menu'),
    
    # Cart operations - requires login
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:menu_item_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:menu_item_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:menu_item_id>/', views.cart_update, name='cart_update'),
    path('cart/apply-promo/', views.apply_promo_code, name='apply_promo_code'),
    path('cart/remove-promo/', views.cart_remove_promo, name='cart_remove_promo'),
    
    # Checkout and order confirmation - requires login
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<uuid:order_id>/', views.order_success, name='order_success'),
    
    # Payment processing - DISABLED
    # path('payment/<uuid:order_id>/', views.process_payment, name='process_payment'),
    # path('payment/verify/', views.verify_payment, name='verify_payment'),
    
    # Order history - requires login
    path('order-history/', views.order_history, name='order_history'),
    
    # Order tracking - requires login
    path('track-order/<uuid:order_id>/', views.order_tracking, name='order_tracking'),
    
    # ==================== REVIEW SYSTEM ====================
    # Review creation and management - requires login
    path('reviews/restaurant/<uuid:order_id>/', views.create_restaurant_review, name='create_restaurant_review'),
    path('reviews/restaurant/edit/<int:review_id>/', views.edit_restaurant_review, name='edit_restaurant_review'),
    path('reviews/menu-item/<uuid:order_id>/<int:menu_item_id>/', views.create_menu_item_review, name='create_menu_item_review'),
    path('reviews/menu-item/edit/<int:review_id>/', views.edit_menu_item_review, name='edit_menu_item_review'),
    
    # Review display and interaction
    path('reviews/<str:review_type>/<int:review_id>/', views.review_detail, name='review_detail'),
    path('reviews/flag/<str:review_type>/<int:review_id>/', views.flag_review, name='flag_review'),
    path('reviews/respond/<str:review_type>/<int:review_id>/', views.create_review_response, name='create_review_response'),
    path('reviews/delete/<str:review_type>/<int:review_id>/', views.delete_review, name='delete_review'),
    
    # User review history - requires login
    path('my-reviews/', views.my_reviews, name='my_reviews'),
    
    # Wishlist - requires login
    path('wishlist/toggle/<int:restaurant_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('my-wishlist/', views.my_wishlist, name='my_wishlist'),
    
    # Table QR Code Menu - no login required
    path('table/<uuid:uuid>/', views.table_menu, name='table_menu'),
    
    # Guest Checkout for QR Table Ordering - no login required
    path('table/<uuid:uuid>/checkout/', views.guest_checkout, name='guest_checkout'),
    path('table/<uuid:uuid>/success/<uuid:order_id>/', views.guest_order_success, name='guest_order_success'),
]
