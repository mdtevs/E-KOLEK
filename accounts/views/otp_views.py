"""
OTP verification views (SMS and Email OTP)
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.http import JsonResponse
import logging

from accounts.models import Users, Family
from accounts.security import UserLoginSecurity
from eko.security_utils import get_client_ip, log_security_event
from accounts import otp_service
from accounts import email_otp_service

logger = logging.getLogger(__name__)


# ========== SMS OTP ENDPOINTS ==========

def send_otp_view(request):
    """AJAX endpoint to send OTP to a provided phone number.
    Returns JSON response for inline verification.
    """
    if request.method == 'POST':
        phone = request.POST.get('phone_number')
        
        if not phone:
            return JsonResponse({'success': False, 'error': 'Phone number missing'}, status=400)

        # Check if phone number is already registered (unless this is for password reset)
        # Skip check if this is a password reset flow
        is_password_reset = request.session.get('password_reset_user_id') is not None
        
        if not is_password_reset:
            # Normalize phone number for checking
            phone_normalized = phone.strip().replace(' ', '').replace('-', '')
            if phone_normalized.startswith('09'):
                phone_normalized = '+63' + phone_normalized[1:]
            elif phone_normalized.startswith('9') and len(phone_normalized) == 10:
                phone_normalized = '+63' + phone_normalized
            elif not phone_normalized.startswith('+'):
                phone_normalized = '+63' + phone_normalized
            
            # Check if phone is already registered
            # Exclude rejected users/families (they should be deleted, but this is a safety check)
            phone_exists = (
                Users.objects.filter(phone=phone).exclude(status='rejected').exists() or
                Users.objects.filter(phone=phone_normalized).exclude(status='rejected').exists() or
                Family.objects.filter(representative_phone=phone).exclude(status='rejected').exists() or
                Family.objects.filter(representative_phone=phone_normalized).exclude(status='rejected').exists()
            )
            
            if phone_exists:
                return JsonResponse({
                    'success': False, 
                    'error': 'This phone number is already registered. Please use a different number or login if you already have an account.'
                }, status=400)

        resp = otp_service.send_otp(phone)
        
        if resp.get('success'):
            # Store phone in session for verification
            request.session['pending_phone'] = phone
            return JsonResponse({'success': True, 'message': 'OTP sent successfully'})
        else:
            error_msg = resp.get('error', 'Failed to send OTP')
            return JsonResponse({'success': False, 'error': error_msg}, status=400)

    return JsonResponse({'error': 'Invalid method'}, status=405)


def resend_otp_view(request):
    """AJAX endpoint to resend OTP. Returns JSON response."""
    if request.method == 'POST':
        phone = request.POST.get('phone_number') or request.session.get('pending_phone')
        if not phone:
            return JsonResponse({'success': False, 'error': 'Phone number missing'}, status=400)
        
        resp = otp_service.send_otp(phone)
        if resp.get('success', True):
            return JsonResponse({'success': True, 'message': 'OTP resent successfully'})
        else:
            return JsonResponse({'success': False, 'error': resp.get('error', 'Failed to resend OTP')}, status=400)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


def verify_otp_view(request):
    """Handle OTP verification - GET renders page, POST processes verification."""
    
    if request.method == 'GET':
        # Render the OTP verification page for traditional login flows
        phone = request.session.get('pending_phone')
        if not phone:
            messages.error(request, 'No pending OTP verification. Please login again.')
            return redirect('login_page')
        
        return render(request, 'verify_otp.html', {
            'phone_number': phone
        })
    
    if request.method == 'POST':
        otp = request.POST.get('otp')
        phone = request.POST.get('phone_number') or request.session.get('pending_phone')
        
        if not phone or not otp:
            return JsonResponse({'success': False, 'error': 'Missing OTP or phone number'}, status=400)

        # Check if this is a pending login attempt
        pending_user_id = request.session.get('pending_login_user_id')
        user = None
        if pending_user_id:
            try:
                user = Users.objects.get(id=pending_user_id)
                
                # Check if account is locked due to failed attempts
                if UserLoginSecurity.is_account_locked(user.username):
                    logger.warning(f"OTP verification blocked for locked account: {user.username}")
                    return JsonResponse({
                        'success': False, 
                        'error': 'Account is temporarily locked. Please try again later.'
                    }, status=403)
                
            except Users.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found'}, status=400)

        # Verify OTP
        resp = otp_service.verify_otp(phone, otp)
        if not resp.get('success', False):
            err = resp.get('error', 'Invalid OTP code')
            error_type = resp.get('error_type', 'unknown')
            
            # Provide user-friendly error messages based on error type
            if error_type == 'invalid_otp':
                user_message = 'Invalid OTP code. Please check and try again.'
            elif error_type == 'expired_otp':
                user_message = 'OTP code has expired. Please request a new code.'
            elif error_type == 'rate_limit':
                user_message = 'Too many attempts. Please wait a few minutes and try again.'
            elif 'expired' in str(err).lower():
                user_message = 'OTP code has expired. Please request a new code.'
            elif 'invalid' in str(err).lower():
                user_message = 'Invalid OTP code. Please check and try again.'
            else:
                user_message = str(err)
            
            # Track failed OTP attempt if this is a login
            if user:
                ip_address = get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
                UserLoginSecurity.increment_failed_attempts(
                    user.username, ip_address, user_agent, 'Failed OTP verification'
                )
                logger.warning(f"Failed OTP verification for user {user.username} from IP {ip_address}: {err}")
            
            return JsonResponse({'success': False, 'error': user_message}, status=400)

        # OTP verified successfully - store verification in session
        request.session['otp_verified'] = True
        request.session['verified_phone'] = phone
        
        # If this is a pending login, log the user in
        if pending_user_id and user:
            # Log the user in (traditional Django authentication for backward compatibility)
            login(request, user)
            
            # Clear failed login attempts on successful login
            UserLoginSecurity.clear_failed_attempts(user.username)
            
            # Clear pending login session data
            request.session.pop('pending_login_user_id', None)
            request.session.pop('pending_phone', None)
            
            # Log successful login
            ip_address = get_client_ip(request)
            logger.info(f"User {user.username} logged in successfully after OTP verification from IP {ip_address}")
            log_security_event(
                'LOGIN_SUCCESS_WITH_OTP',
                user=user,
                ip_address=ip_address,
                details=f'Successful login with OTP verification for user: {user.username}'
            )
            
            # Return success response (Django session is already set by login())
            logger.info(f"User {user.username} successfully verified OTP and logged in")
            
            return JsonResponse({
                'success': True, 
                'message': 'OTP verified successfully',
                'redirect': True,
                'redirect_url': '/accounts/userdashboard/'
            })

        
        # For registration flows (no pending login)
        return JsonResponse({'success': True, 'message': 'OTP verified successfully'})

    return JsonResponse({'error': 'Invalid method'}, status=405)


# ========== EMAIL OTP ENDPOINTS ==========

def send_email_otp_view(request):
    """AJAX endpoint to send OTP to a provided email address.
    Returns JSON response for inline verification.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            return JsonResponse({'success': False, 'error': 'Email address missing'}, status=400)

        # Check if email is already registered (unless this is for password reset)
        # Skip check if this is a password reset flow
        is_password_reset = request.session.get('password_reset_user_id') is not None
        
        if not is_password_reset:
            # Normalize email for checking
            email_normalized = email.strip().lower()
            
            # Check if email is already registered
            email_exists = Users.objects.filter(email__iexact=email_normalized).exists()
            
            if email_exists:
                return JsonResponse({
                    'success': False,
                    'error': 'This email address is already registered. Please use a different email or login if you already have an account.'
                }, status=400)

        resp = email_otp_service.send_otp(email)
        
        if resp.get('success', True):
            # Store email in session for verification
            request.session['pending_email'] = email
            return JsonResponse({'success': True, 'message': 'OTP sent to your email'})
        else:
            error_msg = resp.get('error', 'Failed to send OTP')
            return JsonResponse({'success': False, 'error': error_msg}, status=400)

    return JsonResponse({'error': 'Invalid method'}, status=405)


