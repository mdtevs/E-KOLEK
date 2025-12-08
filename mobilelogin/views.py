"""
Mobile Login Views Module
This file imports all views from the organized submodules for backwards compatibility.

View Organization:
- auth_views.py: Authentication endpoints (login, logout, token management)
- user_views.py: User data endpoints (points, profile, family)
- debug_views.py: Debug and testing endpoints
- schedule_views.py: Garbage collection schedule endpoints
- game_views.py: Game configuration endpoints
"""

# Import all authentication views
from .auth_views import (
    login_view,
    qr_login,
    login_verify_otp,
    logout_view,
    logout_debug,
    refresh_token_view,
    validate_token_view,
)

# Import all user data views
from .user_views import (
    current_points,
    current_user_data,
    family_members,
    update_points,
)

# Import all debug views
from .debug_views import (
    api_test,
    debug_user_info,
    debug_simple_points,
    debug_basic_auth,
)

# Import all schedule views
from .schedule_views import (
    get_garbage_schedule,
    get_all_schedules,
    get_schedule_by_barangay,
    get_todays_schedule,
)

# Import all game configuration views
from .game_views import (
    get_game_configurations,
    get_game_cooldown,
    get_quiz_cooldown,
    get_dragdrop_cooldown,
)

# Import all notification views
from .notification_views import (
    get_notifications,
    mark_notifications_viewed,
    mark_notification_read,
    get_unread_count,
)

# Export all views for easy importing
__all__ = [
    # Authentication views
    'login_view',
    'qr_login',
    'login_verify_otp',
    'logout_view',
    'logout_debug',
    'refresh_token_view',
    'validate_token_view',
    # User data views
    'current_points',
    'current_user_data',
    'family_members',
    'update_points',
    # Debug views
    'api_test',
    'debug_user_info',
    'debug_simple_points',
    'debug_basic_auth',
    # Schedule views
    'get_garbage_schedule',
    'get_all_schedules',
    'get_schedule_by_barangay',
    'get_todays_schedule',
    # Game configuration views
    'get_game_configurations',
    'get_game_cooldown',
    'get_quiz_cooldown',
    'get_dragdrop_cooldown',
    # Notification views
    'get_notifications',
    'mark_notifications_viewed',
    'mark_notification_read',
    'get_unread_count',
]
