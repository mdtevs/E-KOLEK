"""
Admin Email Notification Service for E-KOLEK System
Handles sending email notifications to admin users
"""
import logging
import threading
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

logger = logging.getLogger(__name__)

# Import Celery task if available
try:
    from accounts.tasks import send_otp_email_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False


def send_email_async(subject, html_message, recipient_email):
    """Send email in a background thread to avoid blocking the request"""
    def send():
        try:
            plain_message = strip_tags(html_message)
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False
            )
            logger.info(f"✅ Admin email sent successfully to {recipient_email}")
        except Exception as e:
            logger.error(f"❌ Failed to send admin email to {recipient_email}: {str(e)}")
    
    # Start email sending in background thread
    thread = threading.Thread(target=send, daemon=True)
    thread.start()
    logger.info(f"📧 Admin email queued for sending to {recipient_email}")


def send_credentials_email(admin_user, temporary_password, created_by_admin):
    """
    Send admin credentials to the newly created admin user
    
    Args:
        admin_user: AdminUser object
        temporary_password: The generated temporary password
        created_by_admin: AdminUser who created this account
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        subject = f'E-KOLEK Admin Account Created - {admin_user.get_role_display()}'
        
        # Create HTML email content
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb; }}
        .header {{ background-color: #6366f1; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .credentials {{ background-color: #f3f4f6; padding: 20px; margin: 20px 0; border-left: 4px solid #6366f1; border-radius: 4px; }}
        .credentials strong {{ color: #6366f1; }}
        .password-box {{ background-color: #fef3cd; border: 2px solid #fbbf24; padding: 15px; margin: 15px 0; border-radius: 4px; font-family: monospace; font-size: 18px; text-align: center; color: #92400e; }}
        .warning {{ background-color: #fee2e2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .footer {{ text-align: center; margin-top: 20px; padding: 20px; color: #6b7280; font-size: 14px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 6px; margin: 15px 0; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Welcome to E-KOLEK Admin Panel</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{admin_user.full_name}</strong>,</p>
            
            <p>Your admin account has been successfully created by <strong>{created_by_admin.full_name}</strong> (Super Administrator).</p>
            
            <div class="credentials">
                <h3>Your Login Credentials:</h3>
                <p><strong>Username:</strong> {admin_user.username}</p>
                <p><strong>Role:</strong> {admin_user.get_role_display()}</p>
                <p><strong>Email:</strong> {admin_user.email}</p>
                
                <p><strong>Temporary Password:</strong></p>
                <div class="password-box">
                    {temporary_password}
                </div>
            </div>
            
            <div class="warning">
                <strong>⚠️ Important Security Information:</strong>
                <ul>
                    <li>This is a <strong>temporary password</strong> that must be changed on your first login.</li>
                    <li>You will be prompted to create a new password immediately after logging in.</li>
                    <li>Your new password must be at least 8 characters long.</li>
                    <li>Do not share your credentials with anyone.</li>
                </ul>
            </div>
            
            <h3>Your Role & Permissions:</h3>
            <p>As a <strong>{admin_user.get_role_display()}</strong>, you have access to:</p>
            <ul>
                {"<li>User Management</li>" if admin_user.can_manage_users else ""}
                {"<li>Controls Management</li>" if admin_user.can_manage_controls else ""}
                {"<li>Points Management</li>" if admin_user.can_manage_points else ""}
                {"<li>Rewards Management</li>" if admin_user.can_manage_rewards else ""}
                {"<li>Schedule Management</li>" if admin_user.can_manage_schedules else ""}
                {"<li>Security Management</li>" if admin_user.can_manage_security else ""}
                {"<li>Learning Management</li>" if admin_user.can_manage_learning else ""}
                {"<li>Games Management</li>" if admin_user.can_manage_games else ""}
            </ul>
            
            <p style="text-align: center;">
                <a href="{settings.SITE_URL}/cenro/admin/login/" class="button">Login to Admin Panel</a>
            </p>
            
            <p style="margin-top: 30px;">If you have any questions or did not expect this account creation, please contact the Super Administrator immediately.</p>
            
            <p>Best regards,<br>
            <strong>E-KOLEK Admin Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated email. Please do not reply to this message.</p>
            <p>© 2025 E-KOLEK System. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Send email asynchronously
        send_email_async(subject, html_message, admin_user.email)
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send credentials email to {admin_user.email}: {str(e)}")
        return False


def send_suspension_email(admin_user, suspended_by_admin, reason):
    """
    Send suspension notification email to admin
    
    Args:
        admin_user: AdminUser object who was suspended
        suspended_by_admin: AdminUser who performed the suspension
        reason: Reason for suspension
    
    Returns:
        bool: True if email was sent successfully
    """
    try:
        subject = f'⚠️ E-KOLEK Admin Account Suspended'
        
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb; }}
        .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .reason-box {{ background-color: #fee2e2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .footer {{ text-align: center; margin-top: 20px; padding: 20px; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ Account Suspended</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{admin_user.full_name}</strong>,</p>
            
            <p>Your E-KOLEK admin account has been <strong>suspended</strong> by <strong>{suspended_by_admin.full_name}</strong> (Super Administrator).</p>
            
            <div class="reason-box">
                <strong>Reason for Suspension:</strong>
                <p>{reason}</p>
            </div>
            
            <p><strong>What this means:</strong></p>
            <ul>
                <li>Your access to the admin panel has been temporarily disabled.</li>
                <li>You will not be able to log in until your account is reactivated.</li>
                <li>All your data and settings remain intact.</li>
            </ul>
            
            <p style="margin-top: 30px;">If you believe this suspension was made in error, please contact the Super Administrator for clarification.</p>
            
            <p>Best regards,<br>
            <strong>E-KOLEK Admin Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated email. Please do not reply to this message.</p>
            <p>© 2025 E-KOLEK System. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        send_email_async(subject, html_message, admin_user.email)
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send suspension email to {admin_user.email}: {str(e)}")
        return False


def send_lock_notification_email(admin_user):
    """
    Send account lock notification email to admin
    
    Args:
        admin_user: AdminUser object whose account was locked
    
    Returns:
        bool: True if email was sent successfully
    """
    try:
        from django.utils import timezone
        lock_until = admin_user.account_locked_until
        
        subject = f'🔒 E-KOLEK Admin Account Locked'
        
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb; }}
        .header {{ background-color: #f59e0b; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .warning {{ background-color: #fef3cd; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .footer {{ text-align: center; margin-top: 20px; padding: 20px; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Account Temporarily Locked</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{admin_user.full_name}</strong>,</p>
            
            <p>Your E-KOLEK admin account has been <strong>temporarily locked</strong> due to multiple failed login attempts.</p>
            
            <div class="warning">
                <strong>Account will be automatically unlocked at:</strong>
                <p style="font-size: 18px; color: #92400e; font-weight: bold;">
                    {lock_until.strftime("%B %d, %Y at %I:%M %p") if lock_until else "N/A"}
                </p>
            </div>
            
            <p><strong>Security Information:</strong></p>
            <ul>
                <li>Your account has been locked for <strong>30 minutes</strong> as a security precaution.</li>
                <li>This helps protect your account from unauthorized access attempts.</li>
                <li>You can try logging in again after the lock period expires.</li>
                <li>If you need immediate access, contact a Super Administrator to unlock your account.</li>
            </ul>
            
            <p style="background-color: #fee2e2; padding: 15px; border-radius: 4px; border-left: 4px solid #dc2626;">
                <strong>⚠️ If you did not attempt to log in:</strong><br>
                Your account may be under attack. Please contact the Super Administrator immediately and consider changing your password.
            </p>
            
            <p style="margin-top: 30px;">Best regards,<br>
            <strong>E-KOLEK Admin Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated email. Please do not reply to this message.</p>
            <p>© 2025 E-KOLEK System. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        send_email_async(subject, html_message, admin_user.email)
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send lock notification email to {admin_user.email}: {str(e)}")
        return False


def send_reactivation_email(admin_user, reactivated_by_admin):
    """
    Send reactivation/unsuspension notification email to admin
    
    Args:
        admin_user: AdminUser object who was reactivated
        reactivated_by_admin: AdminUser who performed the reactivation
    
    Returns:
        bool: True if email was sent successfully
    """
    try:
        subject = f'✅ E-KOLEK Admin Account Reactivated'
        
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb; }}
        .header {{ background-color: #10b981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .success-box {{ background-color: #d1fae5; border-left: 4px solid #10b981; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #10b981; color: white; text-decoration: none; border-radius: 6px; margin: 15px 0; }}
        .footer {{ text-align: center; margin-top: 20px; padding: 20px; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Account Reactivated</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{admin_user.full_name}</strong>,</p>
            
            <p>Good news! Your E-KOLEK admin account has been <strong>reactivated</strong> by <strong>{reactivated_by_admin.full_name}</strong> (Super Administrator).</p>
            
            <div class="success-box">
                <strong>✓ Your account is now active</strong>
                <p>You can now log in and access all your assigned admin functions.</p>
            </div>
            
            <p><strong>Account Details:</strong></p>
            <ul>
                <li><strong>Username:</strong> {admin_user.username}</li>
                <li><strong>Role:</strong> {admin_user.get_role_display()}</li>
                <li><strong>Email:</strong> {admin_user.email}</li>
            </ul>
            
            <p style="text-align: center;">
                <a href="{settings.SITE_URL}/cenro/admin/login/" class="button">Login to Admin Panel</a>
            </p>
            
            <p style="margin-top: 30px;">If you have any questions, please contact the Super Administrator.</p>
            
            <p>Best regards,<br>
            <strong>E-KOLEK Admin Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated email. Please do not reply to this message.</p>
            <p>© 2025 E-KOLEK System. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        send_email_async(subject, html_message, admin_user.email)
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send reactivation email to {admin_user.email}: {str(e)}")
        return False


def send_unlock_notification_email(admin_user, unlocked_by_admin):
    """
    Send account unlock notification email to admin
    
    Args:
        admin_user: AdminUser object whose account was unlocked
        unlocked_by_admin: AdminUser who performed the unlock
    
    Returns:
        bool: True if email was sent successfully
    """
    try:
        subject = f'🔓 E-KOLEK Admin Account Unlocked'
        
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb; }}
        .header {{ background-color: #3b82f6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .success-box {{ background-color: #dbeafe; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 6px; margin: 15px 0; }}
        .footer {{ text-align: center; margin-top: 20px; padding: 20px; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔓 Account Unlocked</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{admin_user.full_name}</strong>,</p>
            
            <p>Your E-KOLEK admin account has been <strong>unlocked</strong> by <strong>{unlocked_by_admin.full_name}</strong> (Super Administrator).</p>
            
            <div class="success-box">
                <strong>✓ Your account is now accessible</strong>
                <p>All failed login attempts have been reset and you can log in immediately.</p>
            </div>
            
            <p style="text-align: center;">
                <a href="{settings.SITE_URL}/cenro/admin/login/" class="button">Login to Admin Panel</a>
            </p>
            
            <p style="margin-top: 30px;">If you continue to have login issues, please contact the Super Administrator.</p>
            
            <p>Best regards,<br>
            <strong>E-KOLEK Admin Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated email. Please do not reply to this message.</p>
            <p>© 2025 E-KOLEK System. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        send_email_async(subject, html_message, admin_user.email)
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send unlock notification email to {admin_user.email}: {str(e)}")
        return False


def send_password_reset_email(admin_user, temporary_password, reset_by_admin, reset_reason=None):
    """
    Send password reset notification email to admin with temporary password
    
    Args:
        admin_user: AdminUser object whose password was reset
        temporary_password: The generated temporary password
        reset_by_admin: AdminUser who performed the password reset
        reset_reason: Optional reason for the password reset
    
    Returns:
        bool: True if email was sent successfully
    """
    try:
        subject = f'🔑 E-KOLEK Admin Password Reset'
        
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb; }}
        .header {{ background-color: #ff9800; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .password-box {{ background-color: #fef9e7; border: 2px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 8px; }}
        .password-display {{ background-color: #ffffff; border: 2px dashed #ff9800; padding: 15px; margin: 15px 0; border-radius: 6px; font-family: 'Courier New', monospace; font-size: 20px; text-align: center; color: #92400e; font-weight: bold; letter-spacing: 2px; }}
        .warning {{ background-color: #fee2e2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .info-box {{ background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .footer {{ text-align: center; margin-top: 20px; padding: 20px; color: #6b7280; font-size: 14px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔑 Password Reset Notification</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{admin_user.full_name}</strong>,</p>
            
            <p>Your E-KOLEK admin account password has been <strong>reset</strong> by <strong>{reset_by_admin.full_name}</strong> ({reset_by_admin.get_role_display()}).</p>
            
            {f'<div class="info-box"><strong>Reason for Reset:</strong><p>{reset_reason}</p></div>' if reset_reason else ''}
            
            <div class="password-box">
                <h3 style="margin-top: 0; color: #92400e;">🔐 Your New Temporary Password:</h3>
                <div class="password-display">
                    {temporary_password}
                </div>
                <p style="font-size: 13px; color: #92400e; margin-bottom: 0;">
                    <strong>⚠️ Important:</strong> Copy this password now. You will need to change it immediately upon login.
                </p>
            </div>
            
            <div class="warning">
                <strong>🔒 Security Requirements:</strong>
                <ul style="margin: 10px 0;">
                    <li>This is a <strong>temporary password</strong> that must be changed on your next login.</li>
                    <li>You will be required to create a new password immediately.</li>
                    <li>Your new password must be at least 8 characters long.</li>
                    <li>Do not share this password with anyone.</li>
                    <li>If you did not request this reset, contact the Super Administrator immediately.</li>
                </ul>
            </div>
            
            <div class="info-box">
                <strong>📝 Next Steps:</strong>
                <ol style="margin: 10px 0; padding-left: 20px;">
                    <li>Copy the temporary password above</li>
                    <li>Go to the admin login page</li>
                    <li>Enter your username: <strong>{admin_user.username}</strong></li>
                    <li>Enter the temporary password</li>
                    <li>You will be prompted to create a new password</li>
                </ol>
            </div>
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{settings.SITE_URL}/cenro/admin/login/" style="display: inline-block; padding: 12px 24px; background-color: #ff9800; color: white; text-decoration: none; border-radius: 6px; font-weight: 600;">
                    Login to Admin Panel
                </a>
            </p>
            
            <p style="margin-top: 30px; font-size: 14px; color: #6b7280;">
                <strong>Account Details:</strong><br>
                Username: <strong>{admin_user.username}</strong><br>
                Role: <strong>{admin_user.get_role_display()}</strong><br>
                Reset Date: <strong>{timezone.now().strftime("%B %d, %Y at %I:%M %p")}</strong>
            </p>
            
            <p style="margin-top: 30px;">Best regards,<br>
            <strong>E-KOLEK Admin Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated email. Please do not reply to this message.</p>
            <p>If you did not request this password reset, please contact your Super Administrator immediately.</p>
            <p>© 2025 E-KOLEK System. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        send_email_async(subject, html_message, admin_user.email)
        logger.info(f"📧 Password reset email sent to {admin_user.email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send password reset email to {admin_user.email}: {str(e)}")
        return False
