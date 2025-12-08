"""
Security utility functions for the EKO project
Provides input validation and SQL injection prevention
"""

import re
import html
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.db import models
import uuid


def validate_user_input(input_string, max_length=255, allow_special_chars=False):
    """
    Validates and sanitizes user input to prevent XSS and injection attacks
    """
    if not input_string:
        return input_string
    
    # Strip HTML tags
    clean_input = strip_tags(input_string)
    
    # HTML escape
    clean_input = html.escape(clean_input)
    
    # Remove potentially dangerous characters if not allowed
    if not allow_special_chars:
        # Allow only alphanumeric, spaces, and common punctuation
        clean_input = re.sub(r'[^\w\s\-\.,!?@]', '', clean_input)
    
    # Truncate to max length
    if len(clean_input) > max_length:
        clean_input = clean_input[:max_length]
    
    return clean_input.strip()


def validate_uuid(uuid_string):
    """
    Validates that a string is a proper UUID
    """
    try:
        uuid_obj = uuid.UUID(uuid_string)
        return str(uuid_obj)
    except (ValueError, TypeError):
        raise ValidationError("Invalid UUID format")


def validate_phone_number(phone):
    """
    Validates phone number format
    """
    if not phone:
        return phone
    
    # Remove all non-digits
    clean_phone = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (10-15 digits)
    if not (10 <= len(clean_phone) <= 15):
        raise ValidationError("Phone number must be 10-15 digits")
    
    return clean_phone


def validate_email(email):
    """
    Basic email validation (Django has better built-in validators)
    """
    if not email:
        return email
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format")
    
    return email.lower().strip()


def sanitize_query_params(params_dict):
    """
    Sanitizes all parameters in a dictionary (like request.GET or request.POST)
    """
    sanitized = {}
    for key, value in params_dict.items():
        if isinstance(value, str):
            sanitized[key] = validate_user_input(value)
        elif isinstance(value, list):
            sanitized[key] = [validate_user_input(v) if isinstance(v, str) else v for v in value]
        else:
            sanitized[key] = value
    return sanitized


def safe_get_object_or_404(model_class, **kwargs):
    """
    Safe version of get_object_or_404 that validates UUID fields
    """
    # Validate UUID fields
    for field_name, value in kwargs.items():
        field = model_class._meta.get_field(field_name)
        if isinstance(field, models.UUIDField) and value:
            kwargs[field_name] = validate_uuid(value)
    
    from django.shortcuts import get_object_or_404
    return get_object_or_404(model_class, **kwargs)


def validate_points_amount(points):
    """
    Validates points amount to prevent negative or excessive values
    """
    try:
        points_float = float(points)
        if points_float < 0:
            raise ValidationError("Points cannot be negative")
        if points_float > 1000000:  # Reasonable upper limit
            raise ValidationError("Points amount too large")
        return points_float
    except (ValueError, TypeError):
        raise ValidationError("Invalid points amount")


def validate_weight(weight):
    """
    Validates weight values for waste transactions
    """
    try:
        weight_float = float(weight)
        if weight_float < 0:
            raise ValidationError("Weight cannot be negative")
        if weight_float > 10000:  # Reasonable upper limit (10 tons)
            raise ValidationError("Weight amount too large")
        return weight_float
    except (ValueError, TypeError):
        raise ValidationError("Invalid weight amount")


def log_security_event(event_type, user=None, ip_address=None, details=None):
    """
    Logs security-related events for monitoring
    """
    import logging
    logger = logging.getLogger('django.security')
    
    message = f"SECURITY_EVENT: {event_type}"
    if user:
        message += f" | User: {user.username if hasattr(user, 'username') else str(user)}"
    if ip_address:
        message += f" | IP: {ip_address}"
    if details:
        message += f" | Details: {details}"
    
    logger.warning(message)


def get_client_ip(request):
    """
    Get the real client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def check_rate_limit(request, group, key, rate):
    """
    Check if request exceeds rate limit
    """
    from django_ratelimit.decorators import ratelimit
    from django_ratelimit import is_ratelimited
    
    return is_ratelimited(request, group=group, key=key, rate=rate, increment=True)
