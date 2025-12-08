"""
Password reset views (forgot password flow)
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
import logging

from accounts.models import Users
from accounts.security import PasswordStrengthValidator
from eko.security_utils import get_client_ip, log_security_event
from accounts import otp_service
from accounts import email_otp_service
from accounts.masking_utils import mask_contact

logger = logging.getLogger(__name__)


def safe_session_clear_password_reset(request):
    """
    Safely clear password reset session data without affecting admin session
    Production-ready: preserves admin authentication when clearing password reset
    """
    # Store admin session data
    admin_session_data = {
        'admin_user_id': request.session.get('admin_user_id'),
        'admin_username': request.session.get('admin_username'),
        'admin_role': request.session.get('admin_role'),
        'admin_full_name': request.session.get('admin_full_name'),
    }
    
    # Clear password reset specific session keys instead of flushing entire session
    keys_to_remove = [
        'password_reset_user_id',
        'password_reset_method',
        'password_reset_contact',
        'password_reset_verified',
        'last_attempted_username'
    ]
    
    for key in keys_to_remove:
        request.session.pop(key, None)
    
    # Restore admin session data if it existed
    for key, value in admin_session_data.items():
        if value is not None:
            request.session[key] = value
    
    request.session.save()


@never_cache
def forgot_password(request):
    """
    Forgot password page - Step 1: User enters username/email and chooses OTP method
    """
    # Get pre-filled username from session if available
    pre_filled_username = request.session.get('last_attempted_username', '')
    
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        otp_method = request.POST.get('otp_method', 'sms')  # 'sms' or 'email'
        
        logger.info(f"Forgot password request for identifier: {identifier[:5]}... via {otp_method}")
        
        # Clear the stored username after use
        if 'last_attempted_username' in request.session:
            del request.session['last_attempted_username']
        
        if not identifier:
            messages.error(request, 'Please enter your username or email.')
            return render(request, 'forgot_password.html', {'pre_filled_username': pre_filled_username})
        
        # Find user by username or email
        user = None
        try:
            # Try to find by username first
            user = Users.objects.get(username=identifier, status='approved')
        except Users.DoesNotExist:
            # Try to find by email
            try:
                user = Users.objects.get(email=identifier, status='approved')
            except Users.DoesNotExist:
                # Don't reveal if user exists or not for security
                messages.error(request, 'If an account with that username/email exists, you will receive a verification code.')
                logger.warning(f"Forgot password: User not found for identifier: {identifier}")
                return render(request, 'forgot_password.html', {'pre_filled_username': ''})
        
        # Check if user account is active
        if not user.is_active:
            messages.error(request, 'Your account is inactive. Please contact support.')
            logger.warning(f"Forgot password: Inactive account - {user.username}")
            return render(request, 'forgot_password.html', {'pre_filled_username': ''})
        
        # Send OTP based on selected method
        if otp_method == 'email':
            if not user.email:
                messages.error(request, 'No email address associated with this account. Please use SMS method.')
                return render(request, 'forgot_password.html', {'pre_filled_username': ''})
            
            # Send email OTP
            logger.info(f"Attempting to send email OTP to {user.email}")
            resp = email_otp_service.send_otp(user.email, purpose='password_reset')
            
            if resp.get('success', False):
                # Store password reset session data
                request.session['password_reset_user_id'] = str(user.id)
                request.session['password_reset_method'] = 'email'
                request.session['password_reset_contact'] = user.email
                
                logger.info(f"Password reset email OTP sent successfully to {user.email}")
                # Mask email for security when displaying to user
                masked_email = mask_contact(user.email, 'email')
                messages.success(request, f'Verification code sent to {masked_email}! Please check your inbox.')
                return redirect('forgot_password_verify')
            else:
                error_msg = resp.get('error', 'Failed to send verification code')
                messages.error(request, f'Failed to send email: {error_msg}. Please try again or use SMS method.')
                logger.error(f"Failed to send email OTP to {user.email}: {error_msg}")
                return render(request, 'forgot_password.html', {'pre_filled_username': identifier})
        else:  # SMS method
            if not user.phone:
                messages.error(request, 'No phone number associated with this account.')
                return render(request, 'forgot_password.html', {'pre_filled_username': ''})
            
            # Send SMS OTP
            logger.info(f"Attempting to send SMS OTP to {user.phone}")
            resp = otp_service.send_otp(user.phone, message='Your E-KOLEK password reset code is :otp. Valid for 5 minutes.')
            
            if resp.get('success', False):
                # Store password reset session data
                request.session['password_reset_user_id'] = str(user.id)
                request.session['password_reset_method'] = 'sms'
                request.session['password_reset_contact'] = user.phone
                
                logger.info(f"Password reset SMS OTP sent successfully to {user.phone}")
                # Mask phone number for security when displaying to user
                masked_phone = mask_contact(user.phone, 'sms')
                messages.success(request, f'Verification code sent to {masked_phone}!')
                return redirect('forgot_password_verify')
            else:
                error_msg = resp.get('error', 'Failed to send verification code')
                messages.error(request, f'Failed to send SMS: {error_msg}. Please try again or use email method.')
                logger.error(f"Failed to send SMS OTP to {user.phone}: {error_msg}")
                return render(request, 'forgot_password.html', {'pre_filled_username': identifier})
    
    return render(request, 'forgot_password.html', {'pre_filled_username': pre_filled_username})


@never_cache
def forgot_password_verify(request):
    """
    Forgot password verification - Step 2: User enters OTP code
    """
    # Check if password reset session exists
    user_id = request.session.get('password_reset_user_id')
    method = request.session.get('password_reset_method')
    contact = request.session.get('password_reset_contact')
    
    if not user_id or not method or not contact:
        messages.error(request, 'Session expired. Please start the password reset process again.')
        return redirect('forgot_password')
    
    # Get user
    try:
        user = Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        messages.error(request, 'Invalid session. Please start again.')
        safe_session_clear_password_reset(request)
        return redirect('forgot_password')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not otp_code or len(otp_code) != 6:
            messages.error(request, 'Please enter a valid 6-digit verification code.')
            return render(request, 'forgot_password_verify.html', {
                'method_display': 'email' if method == 'email' else 'phone',
                'masked_contact': mask_contact(contact, method)
            })
        
        # Verify OTP based on method
        if method == 'email':
            resp = email_otp_service.verify_otp(contact, otp_code, purpose='password_reset')
        else:
            resp = otp_service.verify_otp(contact, otp_code)
        
        if resp.get('success', False):
            # OTP verified successfully
            request.session['password_reset_verified'] = True
            logger.info(f"Password reset OTP verified for user {user.username}")
            messages.success(request, 'Verification successful! Please create a new password.')
            return redirect('reset_password')
        else:
            error_msg = resp.get('error', 'Invalid verification code')
            messages.error(request, error_msg)
            logger.warning(f"Failed OTP verification for password reset - {user.username}")
    
    return render(request, 'forgot_password_verify.html', {
        'method_display': 'email' if method == 'email' else 'phone',
        'masked_contact': mask_contact(contact, method)
    })


@never_cache
def forgot_password_resend(request):
    """
    Resend OTP for password reset
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    # Check if password reset session exists
    user_id = request.session.get('password_reset_user_id')
    method = request.session.get('password_reset_method')
    contact = request.session.get('password_reset_contact')
    
    if not user_id or not method or not contact:
        return JsonResponse({'success': False, 'error': 'Session expired'}, status=400)
    
    # Resend OTP based on method
    if method == 'email':
        resp = email_otp_service.send_otp(contact, purpose='password_reset')
    else:
        resp = otp_service.send_otp(contact, message='Your E-KOLEK password reset code is :otp. Valid for 5 minutes.')
    
    if resp.get('success', True):
        logger.info(f"Password reset OTP resent via {method} to {contact}")
        return JsonResponse({'success': True, 'message': 'Verification code resent successfully'})
    else:
        return JsonResponse({'success': False, 'error': resp.get('error', 'Failed to resend code')}, status=400)


