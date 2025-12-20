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
    """
    Check if Celery is configured and should be used.
    
    In production (Railway), Celery worker is always started by start.sh,
    so we trust that if CELERY_AVAILABLE=True and Redis is configured,
    then we should use Celery for email tasks.
    
    This is critical because Railway blocks direct SMTP connections,
    but allows Celery tasks to send emails through the broker queue.
    """
    if not CELERY_AVAILABLE:
        return False
    
    # Check if Redis/broker is configured (indicates production environment)
    try:
        from django.conf import settings
        broker_url = getattr(settings, 'CELERY_BROKER_URL', None)
        if broker_url and ('redis://' in broker_url or 'rediss://' in broker_url):
            # Redis is configured, assume Celery worker is running
            logger.info("✅ Celery configuration detected - using task queue for emails")
            return True
    except Exception as e:
        logger.debug(f"Celery config check failed: {str(e)}")
    
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

# OTP Configuration - Industry Standard Rate Limiting
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 3  # Legacy - now using global rate limit
OTP_SEND_LIMIT = 3  # Max OTP sends per hour
OTP_SEND_WINDOW_MINUTES = 60  # Time window for send limit
OTP_MAX_VERIFY_ATTEMPTS = 5  # Max verification attempts per OTP
OTP_COOLDOWN_MINUTES = 15  # Lockout period after exceeding limits


def _check_send_rate_limit(email):
    """
    Check if email address has exceeded OTP send rate limit.
    
    Returns:
        dict: {'allowed': bool, 'error': str, 'retry_after': int}
    """
    send_count_key = f'email_otp_send_count_{email.lower()}'
    cooldown_key = f'email_otp_cooldown_{email.lower()}'
    
    # Check if in cooldown period
    cooldown_until = cache.get(cooldown_key)
    if cooldown_until:
        cooldown_time = datetime.fromisoformat(cooldown_until)
        if datetime.now() < cooldown_time:
            remaining_seconds = int((cooldown_time - datetime.now()).total_seconds())
            remaining_minutes = remaining_seconds // 60
            logger.warning(f"[RATE LIMIT] Email {email} is in cooldown period. {remaining_minutes}min remaining")
            return {
                'allowed': False,
                'error': f'Too many OTP requests. Please wait {remaining_minutes} minutes before trying again.',
                'retry_after': remaining_seconds
            }
        else:
            cache.delete(cooldown_key)
    
    # Get current send count
    send_data = cache.get(send_count_key)
    if send_data:
        count = send_data.get('count', 0)
        first_send = datetime.fromisoformat(send_data.get('first_send'))
        
        # Check if we're still within the time window
        time_elapsed = datetime.now() - first_send
        if time_elapsed < timedelta(minutes=OTP_SEND_WINDOW_MINUTES):
            if count >= OTP_SEND_LIMIT:
                # Exceeded limit - set cooldown
                cooldown_until = datetime.now() + timedelta(minutes=OTP_COOLDOWN_MINUTES)
                cache.set(cooldown_key, cooldown_until.isoformat(), timeout=OTP_COOLDOWN_MINUTES * 60)
                
                logger.warning(f"[RATE LIMIT] Email {email} exceeded send limit ({count}/{OTP_SEND_LIMIT}). Cooldown for {OTP_COOLDOWN_MINUTES}min")
                return {
                    'allowed': False,
                    'error': f'Too many OTP requests. You have reached the limit of {OTP_SEND_LIMIT} requests per hour. Please wait {OTP_COOLDOWN_MINUTES} minutes.',
                    'retry_after': OTP_COOLDOWN_MINUTES * 60
                }
            else:
                # Within limit, increment counter
                send_data['count'] = count + 1
                send_data['last_send'] = datetime.now().isoformat()
                remaining_time = OTP_SEND_WINDOW_MINUTES * 60 - int(time_elapsed.total_seconds())
                cache.set(send_count_key, send_data, timeout=remaining_time)
                logger.info(f"[RATE LIMIT] Email {email} OTP send count: {count + 1}/{OTP_SEND_LIMIT}")
                return {'allowed': True}
        else:
            cache.delete(send_count_key)
    
    # First send or counter expired, initialize
    send_data = {
        'count': 1,
        'first_send': datetime.now().isoformat(),
        'last_send': datetime.now().isoformat()
    }
    cache.set(send_count_key, send_data, timeout=OTP_SEND_WINDOW_MINUTES * 60)
    logger.info(f"[RATE LIMIT] Email {email} OTP send count: 1/{OTP_SEND_LIMIT}")
    return {'allowed': True}


