"""
Application-wide constants for CENRO Waste Management System
Centralizes magic numbers and configuration values
"""

# ============================================
# SESSION & AUTHENTICATION
# ============================================
SESSION_DURATION_SECONDS = 24 * 60 * 60  # 24 hours
OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 3
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_VERIFICATION_CACHE_MINUTES = 2

# JWT Token lifetimes (in seconds)
JWT_ACCESS_TOKEN_LIFETIME_HOURS = 1
JWT_REFRESH_TOKEN_LIFETIME_DAYS = 30

# ============================================
# GAME CONFIGURATION
# ============================================
DEFAULT_GAME_COOLDOWN_HOURS = 72  # 3 days
QUIZ_PASSING_PERCENTAGE = 70.0
DEFAULT_QUESTION_POINTS = 1.0
DEFAULT_WASTE_ITEM_POINTS = 10.0

# Game difficulty levels
DIFFICULTY_EASY = 'easy'
DIFFICULTY_MEDIUM = 'medium'
DIFFICULTY_HARD = 'hard'

# ============================================
# POINTS & REWARDS
# ============================================
REFERRAL_BONUS_POINTS = 50.0
VIDEO_WATCH_MIN_PERCENTAGE = 80.0  # Minimum % to earn points
QUIZ_COMPLETION_BONUS = 10.0

# ============================================
# SECURITY
# ============================================
MAX_LOGIN_ATTEMPTS = 3
LOGIN_ATTEMPT_WINDOW_MINUTES = 15
BRUTE_FORCE_COOLDOWN_MINUTES = 30

# Password requirements
MIN_PASSWORD_LENGTH = 12
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True

# ============================================
# NOTIFICATIONS
# ============================================
SMS_RETRY_ATTEMPTS = 3
SMS_TIMEOUT_SECONDS = 10
EMAIL_RETRY_ATTEMPTS = 3
EMAIL_TIMEOUT_SECONDS = 30

# ============================================
# FILE UPLOADS
# ============================================
MAX_UPLOAD_SIZE_MB = 10
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.webm', '.mov']

# ============================================
# PAGINATION
# ============================================
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ============================================
# FAMILY & USER
# ============================================
FAMILY_CODE_LENGTH = 12
QR_CODE_SIZE = 300  # pixels
DEFAULT_CITY = "San Pedro City"

# User status choices
STATUS_PENDING = 'pending'
STATUS_APPROVED = 'approved'
STATUS_REJECTED = 'rejected'

# ============================================
# ADMIN ROLES
# ============================================
ROLE_SUPER_ADMIN = 'super_admin'
ROLE_ADMIN = 'admin'
ROLE_OPERATIONS_MANAGER = 'operations_manager'

# Special admin family code
ADMIN_FAMILY_CODE = 'ADMIN000000'
ADMIN_BARANGAY_NAME = 'Admin'

# ============================================
# DATABASE OPTIMIZATION
# ============================================
DB_QUERY_BATCH_SIZE = 500
CACHE_TIMEOUT_SHORT = 60  # 1 minute
CACHE_TIMEOUT_MEDIUM = 300  # 5 minutes
CACHE_TIMEOUT_LONG = 3600  # 1 hour

# ============================================
# API VERSIONING
# ============================================
API_VERSION = 'v1'
API_BASE_PATH = f'/api/{API_VERSION}/'

# ============================================
# LOGGING
# ============================================
LOG_ROTATION_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