@never_cache
def reset_password(request):
    """
    Reset password - Step 3: User creates new password
    """
    # Check if OTP was verified
    if not request.session.get('password_reset_verified'):
        messages.error(request, 'Please verify your identity first.')
        return redirect('forgot_password')
    
    user_id = request.session.get('password_reset_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('forgot_password')
    
    # Get user
    try:
        user = Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        messages.error(request, 'Invalid session. Please start again.')
        safe_session_clear_password_reset(request)
        return redirect('forgot_password')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        # Validate passwords
        if not new_password or not confirm_password:
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'reset_password.html')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'reset_password.html')
        
        # Validate password strength
        validator = PasswordStrengthValidator()
        try:
            validator.validate(new_password, user)
        except Exception as e:
            messages.error(request, str(e))
            return render(request, 'reset_password.html')
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        # Clear session data
        request.session.pop('password_reset_user_id', None)
        request.session.pop('password_reset_method', None)
        request.session.pop('password_reset_contact', None)
        request.session.pop('password_reset_verified', None)
        
        # Log security event
        ip_address = get_client_ip(request)
        log_security_event(
            'PASSWORD_RESET_SUCCESS',
            user=user,
            ip_address=ip_address,
            details=f'Password reset successfully for user: {user.username}'
        )
        
        logger.info(f"Password reset completed for user {user.username}")
        messages.success(request, '✅ Password reset successfully! You can now login with your new password.')
        return redirect('login_page')
    
    return render(request, 'reset_password.html')