def _check_verify_rate_limit(email):
    """
    Check if email address has exceeded OTP verification attempt limit.
    
    Returns:
        dict: {'allowed': bool, 'error': str, 'attempts_left': int}
    """
    attempts_key = f'email_otp_verify_attempts_{email.lower()}'
    cooldown_key = f'email_otp_verify_cooldown_{email.lower()}'
    
    # Check if in verification cooldown
    cooldown_until = cache.get(cooldown_key)
    if cooldown_until:
        cooldown_time = datetime.fromisoformat(cooldown_until)
        if datetime.now() < cooldown_time:
            remaining_seconds = int((cooldown_time - datetime.now()).total_seconds())
            remaining_minutes = remaining_seconds // 60
            logger.warning(f"[RATE LIMIT] Email {email} is in verification cooldown. {remaining_minutes}min remaining")
            return {
                'allowed': False,
                'error': f'Too many failed verification attempts. Please wait {remaining_minutes} minutes before trying again.',
                'retry_after': remaining_seconds
            }
        else:
            cache.delete(cooldown_key)
    
    # Get current attempt count
    attempt_data = cache.get(attempts_key)
    if attempt_data:
        count = attempt_data.get('count', 0)
        
        if count >= OTP_MAX_VERIFY_ATTEMPTS:
            # Exceeded limit - set cooldown
            cooldown_until = datetime.now() + timedelta(minutes=OTP_COOLDOWN_MINUTES)
            cache.set(cooldown_key, cooldown_until.isoformat(), timeout=OTP_COOLDOWN_MINUTES * 60)
            cache.delete(attempts_key)
            
            logger.warning(f"[RATE LIMIT] Email {email} exceeded verification attempts ({count}/{OTP_MAX_VERIFY_ATTEMPTS}). Cooldown for {OTP_COOLDOWN_MINUTES}min")
            return {
                'allowed': False,
                'error': f'Too many failed attempts. Please wait {OTP_COOLDOWN_MINUTES} minutes before trying again.',
                'retry_after': OTP_COOLDOWN_MINUTES * 60
            }
        
        return {'allowed': True, 'attempts_left': OTP_MAX_VERIFY_ATTEMPTS - count}
    
    return {'allowed': True, 'attempts_left': OTP_MAX_VERIFY_ATTEMPTS}


def _increment_verify_attempts(email):
    """Increment verification attempt counter"""
    attempts_key = f'email_otp_verify_attempts_{email.lower()}'
    attempt_data = cache.get(attempts_key)
    
    if attempt_data:
        attempt_data['count'] = attempt_data.get('count', 0) + 1
        attempt_data['last_attempt'] = datetime.now().isoformat()
    else:
        attempt_data = {
            'count': 1,
            'first_attempt': datetime.now().isoformat(),
            'last_attempt': datetime.now().isoformat()
        }
    
    cache.set(attempts_key, attempt_data, timeout=(OTP_EXPIRY_MINUTES + 5) * 60)
    logger.info(f"[RATE LIMIT] Email {email} verification attempts: {attempt_data['count']}/{OTP_MAX_VERIFY_ATTEMPTS}")


