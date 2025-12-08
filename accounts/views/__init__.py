"""
Accounts views package - Organized view modules
All views are exported here for backward compatibility
"""

# Authentication views
from .auth_views import (
    safe_user_logout,
    login_page,
    logout_view,
    code_login,
    qr_login,
)

# Registration views
from .registration_views import (
    register,
    register_family,
    register_member,
)

# OTP verification views
from .otp_views import (
    send_otp_view,
    resend_otp_view,
    verify_otp_view,
    send_email_otp_view,
    resend_email_otp_view,
    verify_email_otp_view,
)

# Password reset views
from .password_views import (
    forgot_password,
    forgot_password_verify,
    forgot_password_resend,
    reset_password,
    mask_contact,
)

# Dashboard and notification views
from .dashboard_views import (
    home,
    userdashboard,
    mark_notifications_viewed,
    get_unread_count,
    privacy_policy,
    terms_of_service,
)

# Validation API views
from .validation_views import (
    check_phone_availability,
    check_email_availability,
    get_active_terms,
)

__all__ = [
    # Authentication
    'safe_user_logout',
    'login_page',
    'logout_view',
    'code_login',
    'qr_login',
    
    # Registration
    'register',
    'register_family',
    'register_member',
    
    # OTP
    'send_otp_view',
    'resend_otp_view',
    'verify_otp_view',
    'send_email_otp_view',
    'resend_email_otp_view',
    'verify_email_otp_view',
    
    # Password Reset
    'forgot_password',
    'forgot_password_verify',
    'forgot_password_resend',
    'reset_password',
    'mask_contact',
    
    # Dashboard
    'home',
    'userdashboard',
    'mark_notifications_viewed',
    'get_unread_count',
    'privacy_policy',
    'terms_of_service',
    
    # Validation
    'check_phone_availability',
    'check_email_availability',
    'get_active_terms',
]
