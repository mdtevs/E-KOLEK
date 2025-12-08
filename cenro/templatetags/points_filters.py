"""
Custom template filters for formatting points values.
Whole numbers display without decimals (e.g., 3.00 → 3)
Decimal values display with precision (e.g., 3.50 → 3.5, 3.75 → 3.75)
"""
from django import template
from decimal import Decimal

register = template.Library()


@register.filter(name='smart_points')
def smart_points(value):
    """
    Format points to show decimals only when necessary.
    Examples:
        3.00 → 3
        5.50 → 5.5
        10.75 → 10.75
        0 → 0
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
