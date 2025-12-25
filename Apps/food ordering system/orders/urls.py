"""
Orders app URL configuration.
Handles promo code management and order-related URLs.
"""
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Promo Code Management
    path('promo-codes/', views.promo_code_list, name='promo_code_list'),
    path('promo-codes/create/', views.create_promo_code, name='create_promo_code'),
    path('promo-codes/<uuid:promo_code_id>/edit/', views.edit_promo_code, name='edit_promo_code'),
    path('promo-codes/<uuid:promo_code_id>/delete/', views.delete_promo_code, name='delete_promo_code'),
    
    # Promo Code Application (AJAX)
    path('apply-promo-code/', views.apply_promo_code, name='apply_promo_code'),
    path('remove-promo-code/', views.remove_promo_code, name='remove_promo_code'),
    
    # Seasonal Promotions (Admin Only)
    path('seasonal-promotions/', views.seasonal_promotion_list, name='seasonal_promotion_list'),
    path('seasonal-promotions/create/', views.create_seasonal_promotion, name='create_seasonal_promotion'),
]
