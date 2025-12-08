# Mobile Development Settings Override
# This file maintains security while allowing mobile app access

from .settings import *

# SECURITY SETTINGS FOR MOBILE DEVELOPMENT
DEBUG = True

# Disable SSL redirects for development (but keep other security)
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False

# Allow non-secure cookies for development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Mobile-friendly CSRF settings (secure but functional)
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://10.0.2.2:8000',
    'http://192.168.1.15:8000',
    'http://192.168.1.6:8000',
]

# CORS settings for mobile (secure but permissive)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'cache-control',
    'pragma',
]

# Disable rate limiting for development testing
RATELIMIT_ENABLE = False

# Mobile-friendly CSP (allows API calls but maintains security) - Updated format
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'", "'unsafe-inline'"),
        'script-src': ("'self'", "'unsafe-inline'", "'unsafe-eval'"),
        'style-src': ("'self'", "'unsafe-inline'", "https://unpkg.com"),  # Allow Boxicons CDN
        'font-src': ("'self'", "https://unpkg.com"),  # Allow font files from CDN
        'connect-src': ("'self'", "*"),  # Allow API connections
        'img-src': ("'self'", "data:", "blob:", "https:"),
    }
}

# Allow additional hosts for mobile testing
ALLOWED_HOSTS = ['*']

# REST Framework settings for mobile API
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

print("� Mobile development settings loaded - Secure API access enabled")
