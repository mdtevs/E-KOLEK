"""
Admin Security Middleware for enhanced security features
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from cenro.models import AdminUser
import logging

logger = logging.getLogger(__name__)

class AdminPasswordResetMiddleware:
    """
    Middleware to handle admin password reset security
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if admin needs to change password
        if hasattr(request, 'admin_user') and request.admin_user:
            if request.admin_user.must_change_password:
                # Allow access to change password page and logout
                allowed_paths = [
                    '/cenro/admin/change-password/',
                    '/cenro/admin/logout/',
                    '/logout/',
                ]
                
                if not any(request.path.startswith(path) for path in allowed_paths):
                    messages.warning(request, 'You must change your password before proceeding.')
                    return redirect('cenro:admin_change_password')
        
        response = self.get_response(request)
        return response

class AdminSecurityLogMiddleware:
    """
    Middleware to log security-related admin actions
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log sensitive admin actions
        if hasattr(request, 'admin_user') and request.admin_user and request.method == 'POST':
            sensitive_actions = [
                'reset_password',
                'suspend',
                'reject',
                'lock',
                'unlock',
                'reactivate',
                'create',
                'delete'
            ]
            
            action = request.POST.get('action', '')
            if action in sensitive_actions:
                client_ip = self.get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
                
                logger.info(
                    f"Admin Security Action: {request.admin_user.username} "
                    f"performed '{action}' from IP {client_ip} "
                    f"using {user_agent[:100]}"
                )
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