def resend_email_otp_view(request):
    """AJAX endpoint to resend email OTP. Returns JSON response."""
    if request.method == 'POST':
        email = request.POST.get('email') or request.session.get('pending_email')
        if not email:
            return JsonResponse({'success': False, 'error': 'Email address missing'}, status=400)
        
        resp = email_otp_service.send_otp(email)
        if resp.get('success', True):
            return JsonResponse({'success': True, 'message': 'OTP resent to your email'})
        else:
            return JsonResponse({'success': False, 'error': resp.get('error', 'Failed to resend OTP')}, status=400)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


def verify_email_otp_view(request):
    """Handle email OTP verification - POST processes verification."""
    
    if request.method == 'POST':
        otp = request.POST.get('otp')
        email = request.POST.get('email') or request.session.get('pending_email')
        
        if not email or not otp:
            return JsonResponse({'success': False, 'error': 'Missing OTP or email address'}, status=400)

        # Verify OTP
        resp = email_otp_service.verify_otp(email, otp)
        if not resp.get('success', False):
            err = resp.get('error', 'Invalid OTP code')
            return JsonResponse({'success': False, 'error': str(err)}, status=400)

        # OTP verified successfully - store verification in session
        request.session['email_otp_verified'] = True
        request.session['verified_email'] = email
        
        # For registration flows
        return JsonResponse({'success': True, 'message': 'Email verified successfully'})

    return JsonResponse({'error': 'Invalid method'}, status=405)
