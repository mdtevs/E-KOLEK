"""
Django settings for E-KOLEK project.

Production-ready configuration with environment-based settings.
All sensitive data is stored in environment variables (.env file).

For more information:
https://docs.djangoproject.com/en/5.2/topics/settings/
"""

from pathlib import Path
import os
from decouple import config
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================================================================
# CORE SETTINGS
# ==============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)

# Allowed hosts configuration
# Support Railway deployment + Flutter mobile app
RAILWAY_STATIC_URL = config('RAILWAY_STATIC_URL', default='')
RAILWAY_PUBLIC_DOMAIN = config('RAILWAY_PUBLIC_DOMAIN', default='')

if DEBUG:
    ALLOWED_HOSTS = ['*']  # Allow all hosts in debug mode for development
else:
    # Production: Railway + custom domains
    allowed_hosts = config('ALLOWED_HOSTS', default='').split(',')
    
    # Add Railway domains if present
    if RAILWAY_PUBLIC_DOMAIN:
        allowed_hosts.append(RAILWAY_PUBLIC_DOMAIN)
    
    # Add common Railway patterns
    allowed_hosts.extend([
        '*.railway.app',
        '*.railway.internal',
        'e-kolek-production.up.railway.app',
    ])
    
    # Remove empty strings and deduplicate
    ALLOWED_HOSTS = list(set(filter(None, allowed_hosts)))

# Site URL configuration
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Custom user model
AUTH_USER_MODEL = 'accounts.Users'


# ==============================================================================
# APPLICATION DEFINITION
# ==============================================================================

INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # E-KOLEK apps
    'accounts.apps.AccountsConfig',
    'cenro',
    'game',
    'learn',
    'mobilelogin',
    'ekoscan',
    
    # Third-party apps
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'csp',  # Content Security Policy
    
    # Celery apps
    'django_celery_results',
    'django_celery_beat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Added for Railway static files
    'eko.security_middleware.SecurityHeadersMiddleware',
    'eko.security_middleware.BruteForceProtectionMiddleware',
    'eko.security_middleware.SQLInjectionDetectionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'eko.security_middleware.AdminAccessControlMiddleware',
    'accounts.middleware.AdminContextMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'eko.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cenro.context_processors.admin_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'eko.wsgi.application'


# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================

# Support both Railway DATABASE_URL and individual settings
import dj_database_url
import os

# Try to use DATABASE_URL first (Railway), fall back to individual settings
database_url = os.environ.get('DATABASE_URL') or config('DATABASE_URL', default='')

if database_url:
    # Railway provides DATABASE_URL
    DATABASES = {
        'default': dj_database_url.parse(
            database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Local development uses individual settings
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='ekolek_cenro'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432', cast=int),
            'CONN_MAX_AGE': 600,  # Connection pooling
            'OPTIONS': {
                'connect_timeout': 10,
            },
        }
    }


# ==============================================================================
# AUTHENTICATION & AUTHORIZATION
# ==============================================================================

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Authentication URLs
LOGIN_URL = '/login/'
ADMIN_LOGIN_URL = '/cenro/admin/login/'
LOGIN_REDIRECT_URL = '/userdashboard/'
LOGOUT_REDIRECT_URL = '/login/'


# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True


# ==============================================================================
# STATIC & MEDIA FILES
# ==============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = []

# WhiteNoise configuration for production static file serving
# Use CompressedStaticFilesStorage instead of Manifest to avoid missing files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Google Drive Storage Configuration
USE_GOOGLE_DRIVE = config('USE_GOOGLE_DRIVE', default=False, cast=bool)

