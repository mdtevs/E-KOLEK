"""
Email OTP Service for E-KOLEK System
Handles sending and verifying OTP codes via email using Celery
"""
import random
import string
import logging
import threading
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Import Celery task
try:
    from accounts.tasks import send_otp_email_task
    CELERY_AVAILABLE = True
    logger.info("✅ Celery available - using production email queue")
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("⚠️ Celery not available - using fallback direct sending")


def check_celery_worker_running():
    """Check if Celery worker is actually running"""
    if not CELERY_AVAILABLE:
        return False
    
    try:
        from eko.celery import app
        # Try to inspect active workers
        inspect = app.control.inspect()
        stats = inspect.stats()
        if stats:
            return True
    except Exception as e:
        logger.debug(f"Celery worker check failed: {str(e)}")
    
    return False


def send_email_async(subject, message, from_email, recipient_list, html_message=None):
    """Send email in a background thread to avoid blocking the request (FALLBACK ONLY)"""
    def send():
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False
            )
            logger.info(f"✅ Email sent successfully to {recipient_list[0]}")
        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
    
    # Start email sending in background thread
    thread = threading.Thread(target=send, daemon=True)
    thread.start()
    logger.info(f"📧 Email queued for sending to {recipient_list[0]}")

# OTP Configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 3


def generate_otp():
    """Generate a random 6-digit OTP code"""
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def get_cache_key(email, purpose='verify'):
    """Generate cache key for OTP storage"""
    return f'email_otp_{purpose}_{email.lower()}'


def get_attempts_key(email):
    """Generate cache key for tracking verification attempts"""
    return f'email_otp_attempts_{email.lower()}'


