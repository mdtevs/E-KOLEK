"""
Utility functions for masking sensitive user data (emails, phone numbers)
These functions are used to protect user privacy when displaying contact information
"""


def mask_email(email):
    """
    Mask email address to show only first 2-3 characters and domain.
    
    Examples:
        Input: "acerorenz3000@gmail.com"
        Output: "ac***@gmail.com"
        
        Input: "john@example.org"
        Output: "jo***@example.org"
        
        Input: "a@test.com"
        Output: "a***@test.com"
    
    Args:
        email: String email address to mask
        
    Returns:
        Masked email address string with asterisks
    """
    if not email:
        return ""
    
    # Convert to string and remove any whitespace
    email_str = str(email).strip()
    
    # Check if valid email format (contains @)
    if '@' not in email_str:
        return email_str
    
    # Split email into username and domain
    parts = email_str.split('@')
    if len(parts) != 2:
        return email_str
    
    username = parts[0]
    domain = parts[1]
    
    # Mask username part
    if len(username) <= 1:
        # Very short username, show first char
        masked_username = username[0] + '***' if username else '***'
    elif len(username) <= 3:
        # Short username (2-3 chars), show first 2 chars
        masked_username = username[:2] + '***'
    else:
        # Longer username, show first 2-3 chars based on length
        visible_chars = 2 if len(username) <= 6 else 3
        masked_username = username[:visible_chars] + '***'
    
    return f"{masked_username}@{domain}"


def mask_phone(phone_number):
    """
    Mask phone number to show only last 3-4 digits.
    
    Examples:
        Input: "09056352991"
        Output: "********991"
        
        Input: "9056352991"
        Output: "*******991"
        
        Input: "+639056352991"
        Output: "**********991"
    
    Args:
        phone_number: String phone number to mask
        
    Returns:
        Masked phone number string with asterisks
    """
    if not phone_number:
        return ""
    
    # Convert to string and remove any whitespace
    phone_str = str(phone_number).strip()
    
    # If phone number is too short (less than 4 digits), mask all but last digit
    if len(phone_str) < 4:
        return '*' * (len(phone_str) - 1) + phone_str[-1] if len(phone_str) > 0 else ""
    
    # Mask all digits except last 3
    masked_part = '*' * (len(phone_str) - 3)
    visible_part = phone_str[-3:]
    
    return masked_part + visible_part


def mask_contact(contact, method):
    """
    Unified function to mask contact information (phone or email).
    
    This is a convenience function that routes to the appropriate masking function
    based on the contact method type.
    
    Args:
        contact: String contact information (phone number or email)
        method: String indicating contact type ('email', 'sms', or 'phone')
        
    Returns:
        Masked contact string
    """
    if method == 'email':
        return mask_email(contact)
    else:
        # For 'sms', 'phone', or any other method, assume phone number
        return mask_phone(contact)