def _clear_verify_attempts(email):
    """Clear verification attempt counter on successful verification"""
    attempts_key = f'email_otp_verify_attempts_{email.lower()}'
    cache.delete(attempts_key)
    logger.info(f"[RATE LIMIT] Email {email} verification attempts cleared after successful verification")


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
    Send OTP to email address with rate limiting.
    
    Rate Limiting (Industry Standards):
    - Maximum 3 OTP sends per hour
    - 15-minute cooldown after exceeding limit
    - Prevents spam and abuse
    
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
    
    # CHECK RATE LIMIT BEFORE SENDING
    rate_limit_check = _check_send_rate_limit(email)
    if not rate_limit_check['allowed']:
        logger.warning(f"[RATE LIMIT BLOCKED] {rate_limit_check['error']}")
        return {
            'success': False,
            'error': rate_limit_check['error'],
            'error_type': 'rate_limit',
            'retry_after': rate_limit_check.get('retry_after', OTP_COOLDOWN_MINUTES * 60)
        }
    
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
        
        print(f"\n{'='*80}")
        print(f"[EMAIL OTP] Email: {email}")
        print(f"[EMAIL OTP] CELERY_AVAILABLE: {CELERY_AVAILABLE}")
        print(f"[EMAIL OTP] use_celery: {use_celery}")
        print(f"{'='*80}\n")
        
        if use_celery:
            # Production: Use Celery task queue (REQUIRED for Railway)
            # Railway blocks direct SMTP, but Celery tasks work!
            logger.info(f"📧 Queuing email task via Celery for: {email}")
            print(f"[EMAIL OTP] ✅ Using Celery task queue (Railway-compatible)")
            
            try:
                task = send_otp_email_task.delay(
                    email=email,
                    subject=subject,
                    message=message,
                    html_message=html_message
                )
                
                logger.info(f"✅ Email task queued successfully | Task ID: {task.id}")
                print(f"[EMAIL OTP] ✅ Task queued: {task.id}")
                
                return {
                    'success': True,
                    'message': 'OTP sent to your email',
                    'task_id': str(task.id)
                }
            except Exception as celery_error:
                # Celery failed, fallback to direct sending
                logger.error(f"❌ Celery task queue failed: {str(celery_error)}")
                print(f"[EMAIL OTP] ❌ Celery failed: {celery_error}")
                logger.info("🔄 Falling back to direct email sending (will likely fail on Railway)...")
        else:
            logger.warning("⚠️ Celery not configured - using direct email sending (will fail on Railway)")
            print(f"[EMAIL OTP] ⚠️ Using direct SMTP (will be blocked by Railway)")
        
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
    Verify OTP code for email address with rate limiting.
    
    Rate Limiting:
    - Maximum 5 verification attempts per OTP
    - 15-minute cooldown after exceeding limit
    
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
    
    # CHECK VERIFICATION RATE LIMIT FIRST
    rate_limit = _check_verify_rate_limit(email)
    if not rate_limit['allowed']:
        logger.warning(f"[RATE LIMIT BLOCKED] {rate_limit['error']}")
        return {
            'success': False,
            'error': rate_limit['error'],
            'error_type': 'rate_limit',
            'retry_after': rate_limit.get('retry_after', OTP_COOLDOWN_MINUTES * 60)
        }
    
    # Get stored OTP from cache
    cache_key = get_cache_key(email, purpose)
    cache_data = cache.get(cache_key)
    
    if not cache_data:
        logger.error("OTP expired or not found")
        _increment_verify_attempts(email)
        return {'success': False, 'error': 'OTP expired or not found. Please request a new code.'}
    
    # Check OTP-specific attempts (legacy support)
    attempts = cache_data.get('attempts', 0)
    if attempts >= OTP_MAX_ATTEMPTS:
        logger.error("Maximum OTP-specific attempts exceeded")
        cache.delete(cache_key)
        return {'success': False, 'error': 'Maximum verification attempts exceeded. Please request a new code.'}
    
    # Verify OTP
    stored_otp = cache_data.get('otp')
    if stored_otp == otp_code:
        logger.info("OTP verified successfully!")
        # Delete OTP from cache after successful verification
        cache.delete(cache_key)
        # Clear verification attempt counter
        _clear_verify_attempts(email)
        return {'success': True, 'message': 'Email verified successfully'}
    else:
        # Increment both OTP-specific attempts AND global verification attempts
        cache_data['attempts'] = attempts + 1
        cache.set(cache_key, cache_data, timeout=OTP_EXPIRY_MINUTES * 60)
        _increment_verify_attempts(email)
        
        attempts_left = rate_limit.get('attempts_left', OTP_MAX_VERIFY_ATTEMPTS) - 1
        logger.warning(f"Invalid OTP. Attempts remaining: {attempts_left}/{OTP_MAX_VERIFY_ATTEMPTS}")
        
        error_msg = f'Invalid OTP code. {attempts_left} attempts remaining.'
        if attempts_left == 0:
            error_msg = 'Invalid OTP code. No attempts remaining. Please wait before trying again.'
        
        return {
            'success': False,
            'error': error_msg,
            'error_type': 'invalid_otp',
            'attempts_left': attempts_left
        }

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