if USE_GOOGLE_DRIVE:
    # OAuth credentials (PREFERRED - more reliable than service accounts)
    GOOGLE_DRIVE_OAUTH_REFRESH_TOKEN = config('GOOGLE_DRIVE_OAUTH_REFRESH_TOKEN', default=None)
    GOOGLE_DRIVE_OAUTH_CLIENT_ID = config('GOOGLE_DRIVE_OAUTH_CLIENT_ID', default=None)
    GOOGLE_DRIVE_OAUTH_CLIENT_SECRET = config('GOOGLE_DRIVE_OAUTH_CLIENT_SECRET', default=None)
    
    # Service account credentials (fallback)
    GOOGLE_DRIVE_CREDENTIALS_JSON = config('GOOGLE_DRIVE_CREDENTIALS_JSON', default=None)
    
    # Folder where files will be uploaded
    GOOGLE_DRIVE_FOLDER_ID = config('GOOGLE_DRIVE_FOLDER_ID')
    
    STORAGES = {
        "default": {
            "BACKEND": "eko.google_drive_storage.GoogleDriveStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==============================================================================
# EMAIL CONFIGURATION  
# ==============================================================================

# SendGrid HTTP API Configuration (Railway Compatible!)
# Railway blocks SMTP ports, so we use SendGrid's HTTP API instead
EMAIL_BACKEND = config('EMAIL_BACKEND', default='accounts.sendgrid_backend.SendGridBackend')

# SendGrid API Key (uses HTTP API, not SMTP)
SENDGRID_API_KEY = config('SENDGRID_API_KEY', default=config('EMAIL_HOST_PASSWORD', default=''))
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='ekolekcenro@gmail.com')

# Legacy SMTP settings (kept for reference, but not used with HTTP API backend)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='apikey')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=30, cast=int)


# ==============================================================================
# SMS & OTP CONFIGURATION
# ==============================================================================

# SMS API Settings (iProg Tech)
SMS_ENABLED = config('SMS_ENABLED', default=True, cast=bool)
SMS_API_URL = config('SMS_API_URL', default='https://www.iprogsms.com/api/v1/sms_messages')
SMS_API_TOKEN = config('SMS_API_TOKEN')
SMS_API_TIMEOUT = config('SMS_API_TIMEOUT', default=10, cast=int)
SMS_PROVIDER = config('SMS_PROVIDER', default=2, cast=int)

# OTP Settings
OTP_EXPIRY_MINUTES = config('OTP_EXPIRY_MINUTES', default=5, cast=int)
OTP_MAX_ATTEMPTS = config('OTP_MAX_ATTEMPTS', default=3, cast=int)
OTP_RESEND_COOLDOWN_SECONDS = config('OTP_RESEND_COOLDOWN_SECONDS', default=60, cast=int)


# ==============================================================================
# CORS CONFIGURATION
# ==============================================================================

# CORS Configuration for Flutter Mobile App + Web Access
if DEBUG:
    # Development: Allow all origins for easier testing
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGINS = []
else:
    # Production: Restrict to specific origins
    CORS_ALLOW_ALL_ORIGINS = False
    
    # Get configured origins from environment
    cors_origins = config('CORS_ALLOWED_ORIGINS', default='').split(',')
    
    # Add Railway domain if present
    if RAILWAY_PUBLIC_DOMAIN:
        cors_origins.append(f'https://{RAILWAY_PUBLIC_DOMAIN}')
    
    # Add common production URLs
    cors_origins.extend([
        'https://e-kolek-production.up.railway.app',
        'https://ekolek.app',  # If you have a custom domain
    ])
    
    # Remove empty strings and deduplicate
    CORS_ALLOWED_ORIGINS = list(set(filter(None, cors_origins)))

# Essential CORS settings for mobile app
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

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]


# ==============================================================================
# REST FRAMEWORK & JWT CONFIGURATION
# ==============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'eko.authentication.CsrfExemptSessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=config('JWT_ACCESS_TOKEN_LIFETIME_HOURS', default=1, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=30, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
}


# ==============================================================================
# SESSION CONFIGURATION
# ==============================================================================

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_NAME = 'ekolek_session'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = False  # TEMPORARY: Allow JS access for debugging (like CSRF cookie)
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SERIALIZER = 'eko.session_serializer.UUIDJSONSerializer'
# Note: We use a unified session for both user and admin to support simultaneous logins
# The logout views are carefully designed to only clear their respective authentication data
SESSION_COOKIE_PATH = '/'
SESSION_COOKIE_DOMAIN = None  # Explicitly set to None for current domain

if not DEBUG:
    SESSION_COOKIE_SECURE = True  # Requires HTTPS in production (Railway has HTTPS)


# ==============================================================================
# CSRF CONFIGURATION
# ==============================================================================

CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access for mobile apps
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_NAME = 'ekolek_csrftoken'
CSRF_USE_SESSIONS = False  # Mobile apps need cookie-based CSRF
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_COOKIE_PATH = '/'

if not DEBUG:
    CSRF_COOKIE_SECURE = True
    
    # Get configured trusted origins from environment
    csrf_origins = config('CSRF_TRUSTED_ORIGINS', default='').split(',')
    
    # Add Railway domain if present
    if RAILWAY_PUBLIC_DOMAIN:
        csrf_origins.append(f'https://{RAILWAY_PUBLIC_DOMAIN}')
    
    # Add common production URLs
    csrf_origins.extend([
        'https://e-kolek-production.up.railway.app',
        'https://ekolek.app',  # If you have a custom domain
    ])
    
    # Remove empty strings and deduplicate
    CSRF_TRUSTED_ORIGINS = list(set(filter(None, csrf_origins)))


# ==============================================================================
# SECURITY SETTINGS
# ==============================================================================

# Basic security settings (always active)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Production-only security settings
if not DEBUG:
    # Railway handles SSL at proxy level
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # SECURE_SSL_REDIRECT = True  # Disabled for Railway - causes redirect loop
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Additional security headers for production
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
else:
    # Development: Relaxed security for mobile testing
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0

