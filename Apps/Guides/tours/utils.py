"""
Utility functions for the tours application.
"""
from decimal import Decimal

def format_currency(amount):
    """
    Format a number as Indian Rupees (INR).
    
    Args:
        amount (Decimal, int, float): The amount to format
        
    Returns:
        str: Formatted currency string with Indian Rupee symbol
        
    Example:
        >>> format_currency(1000)
        '₹1,000.00'
        >>> format_currency(1000000)
        '₹10,00,000.00'
    """
    if amount is None:
        return "₹0.00"
        
    # Convert to Decimal if it's not already
    if not isinstance(amount, Decimal):
        try:
            amount = Decimal(str(amount))
        except (TypeError, ValueError):
            return "₹0.00"
    
    # Format with Indian numbering system (lakhs and crores)
    formatted = "₹{:,.2f}".format(amount)
    
    # Adjust for Indian numbering system (1,00,000 format)
    parts = formatted.split(".")
    integer_part = parts[0][1:]  # Remove the ₹ symbol
    
    # Format integer part with Indian numbering system
    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        other = integer_part[:-3]
        if len(other) > 2:
            other = ",".join([other[:-2], other[-2:]])
        formatted = f"₹{other},{last_three}"
    else:
        formatted = f"₹{integer_part}"
    
    # Add decimal part if it exists
    if len(parts) > 1:
        formatted += f".{parts[1]}"
    
    return formatted