def send_otp(email, purpose='verification'):
    """
    Send OTP to email address.
    
    Args:
        email: Email address to send OTP to
        purpose: Purpose of OTP (verification, password_reset, etc.)
    
    Returns:
        dict: {'success': bool, 'error': str (if failed)}
    """
    logger.info(f"=== EMAIL OTP SERVICE: send_otp called ===")
    logger.info(f"Email: {email}, Purpose: {purpose}")
    
    if not email:
        logger.error("ERROR: Missing email address")
        return {'success': False, 'error': 'Missing email address'}
    
    # Normalize email
    email = email.strip().lower()
    
    # Generate OTP
    otp_code = generate_otp()
    logger.info(f"Generated OTP: {otp_code}")
    
    # Store OTP in cache with expiry
    cache_key = get_cache_key(email, purpose)
    cache_data = {
        'otp': otp_code,
        'created_at': datetime.now().isoformat(),
        'attempts': 0
    }
    cache.set(cache_key, cache_data, timeout=OTP_EXPIRY_MINUTES * 60)
    logger.info(f"Stored OTP in cache: {cache_key}")
    
    # Prepare email content based on purpose
    if purpose == 'password_reset':
        subject = 'E-KOLEK Password Reset Code'
        message = f"""
Hello,

Your E-KOLEK password reset verification code is: {otp_code}

This code will expire in {OTP_EXPIRY_MINUTES} minutes.

If you did not request a password reset, please ignore this email and your password will remain unchanged.

Best regards,
E-KOLEK Team
        """
    elif purpose == 'verification':
        subject = 'E-KOLEK Email Verification Code'
        message = f"""
Hello,

Your E-KOLEK email verification code is: {otp_code}

This code will expire in {OTP_EXPIRY_MINUTES} minutes.

If you did not request this code, please ignore this email.

Best regards,
E-KOLEK Team
        """
    else:
        subject = 'E-KOLEK Verification Code'
        message = f"""
Hello,

Your E-KOLEK verification code is: {otp_code}

This code will expire in {OTP_EXPIRY_MINUTES} minutes.

Best regards,
E-KOLEK Team
        """
    
    # Generate HTML email based on purpose
    if purpose == 'password_reset':
        email_title = "Password Reset"
        email_message = "You requested to reset your password. Please use the verification code below to proceed:"
        security_notice = "If you did not request a password reset, please ignore this email and your password will remain unchanged."
    else:
        email_title = "Email Verification"
        email_message = "Thank you for registering with E-KOLEK! To complete your registration, please use the verification code below:"
        security_notice = "If you did not request this verification code, please ignore this email or contact our support team if you have concerns."
    
    html_message = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); padding: 40px 20px; text-align: center; }}
            .header h1 {{ color: #ffffff; margin: 0; font-size: 32px; font-weight: 700; }}
            .content {{ padding: 40px 30px; }}
            .otp-box {{ background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); padding: 30px; text-align: center; border-radius: 10px; margin: 30px 0; border: 2px solid #6366f1; }}
            .otp-code {{ font-size: 42px; font-weight: bold; letter-spacing: 8px; color: #6366f1; font-family: 'Courier New', monospace; }}
            .message {{ color: #333333; line-height: 1.6; font-size: 16px; }}
            .warning {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px; }}
            .warning strong {{ color: #f59e0b; }}
            .footer {{ background-color: #f9fafb; padding: 25px; text-align: center; border-top: 1px solid #e5e7eb; }}
            .footer p {{ color: #6b7280; font-size: 14px; margin: 5px 0; }}
            .icon {{ display: inline-block; width: 50px; height: 50px; background-color: rgba(255, 255, 255, 0.2); border-radius: 50%; margin-bottom: 10px; line-height: 50px; font-size: 24px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="icon">🔐</div>
                <h1>E-KOLEK</h1>
                <p style="color: rgba(255, 255, 255, 0.9); margin: 10px 0 0 0; font-size: 14px;">{email_title}</p>
            </div>
            
            <div class="content">
                <p class="message">Hello,</p>
                
                <p class="message">{email_message}</p>
                
                <div class="otp-box">
                    <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Your Verification Code</p>
                    <div class="otp-code">{otp_code}</div>
                    <p style="margin: 15px 0 0 0; color: #6b7280; font-size: 14px;">Valid for {OTP_EXPIRY_MINUTES} minutes</p>
                </div>
                
                <div class="warning">
                    <strong>⚠️ Security Notice:</strong>
                    <p style="margin: 5px 0 0 0; color: #333;">This code will expire in <strong>{OTP_EXPIRY_MINUTES} minutes</strong>. Never share this code with anyone. E-KOLEK staff will never ask for your verification code.</p>
                </div>
                
                <p class="message">{security_notice}</p>
            </div>
            
            <div class="footer">
                <p style="font-weight: 600; color: #333;">Best regards,</p>
                <p style="font-weight: 600; color: #6366f1;">E-KOLEK Team</p>
                <p style="margin-top: 15px;">© 2025 E-KOLEK. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    
    try:
        from_email = f"E-KOLEK System <{settings.DEFAULT_FROM_EMAIL}>"
        
        # Check if we should try Celery
        use_celery = CELERY_AVAILABLE and check_celery_worker_running()
        
        if use_celery:
            # Production: Use Celery task queue (recommended)
            logger.info(f"📧 Queuing email task via Celery for: {email}")
            
            try:
                task = send_otp_email_task.delay(
                    email=email,
                    subject=subject,
                    message=message,
                    html_message=html_message
                )
                
                logger.info(f"✅ Email task queued successfully | Task ID: {task.id}")
                return {
                    'success': True,
                    'message': 'OTP sent to your email',
                    'task_id': str(task.id)
                }
            except Exception as celery_error:
                # Celery failed, fallback to direct sending
                logger.warning(f"⚠️ Celery task failed: {str(celery_error)}")
                logger.info("🔄 Falling back to direct email sending...")
        else:
            logger.info("⚠️ Celery worker not running - using direct email sending")
        
        # Send email directly (synchronous) - fallback or when Celery unavailable
        try:
            print(f"\n{'='*80}")
            print(f"[EMAIL DEBUG] Attempting to send email to: {email}")
            print(f"[EMAIL DEBUG] Subject: {subject}")
            print(f"[EMAIL DEBUG] From: {from_email}")
            print(f"{'='*80}\n")
            
            logger.info(f"📧 Sending email directly to: {email}")
            
            result = send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False
            )
            
            print(f"\n{'='*80}")
            print(f"[EMAIL DEBUG] ✅ send_mail returned: {result}")
            print(f"[EMAIL DEBUG] Email should be sent successfully")
            print(f"{'='*80}\n")
            
            logger.info(f"✅ Email sent directly to {email}")
            return {'success': True, 'message': 'OTP sent to your email'}
            
        except Exception as mail_error:
            print(f"\n{'='*80}")
            print(f"[EMAIL DEBUG] ❌ EXCEPTION CAUGHT!")
            print(f"[EMAIL DEBUG] Error type: {type(mail_error).__name__}")
            print(f"[EMAIL DEBUG] Error message: {str(mail_error)}")
            print(f"{'='*80}\n")
            
            logger.error(f"❌ Failed to send email directly: {str(mail_error)}")
            import traceback
            logger.error(traceback.format_exc())
            print(traceback.format_exc())
            
            return {'success': False, 'error': f'Failed to send email: {str(mail_error)}'}
    
    except Exception as e:
        logger.error(f"Failed to send/queue email: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {'success': False, 'error': f'Failed to send email: {str(e)}'}


def verify_otp(email, otp_code, purpose='verification'):
    """
    Verify OTP code for email address.
    
    Args:
        email: Email address
        otp_code: OTP code to verify
        purpose: Purpose of OTP verification
    
    Returns:
        dict: {'success': bool, 'error': str (if failed)}
    """
    logger.info(f"=== EMAIL OTP SERVICE: verify_otp called ===")
    logger.info(f"Email: {email}, OTP: {otp_code}")
    
    if not email or not otp_code:
        logger.error("ERROR: Missing email or OTP code")
        return {'success': False, 'error': 'Missing email or OTP code'}
    
    # Normalize
    email = email.strip().lower()
    otp_code = str(otp_code).strip()
    
    # Get stored OTP from cache
    cache_key = get_cache_key(email, purpose)
    cache_data = cache.get(cache_key)
    
    if not cache_data:
        logger.error("OTP expired or not found")
        return {'success': False, 'error': 'OTP expired or not found. Please request a new code.'}
    
    # Check attempts
    attempts = cache_data.get('attempts', 0)
    if attempts >= OTP_MAX_ATTEMPTS:
        logger.error("Maximum verification attempts exceeded")
        cache.delete(cache_key)
        return {'success': False, 'error': 'Maximum verification attempts exceeded. Please request a new code.'}
    
    # Verify OTP
    stored_otp = cache_data.get('otp')
    if stored_otp == otp_code:
        logger.info("OTP verified successfully!")
        # Delete OTP from cache after successful verification
        cache.delete(cache_key)
        return {'success': True, 'message': 'Email verified successfully'}
    else:
        logger.warning(f"Invalid OTP. Attempts: {attempts + 1}/{OTP_MAX_ATTEMPTS}")
        # Increment attempts
        cache_data['attempts'] = attempts + 1
        cache.set(cache_key, cache_data, timeout=OTP_EXPIRY_MINUTES * 60)
        
        remaining_attempts = OTP_MAX_ATTEMPTS - cache_data['attempts']
        if remaining_attempts > 0:
            return {'success': False, 'error': f'Invalid OTP code. {remaining_attempts} attempts remaining.'}
        else:
            cache.delete(cache_key)
            return {'success': False, 'error': 'Invalid OTP code. Maximum attempts exceeded.'}


def clear_otp(email, purpose='verification'):
    """Clear OTP from cache"""
    cache_key = get_cache_key(email, purpose)
    cache.delete(cache_key)
    logger.info(f"Cleared OTP for {email}")
