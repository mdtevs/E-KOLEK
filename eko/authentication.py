"""
Custom authentication classes for Django REST Framework
Provides CSRF-exempt session authentication for mixed JWT/Session environments
"""
from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication without CSRF check.
    
    This is used for API endpoints that support both JWT and Session authentication.
    JWT requests don't need CSRF protection since they use token-based auth.
    Session-based requests from the web app will be handled by Django's middleware.
    
    This prevents CSRF errors when mobile apps use session cookies unintentionally.
    """
    
    def enforce_csrf(self, request):
        """
        Override to skip CSRF check.
        Django's CsrfViewMiddleware will still protect session-based endpoints
        when accessed from browsers with the @csrf_protect decorator.
        """
        return  # Skip CSRF validation
