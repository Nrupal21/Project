"""
Customer app context processors.
Provides cart count and cart total to all templates.
"""
from .cart import Cart


def cart_count(request):
    """
    Context processor to make cart count and cart total available in all templates.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        dict: Dictionary with cart_count and cart_total keys
    """
    cart = Cart(request)
    cart_total = cart.get_cart_total() if len(cart) > 0 else 0
    return {
        'cart_count': len(cart),
        'cart_total': cart_total
    }
