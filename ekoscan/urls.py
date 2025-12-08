from django.urls import path
from . import views

# Mobile API endpoints for Admin use (Super Admin & Operations Manager only)
# Now using JWT authentication instead of custom tokens
urlpatterns = [
    # Health check
    path('api/admin/health/', views.health_check, name='health_check'),
    
    # Admin Authentication (JWT-based)
    path('api/admin/login/', views.admin_mobile_login, name='admin_mobile_login'),
    path('api/admin/logout/', views.admin_mobile_logout, name='admin_mobile_logout'),
    path('api/admin/refresh-token/', views.admin_refresh_token, name='admin_refresh_token'),
    path('api/admin/debug-token/', views.debug_token, name='debug_token'),  # Deprecated
    
    # Admin profile
    path('api/admin/profile/', views.get_admin_profile, name='admin_mobile_profile'),
    
    # QR code scanning (Admin scans user QR codes)
    path('api/admin/scan-user/', views.get_user_by_qr, name='admin_scan_user'),
    path('api/admin/user/<str:user_id>/', views.get_user_by_id, name='admin_get_user_by_id'),
    
    # Waste management (Admin processes transactions)
    path('api/admin/waste-types/', views.get_waste_types, name='admin_waste_types'),
    path('api/admin/waste-transaction/', views.create_waste_transaction, name='admin_waste_transaction'),
    
    # Rewards management (Admin processes redemptions)
    path('api/admin/rewards/', views.get_available_rewards, name='admin_rewards'),
    path('api/admin/redeem/', views.redeem_reward, name='admin_redeem_reward'),
    
    # Admin transaction history
    path('api/admin/transactions/', views.get_recent_transactions, name='admin_recent_transactions'),
    
    # User notification endpoints (Public access for dashboard integration)
    path('api/notifications/', views.get_user_notifications, name='get_user_notifications'),
    path('api/notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),
]
