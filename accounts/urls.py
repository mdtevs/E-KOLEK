from django.urls import path
from . import views
from . import security_views

urlpatterns = [

    path('', views.home, name='E-KOLEK'),
    
    # Legal Pages
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),

    # Registration URLs
    path('register/', views.register, name='register'),  # Legacy redirect
    path('register/family/', views.register_family, name='register_family'),
    path('register/member/', views.register_member, name='register_member'),

    path('login/', views.login_page, name='login_page'),
    path('logout/', views.logout_view, name='logout'), 

    # Forgot Password URLs
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('forgot-password/verify/', views.forgot_password_verify, name='forgot_password_verify'),
    path('forgot-password/resend/', views.forgot_password_resend, name='forgot_password_resend'),
    path('reset-password/', views.reset_password, name='reset_password'),

    path('login/code/', views.code_login, name='code_login'),
    path('login/qr/', views.qr_login, name='web_qr_login'),  # QR login with user ID

    # OTP endpoints
    path('otp/send/', views.send_otp_view, name='send_otp'),
    path('otp/verify/', views.verify_otp_view, name='verify_otp'),  # Handles both GET (page) and POST (API)
    path('otp/resend/', views.resend_otp_view, name='resend_otp'),

    # Email OTP endpoints
    path('email-otp/send/', views.send_email_otp_view, name='send_email_otp'),
    path('email-otp/verify/', views.verify_email_otp_view, name='verify_email_otp'),
    path('email-otp/resend/', views.resend_email_otp_view, name='resend_email_otp'),

    # Availability check endpoints for registration validation
    path('api/check-phone/', views.check_phone_availability, name='check_phone_availability'),
    path('api/check-email/', views.check_email_availability, name='check_email_availability'),
    
    # Terms and Conditions public API
    path('api/terms/active/', views.get_active_terms, name='get_active_terms'),

    path('userdashboard/', views.userdashboard, name='userdashboard'),
    
    # Notification API endpoints
    path('api/notifications/mark-viewed/', views.mark_notifications_viewed, name='mark_notifications_viewed'),
    path('api/notifications/unread-count/', views.get_unread_count, name='get_unread_count'),
    
    # Security monitoring URLs (admin only)
    path('admin/security/api/stats/', security_views.security_api_stats, name='security_api_stats'),
    path('admin/security/block-ip/', security_views.block_ip, name='block_ip'),
    path('admin/security/unlock-account/', security_views.unlock_account, name='unlock_account'),
    
]
