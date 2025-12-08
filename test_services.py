"""
Test Script for Email, SMS, and OTP Services
Run this to diagnose and test all communication services
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eko.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from accounts import email_otp_service, otp_service, sms_service
import logging

logger = logging.getLogger(__name__)

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(title):
    print(f"\n{Colors.HEADER}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{title.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 70}{Colors.ENDC}\n")


def print_success(message):
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_error(message):
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def print_warning(message):
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


def print_info(message):
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")


def test_configuration():
    """Test if all required settings are configured"""
    print_header("CONFIGURATION CHECK")
    
    issues = []
    
    # Email configuration
    print_info("Email Configuration:")
    if settings.EMAIL_HOST_USER:
        print_success(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    else:
        print_error("  EMAIL_HOST_USER: Not configured")
        issues.append("EMAIL_HOST_USER")
    
    if settings.EMAIL_HOST_PASSWORD:
        print_success(f"  EMAIL_HOST_PASSWORD: {'*' * 16} (hidden)")
    else:
        print_error("  EMAIL_HOST_PASSWORD: Not configured")
        issues.append("EMAIL_HOST_PASSWORD")
    
    print_success(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
    print_success(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
    print_success(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    
    # SMS configuration
    print_info("\nSMS Configuration:")
    sms_token = getattr(settings, 'SMS_API_TOKEN', None)
    if sms_token:
        print_success(f"  SMS_API_TOKEN: {sms_token[:8]}... (hidden)")
    else:
        print_error("  SMS_API_TOKEN: Not configured")
        issues.append("SMS_API_TOKEN")
    
    print_success(f"  SMS_ENABLED: {getattr(settings, 'SMS_ENABLED', False)}")
    print_success(f"  SMS_API_URL: {getattr(settings, 'SMS_API_URL', 'Not set')}")
    
    # Redis/Celery configuration
    print_info("\nCelery Configuration:")
    celery_broker = getattr(settings, 'CELERY_BROKER_URL', 'Not set')
    print_success(f"  CELERY_BROKER_URL: {celery_broker}")
    
    if 'localhost' in celery_broker:
        print_warning("  Using localhost Redis - Make sure Redis is running locally")
    
    # Check Celery availability
    try:
        from accounts.tasks import test_celery_task
        print_success("  Celery tasks module: Available")
        
        # Try to check if worker is running
        try:
            from eko.celery import app
            inspect = app.control.inspect()
            stats = inspect.stats()
            if stats:
                print_success(f"  Celery worker: Running ({len(stats)} workers)")
            else:
                print_warning("  Celery worker: Not running (will use fallback)")
        except Exception as e:
            print_warning(f"  Celery worker: Cannot check status - {str(e)}")
    except ImportError:
        print_error("  Celery: Not available")
        issues.append("CELERY")
    
    if issues:
        print_error(f"\n⚠️  Configuration issues found: {', '.join(issues)}")
        return False
    else:
        print_success("\n✅ All configurations OK!")
        return True


def test_email_direct():
    """Test direct email sending (without OTP)"""
    print_header("TEST 1: Direct Email Sending")
    
    test_email = input("Enter test email address (or press Enter to skip): ").strip()
    if not test_email:
        print_warning("Skipped")
        return
    
    try:
        print_info(f"Sending test email to {test_email}...")
        
        result = send_mail(
            subject='E-KOLEK Test Email',
            message='This is a test email from E-KOLEK system. If you receive this, email configuration is working!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False
        )
        
        if result:
            print_success(f"Email sent successfully! Check {test_email}")
        else:
            print_error("Email sending failed (result=0)")
            
    except Exception as e:
        print_error(f"Email sending failed: {str(e)}")
        print_info("Common fixes:")
        print_info("  1. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env")
        print_info("  2. For Gmail: Enable 2FA and generate App Password")
        print_info("  3. Check if SMTP port 587 is not blocked")


def test_email_otp():
    """Test email OTP sending"""
    print_header("TEST 2: Email OTP Service")
    
    test_email = input("Enter test email address (or press Enter to skip): ").strip()
    if not test_email:
        print_warning("Skipped")
        return
    
    try:
        print_info(f"Sending OTP email to {test_email}...")
        
        result = email_otp_service.send_otp(test_email, purpose='verification')
        
        if result.get('success'):
            print_success("OTP email sent successfully!")
            print_info(f"Task ID: {result.get('task_id', 'N/A')}")
            
            # Test verification
            otp_code = input("\nEnter the OTP code you received (or press Enter to skip): ").strip()
            if otp_code:
                verify_result = email_otp_service.verify_otp(test_email, otp_code, purpose='verification')
                if verify_result.get('success'):
                    print_success("OTP verified successfully!")
                else:
                    print_error(f"OTP verification failed: {verify_result.get('error')}")
        else:
            print_error(f"OTP email failed: {result.get('error')}")
            
    except Exception as e:
        print_error(f"Email OTP test failed: {str(e)}")
        import traceback
        traceback.print_exc()


def test_sms():
    """Test SMS sending"""
    print_header("TEST 3: SMS Service")
    
    test_phone = input("Enter test phone number (09XXXXXXXXX or press Enter to skip): ").strip()
    if not test_phone:
        print_warning("Skipped")
        return
    
    try:
        print_info(f"Sending test SMS to {test_phone}...")
        
        result = sms_service.send_sms(test_phone, "This is a test SMS from E-KOLEK system. If you receive this, SMS configuration is working!")
        
        if result.get('success'):
            print_success("SMS sent successfully!")
            print_info(f"Message ID: {result.get('message_id', 'N/A')}")
        else:
            print_error(f"SMS failed: {result.get('error')}")
            print_info("Common fixes:")
            print_info("  1. Check SMS_API_TOKEN in .env")
            print_info("  2. Verify iProg Tech account has credits")
            print_info("  3. Check phone number format (must be Philippine number)")
            
    except Exception as e:
        print_error(f"SMS test failed: {str(e)}")
        import traceback
        traceback.print_exc()


def test_sms_otp():
    """Test SMS OTP sending"""
    print_header("TEST 4: SMS OTP Service")
    
    test_phone = input("Enter test phone number (09XXXXXXXXX or press Enter to skip): ").strip()
    if not test_phone:
        print_warning("Skipped")
        return
    
    try:
        print_info(f"Sending OTP SMS to {test_phone}...")
        
        result = otp_service.send_otp(test_phone)
        
        if result.get('success'):
            print_success("OTP SMS sent successfully!")
            print_info(f"Message ID: {result.get('message_id', 'N/A')}")
            print_warning(f"OTP Code (for testing): {result.get('data', {}).get('otp_code', 'N/A')}")
            
            # Test verification
            otp_code = input("\nEnter the OTP code you received (or press Enter to skip): ").strip()
            if otp_code:
                verify_result = otp_service.verify_otp(test_phone, otp_code)
                if verify_result.get('success'):
                    print_success("OTP verified successfully!")
                else:
                    print_error(f"OTP verification failed: {verify_result.get('error')}")
        else:
            print_error(f"OTP SMS failed: {result.get('error')}")
            
    except Exception as e:
        print_error(f"SMS OTP test failed: {str(e)}")
        import traceback
        traceback.print_exc()


def test_celery():
    """Test Celery task execution"""
    print_header("TEST 5: Celery Worker")
    
    try:
        from accounts.tasks import test_celery_task
        
        print_info("Sending test task to Celery...")
        
        task = test_celery_task.delay("Hello from test script!")
        
        print_success(f"Task queued! Task ID: {task.id}")
        print_info("Waiting for result (5 seconds timeout)...")
        
        try:
            result = task.get(timeout=5)
            print_success(f"Task completed! Result: {result}")
        except Exception as e:
            print_warning(f"Task did not complete in 5 seconds: {str(e)}")
            print_info("This might mean Celery worker is not running")
            print_info("Check Celery worker logs or start worker with: celery -A eko worker")
            
    except ImportError:
        print_error("Celery not available")
    except Exception as e:
        print_error(f"Celery test failed: {str(e)}")


def main():
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}E-KOLEK Communication Services Test Suite{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    
    # Test configuration
    config_ok = test_configuration()
    
    if not config_ok:
        print_warning("\nSome configurations are missing. Tests may fail.")
        proceed = input("Continue anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            return
    
    # Run tests
    test_email_direct()
    test_email_otp()
    test_sms()
    test_sms_otp()
    test_celery()
    
    # Summary
    print_header("TEST COMPLETE")
    print_info("If any tests failed, check the error messages above")
    print_info("Review SMS_EMAIL_OTP_FIXES.md for detailed troubleshooting")


if __name__ == '__main__':
    main()
