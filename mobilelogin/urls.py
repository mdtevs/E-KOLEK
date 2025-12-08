from django.urls import path
from django.conf import settings
from . import auth_views
from . import user_views
from . import debug_views
from . import schedule_views
from . import game_views
from . import biometric_views
from . import notification_views

urlpatterns = [
    # Authentication endpoints with OTP
    path('api/login/', auth_views.login_view, name='api_login'),          # mobile login -> sends OTP
    path('api/qr-login/', auth_views.qr_login, name='api_qr_login'),      # QR login -> sends OTP
    path('api/login/verify-otp/', auth_views.login_verify_otp, name='api_login_verify_otp'),  # verify OTP and get token
    path('api/logout/', auth_views.logout_view, name='logout'),
    path('logout/', auth_views.logout_view, name='api_logout_web'),  # Browser-friendly logout
    path('api/refresh-token/', auth_views.refresh_token_view, name='refresh_token'),
    path('api/validate-token/', auth_views.validate_token_view, name='validate_token'),
    
    # Biometric authentication endpoints
    path('api/biometric/register/', biometric_views.register_biometric_device, name='biometric_register'),
    path('api/biometric/login/init/', biometric_views.biometric_login_init, name='biometric_login_init'),
    path('api/biometric/login/verify/', biometric_views.biometric_login_verify, name='biometric_login_verify'),
    path('api/biometric/devices/', biometric_views.list_biometric_devices, name='biometric_list_devices'),
    path('api/biometric/devices/<uuid:device_id>/revoke/', biometric_views.revoke_biometric_device, name='biometric_revoke_device'),
    path('api/biometric/devices/<uuid:device_id>/trust/', biometric_views.trust_biometric_device, name='biometric_trust_device'),
    path('api/biometric/history/', biometric_views.biometric_login_history, name='biometric_login_history'),
    
    # User data endpoints
    path('api/current_points/', user_views.current_points, name='current_points'),
    path('api/current_user_data/', user_views.current_user_data, name='current_user_data'),
    path('api/family_members/', user_views.family_members, name='family_members'),
    
    # Points management
    path('api/update_points/', user_views.update_points, name='update_points'),
    
    # Garbage collection schedule endpoints
    path('api/schedule/', schedule_views.get_garbage_schedule, name='get_garbage_schedule'),
    path('api/schedule/all/', schedule_views.get_all_schedules, name='get_all_schedules'),
    path('api/schedule/today/', schedule_views.get_todays_schedule, name='get_todays_schedule'),
    path('api/schedule/barangay/<uuid:barangay_id>/', schedule_views.get_schedule_by_barangay, name='get_schedule_by_barangay'),
    
    # Game configuration endpoints
    path('api/game/configurations/', game_views.get_game_configurations, name='get_game_configurations'),
    path('api/game/cooldown/<str:game_type>/', game_views.get_game_cooldown, name='get_game_cooldown'),
    path('api/game/cooldown/quiz/', game_views.get_quiz_cooldown, name='get_quiz_cooldown'),
    path('api/game/cooldown/dragdrop/', game_views.get_dragdrop_cooldown, name='get_dragdrop_cooldown'),
    
    # Notification endpoints
    path('api/notifications/', notification_views.get_notifications, name='get_notifications'),
    path('api/notifications/mark-viewed/', notification_views.mark_notifications_viewed, name='mark_notifications_viewed'),
    path('api/notifications/<uuid:notification_id>/mark-read/', notification_views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/unread-count/', notification_views.get_unread_count, name='get_unread_count'),
]

# Debug endpoints - only available in DEBUG mode
if settings.DEBUG:
    debug_patterns = [
        path('api/', debug_views.api_test, name='api_test'),
        path('api/debug/user/', debug_views.debug_user_info, name='debug_user_info'),
        path('api/debug/simple-points/', debug_views.debug_simple_points, name='debug_simple_points'),
        path('api/debug/basic-auth/', debug_views.debug_basic_auth, name='debug_basic_auth'),
        path('api/logout/debug/', auth_views.logout_debug, name='logout_debug'),
    ]
    urlpatterns += debug_patterns