# Content Security Policy (CSP)
# Configured for web app + mobile API access
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net', 'https://unpkg.com', 'https://cdn.tailwindcss.com', 'https://cdnjs.cloudflare.com')
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", 'https://fonts.googleapis.com', 'https://unpkg.com', 'https://cdn.tailwindcss.com', 'https://cdnjs.cloudflare.com', 'https://cdn.jsdelivr.net')
CSP_FONT_SRC = ("'self'", 'https://fonts.gstatic.com', 'https://unpkg.com', 'https://cdnjs.cloudflare.com', 'https://cdn.jsdelivr.net')
CSP_IMG_SRC = ("'self'", 'data:', 'https:', 'blob:')
CSP_CONNECT_SRC = ("'self'", 'https:', 'wss:', 'ws:', '*')  # Allow mobile app API connections
CSP_FRAME_SRC = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_INCLUDE_NONCE_IN = ['script-src', 'style-src']
CSP_REPORT_ONLY = DEBUG  # Only report in debug mode, enforce in production
CSP_EXCLUDE_URL_PREFIXES = ('/admin/', '/api/')  # Don't enforce CSP on API endpoints

# Permissions Policy
PERMISSIONS_POLICY = {
    'accelerometer': [],
    'camera': [],
    'geolocation': [],
    'gyroscope': [],
    'magnetometer': [],
    'microphone': [],
    'payment': [],
    'usb': []
}


# ==============================================================================
# CACHE CONFIGURATION
# ==============================================================================

# Support Railway Redis URL
redis_url = config('REDIS_URL', default='')

if redis_url:
    # Railway Redis
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': redis_url,
        }
    }
else:
    # Local or custom configuration
    CACHES = {
        'default': {
            'BACKEND': config('CACHE_BACKEND', default='django.core.cache.backends.locmem.LocMemCache'),
            'LOCATION': config('CACHE_LOCATION', default=''),
        }
    }


# ==============================================================================
# CELERY CONFIGURATION
# ==============================================================================

# Support Railway Redis URL for Celery
celery_broker_url = config('REDIS_URL', default=config('CELERY_BROKER_URL', default='redis://localhost:6379/0'))

CELERY_BROKER_URL = celery_broker_url
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'default'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_RESULT_EXPIRES = 3600  # 1 hour


# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO' if DEBUG else 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)


# ==============================================================================
# FLUTTER MOBILE APP INTEGRATION
# ==============================================================================
"""
RAILWAY ENVIRONMENT VARIABLES FOR FLUTTER APP CONNECTION:

Required Environment Variables on Railway:
------------------------------------------
1. DJANGO_DEBUG=False
2. RAILWAY_PUBLIC_DOMAIN=your-app.up.railway.app
3. ALLOWED_HOSTS=your-app.up.railway.app,*.railway.app
4. CORS_ALLOWED_ORIGINS=https://your-app.up.railway.app
5. CSRF_TRUSTED_ORIGINS=https://your-app.up.railway.app

Flutter App API Endpoints:
--------------------------
Base URL: https://e-kolek-production.up.railway.app

Authentication:
- POST /api/auth/login/          - Login with JWT
- POST /api/auth/register/       - Register new user
- POST /api/auth/refresh/        - Refresh JWT token
- POST /api/auth/logout/         - Logout

OTP Endpoints:
- POST /api/otp/send/            - Send OTP via SMS
- POST /api/otp/verify/          - Verify OTP code
- POST /api/otp/email/send/      - Send OTP via Email
- POST /api/otp/email/verify/    - Verify Email OTP

User Endpoints:
- GET  /api/user/profile/        - Get user profile
- PUT  /api/user/profile/        - Update user profile
- GET  /api/user/dashboard/      - Get dashboard data

Rate Limiting (Configured):
---------------------------
- OTP Send: 3 requests per hour
- OTP Verify: 5 attempts per OTP
- Cooldown: 15 minutes after limit exceeded

Security Headers (Active):
--------------------------
✅ CORS enabled for mobile app
✅ CSRF protection with mobile support
✅ JWT authentication
✅ Rate limiting on OTP
✅ HTTPS enforced in production
✅ Secure cookies in production

Flutter HTTP Client Setup:
--------------------------
import 'package:http/http.dart' as http;

final String baseUrl = 'https://e-kolek-production.up.railway.app';

// Example: Login request
Future<Map<String, dynamic>> login(String username, String password) async {
  final response = await http.post(
    Uri.parse('$baseUrl/api/auth/login/'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'username': username,
      'password': password,
    }),
  );
  
  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Login failed');
  }
}

Testing the Connection:
-----------------------
1. Test in browser: https://e-kolek-production.up.railway.app/api/
2. Test with Postman/Insomnia
3. Test with Flutter app (dev mode)
4. Check Railway logs for errors

Common Issues:
--------------
1. CORS errors → Check CORS_ALLOWED_ORIGINS
2. CSRF errors → Ensure CSRF token is included
3. 404 errors → Check URL patterns
4. 500 errors → Check Railway logs
5. Connection timeout → Check Railway service status
"""

