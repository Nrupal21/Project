"""
Orders app admin configuration.
Customizes Django admin interface for Order and OrderItem models.
"""
from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """
    Inline admin for OrderItem model.
    Displays order items within the order admin page.
    """
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']
    fields = ['menu_item', 'quantity', 'price', 'subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin interface for Order model.
    Provides comprehensive order management with inline items display.
    """
    list_display = [
        'order_id',
        'customer_name',
        'customer_phone',
        'total_amount',
        'status',
        'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['order_id', 'customer_name', 'customer_phone']
    readonly_fields = ['order_id', 'created_at', 'updated_at']
    list_editable = ['status']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'status', 'total_amount')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_phone', 'customer_address')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Admin interface for OrderItem model.
    Provides management of individual order items.
    """
    list_display = ['order', 'menu_item', 'quantity', 'price', 'subtotal']
    list_filter = ['order__status', 'created_at']
    search_fields = ['order__order_id', 'menu_item__name']
    readonly_fields = ['subtotal', 'created_at', 'updated_at']
