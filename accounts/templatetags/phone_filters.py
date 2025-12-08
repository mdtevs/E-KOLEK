"""
Custom template filters for phone number formatting, masking, email masking, and points display.
These filters wrap the utility functions from masking_utils for use in Django templates.
"""
from django import template
from decimal import Decimal
from accounts.masking_utils import mask_phone as _mask_phone, mask_email as _mask_email

register = template.Library()


@register.filter(name='mask_phone')
def mask_phone(phone_number):
    """
    Template filter to mask phone number.
    Wraps the utility function from masking_utils.
    
    Example:
        Input: "09056352991"
        Output: "********991"
        
    Usage in template:
        {{ user.phone|mask_phone }}
    """
    return _mask_phone(phone_number)


@register.filter(name='mask_email')
def mask_email(email):
    """
    Template filter to mask email address.
    Wraps the utility function from masking_utils.
    
    Example:
        Input: "acerorenz3000@gmail.com"
        Output: "ac***@gmail.com"
        
    Usage in template:
        {{ user.email|mask_email }}
    """
    return _mask_email(email)


@register.filter(name='smart_points')
def smart_points(value):
    """
    Format points to show decimals only when necessary.
    
    Examples:
        3.00 → 3
        5.50 → 5.5
        10.75 → 10.75
        0 → 0
    
    Args:
        value: Numeric value (int, float, Decimal, or string)
        
    Returns:
        Formatted string representation of the points value
    """
    if value is None:
        return '0'
    
    try:
        # Convert to Decimal for precision
        decimal_value = Decimal(str(value))
        
        # Check if it's a whole number
        if decimal_value == decimal_value.to_integral_value():
            return str(int(decimal_value))
        
        # Remove trailing zeros after decimal point
        normalized = decimal_value.normalize()
        return str(normalized)
    except (ValueError, TypeError, ArithmeticError):
        return str(value)
