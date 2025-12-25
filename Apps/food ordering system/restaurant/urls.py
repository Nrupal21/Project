"""
Restaurant app URL configuration.
Maps URLs to restaurant dashboard views and registration wizard.
"""
from django.urls import path
from . import views
from .registration_wizard import (
    RestaurantRegistrationWizardView,
    RegistrationSuccessView
)
from .approval_views import (
    ApprovalDashboardView,
    PendingRestaurantsListView,
    RestaurantReviewView,
    BulkApprovalView,
    ApprovalAnalyticsView,
)

app_name = 'restaurant'

# URL patterns for restaurant dashboard
urlpatterns = [
    # Registration Wizard (NEW)
    path('register/wizard/', RestaurantRegistrationWizardView.as_view(), name='registration_wizard'),
    path('register/success/', RegistrationSuccessView.as_view(), name='registration_success'),
    
    # Approval Management (NEW - Manager/Admin only)
    path('approvals/dashboard/', ApprovalDashboardView.as_view(), name='approval_dashboard'),
    path('approvals/pending/', PendingRestaurantsListView.as_view(), name='pending_list'),
    path('approvals/review/<int:pk>/', RestaurantReviewView.as_view(), name='review_detail'),
    path('approvals/bulk/', BulkApprovalView.as_view(), name='bulk_approval'),
    path('approvals/analytics/', ApprovalAnalyticsView.as_view(), name='approval_analytics'),
    
    # Authentication
    path('login/', views.restaurant_login, name='login'),
    path('logout/', views.restaurant_logout, name='logout'),
    
    # Restaurant Selection (for multi-restaurant owners)
    path('select/', views.select_restaurant, name='select_restaurant'),
    path('set/<int:restaurant_id>/', views.set_restaurant, name='set_restaurant'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('operations/', views.operations_hub, name='operations_hub'),  # Unified Operations Hub
    
    # Marketing Campaigns
    path('campaigns/', views.campaign_list, name='campaign_list'),
    path('campaigns/create/', views.campaign_create, name='campaign_create'),
    path('campaigns/<int:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('campaigns/<int:campaign_id>/edit/', views.campaign_update, name='campaign_update'),
    path('campaigns/<int:campaign_id>/delete/', views.campaign_delete, name='campaign_delete'),
    path('campaigns/<int:campaign_id>/preview/', views.campaign_preview, name='campaign_preview'),
    path('campaigns/<int:campaign_id>/send/', views.campaign_send, name='campaign_send'),
    
    # Menu Management
    path('menu/', views.menu_management, name='menu_management'),
    path('menu/add/', views.add_menu_item, name='add_menu_item'),
    path('menu/edit/<int:menu_item_id>/', views.edit_menu_item, name='edit_menu_item'),
    path('menu/delete/<int:menu_item_id>/', views.delete_menu_item, name='delete_menu_item'),
    path('menu/toggle/<int:menu_item_id>/', views.toggle_menu_item_availability, name='toggle_menu_item_availability'),
    path('menu/bulk-update/', views.bulk_update_availability, name='bulk_update_availability'),
    
    # Table Management (QR Code Menu System)
    path('tables/', views.table_management, name='table_management'),
    path('tables/add/', views.add_table, name='add_table'),
    path('tables/edit/<int:table_id>/', views.edit_table, name='edit_table'),
    path('tables/delete/<int:table_id>/', views.delete_table, name='delete_table'),
    path('tables/toggle/<int:table_id>/', views.toggle_table_status, name='toggle_table_status'),
    path('tables/download-qr/<int:table_id>/', views.download_table_qr, name='download_table_qr'),
    path('tables/regenerate-qr/<int:table_id>/', views.regenerate_table_qr, name='regenerate_table_qr'),
    path('tables/generate-missing-qr/', views.generate_missing_qr_codes, name='generate_missing_qr_codes'),
    
    # QR Code Ordering System - Table Orders & Staff Order Management
    path('table-orders/', views.table_orders_list, name='table_orders_list'),
    path('active-tables/', views.active_tables_view, name='active_tables'),
    path('table-layout/', views.table_layout_view, name='table_layout'),
    path('select-table/', views.table_selection_view, name='table_selection'),
    path('table-order/<int:table_id>/', views.create_table_order, name='create_table_order'),
    path('orders/<uuid:order_id>/add-items/', views.add_items_to_order, name='add_items_to_order'),
    path('orders/<uuid:order_id>/kitchen-receipt/', views.print_kitchen_receipt, name='print_kitchen_receipt'),
    path('orders/<uuid:order_id>/final-bill/', views.print_final_bill, name='print_final_bill'),
    path('orders/<uuid:order_id>/mark-complete/', views.mark_order_complete, name='mark_order_complete'),
    
    # API Endpoints for Real-time Updates
    path('api/table-status/', views.get_table_status_api, name='table_status_api'),
    path('api/tables/status/', views.table_status_ajax, name='table_status_ajax'),
    path('api/tables/floor-plan/', views.floor_plan_ajax, name='floor_plan_ajax'),
    
    # Category Management
    path('categories/', views.category_management, name='category_management'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    
    # Order management
    path('orders/', views.order_list, name='order_list'),
    path('orders/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<uuid:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    
    # Manager Approval System
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/pending/<int:pending_id>/', views.pending_restaurant_detail, name='pending_restaurant_detail'),
    path('manager/approve/<int:pending_id>/', views.approve_restaurant, name='approve_restaurant'),
    path('manager/reject/<int:pending_id>/', views.reject_restaurant, name='reject_restaurant'),
    path('manager/restaurants/', views.manager_restaurants_list, name='manager_restaurants_list'),
    path('manager/toggle-status/<int:restaurant_id>/', views.toggle_restaurant_status, name='toggle_restaurant_status'),
    
    # Search API
    path('manager/search-users/', views.search_users, name='search_users'),
]
