"""
Utility functions for admin management
"""
import secrets
import string
import logging

logger = logging.getLogger(__name__)

def generate_secure_password(length=12, include_symbols=True):
    """
    Generate a secure random password
    
    Args:
        length (int): Length of the password (default: 12)
        include_symbols (bool): Whether to include special characters (default: True)
    
    Returns:
        str: Secure random password
    """
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?' if include_symbols else ''
    
    # Ensure at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits)
    ]
    
    if include_symbols:
        password.append(secrets.choice(symbols))
    
    # Fill the rest of the password length
    all_chars = lowercase + uppercase + digits + symbols
    for _ in range(length - len(password)):
        password.append(secrets.choice(all_chars))
    
    # Shuffle the password list to avoid predictable patterns
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip

def log_admin_action(admin_user, target_admin, action, details="", request=None):
    """
    Log administrative actions for audit trail using the AdminActionHistory model
    
    Args:
        admin_user: The admin performing the action
        target_admin: The admin being acted upon (can be None)
        action (str): The action being performed
        details (str): Additional details about the action
        request: The HTTP request object (optional, for IP/user agent tracking)
    """
    from cenro.models import AdminActionHistory
    
    # Basic log message
    log_message = f"Admin Action: {admin_user.username} performed '{action}'"
    if target_admin:
        log_message += f" on {target_admin.username}"
    if details:
        log_message += f" - Details: {details}"
    
    logger.info(log_message)
    
    # Create database record if we have enough information
    try:
        history_data = {
            'admin_user': admin_user,
            'target_admin': target_admin,
            'action': action,
            'description': log_message,
            'details': {'details': details} if details else {}
        }
        
        # Add request context if available
        if request:
            history_data.update({
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')[:500],  # Truncate long user agents
                'session_key': request.session.session_key
            })
        else:
            # Default values when no request available
            history_data.update({
                'ip_address': '127.0.0.1',
                'user_agent': 'System Action'
            })
        
        AdminActionHistory.objects.create(**history_data)
        
    except Exception as e:
        logger.error(f"Failed to create admin action history record: {str(e)}")

def validate_password_strength(password):
    """
    Validate password strength
    
    Args:
        password (str): Password to validate
    
    Returns:
        dict: Validation result with 'is_valid' bool and 'errors' list
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        errors.append("Password should contain at least one special character")
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors
    }