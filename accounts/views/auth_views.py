"""
Authentication views for login and logout
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
import logging
import re
import uuid

from accounts.models import Users
from accounts.security import UserLoginSecurity
from eko.security_utils import get_client_ip, log_security_event
from accounts import otp_service

logger = logging.getLogger(__name__)


def safe_user_logout(request):
    """
    Safely logout user without clearing admin session data
    Preserves admin_* session keys while logging out the user
    Production-ready implementation that handles simultaneous sessions
    """
    # Store admin session data before logout
    admin_session_data = {
        'admin_user_id': request.session.get('admin_user_id'),
        'admin_username': request.session.get('admin_username'),
        'admin_role': request.session.get('admin_role'),
        'admin_full_name': request.session.get('admin_full_name'),
    }
    
    # Get user info for logging before logout
    username = request.user.username if request.user.is_authenticated else 'Unknown'
    
    # Perform standard Django logout (clears user authentication)
    logout(request)
    
    # Restore admin session data if it existed
    for key, value in admin_session_data.items():
        if value is not None:
            request.session[key] = value
    
    # Save session to persist changes
    request.session.save()
    
    logger.info(f"User '{username}' logged out safely, admin session preserved if exists")


@never_cache
@require_http_methods(["GET", "POST"])
def login_page(request):
    # Clear any admin-related messages when loading the login page
    # This prevents admin dashboard messages from appearing in user login interface
    if request.method == 'GET':
        # Check if user just completed registration
        registration_success = request.session.pop('registration_success', False)
        registration_type = request.session.pop('registration_type', None)
        
        # If registration was successful, add appropriate success message
        if registration_success:
            if registration_type == 'family':
                messages.success(request, "Family registered successfully! Please wait for admin approval.")
            elif registration_type == 'member':
                messages.success(request, "Successfully registered as family member! Please wait for admin approval.")
        
        # Get all messages and filter out admin-specific ones
        storage = messages.get_messages(request)
        user_messages = []
        seen_messages = set()  # Track unique messages to prevent duplicates
        
        for message in storage:
            # Only keep messages that are NOT admin-related
            message_text = str(message)
            
            # Skip duplicate messages
            if message_text in seen_messages:
                continue
                
            seen_messages.add(message_text)
            
            # Comprehensive filter to exclude ALL admin messages
            admin_keywords = [
                'admin account', 'suspended', 'unsuspended', 'unlocked', 
                'reactivated', 'approved successfully', 'admin management',
                'sms notification sent', 'sms notification failed', 
                'rejected successfully', 'rejected and removed', 
                'user satoru', 'user gojo',
                'removed from database', 'deleted by',
                'admin created', 'password changed',
                'waste type', 'barangay', 'schedule',
                'reward', 'video', 'question'
            ]
            
            # Check if it starts with "User " followed by a name (admin action pattern)
            is_admin_user_action = False
            if message_text.startswith('User ') and any(keyword in message_text.lower() for keyword in ['approved', 'rejected', 'deleted', 'removed']):
                is_admin_user_action = True
            
            # Only keep login-relevant messages
            if not is_admin_user_action and not any(keyword in message_text.lower() for keyword in admin_keywords):
                user_messages.append((message.level, message_text, message.tags))
        
        # Clear all messages and re-add only user-relevant ones
        storage.used = True
        for level, message_text, tags in user_messages:
            messages.add_message(request, level, message_text, tags)
        
        # DO NOT clear admin session data here - admins should remain logged in
        # when viewing user pages in a different tab/window
        # Admin sessions are managed separately via JWT cookies with 'admin_' prefix
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Check if account is locked
        if UserLoginSecurity.is_account_locked(username):
            messages.error(request, 'Account temporarily locked due to too many failed attempts. Please try again later.')
            log_security_event(
                'LOGIN_BLOCKED_LOCKED_ACCOUNT',
                ip_address=ip_address,
                details=f'Blocked login attempt for locked account: {username}'
            )
            return render(request, 'login.html')

        # Check IP rate limiting
        if UserLoginSecurity.is_ip_rate_limited(ip_address):
            messages.error(request, 'Too many requests from your IP. Please try again later.')
            return render(request, 'login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.status == 'approved':
                # Instead of logging in immediately, send OTP to user's phone
                phone = user.phone
                send_resp = otp_service.send_otp(phone)
                if send_resp.get('success', True):
                    request.session['pending_login_user_id'] = str(user.id)
                    request.session['pending_phone'] = phone
                    messages.info(request, 'OTP sent to your phone. Please verify to continue.')
                    return redirect('verify_otp')
                else:
                    messages.error(request, 'Failed to send OTP. Please try again later.')
            else:
                # Account not approved - this is not a failed authentication, so we manually log it
                UserLoginSecurity.increment_failed_attempts(
                    username, ip_address, user_agent, 'Account not approved'
                )
                messages.error(request, 'Your account is not yet approved by the admin.')
        else:
            # Failed login - signals will handle LoginAttempt creation
            attempts = UserLoginSecurity.get_failed_attempts(username)
            remaining_attempts = max(0, 5 - attempts)  # Ensure non-negative
            
            if attempts >= 5:
                messages.error(request, 'Too many failed login attempts. Your account has been temporarily locked.')
            elif attempts >= 3:
                messages.error(request, f'Invalid username or password. {remaining_attempts} attempts remaining before account lock.')
            else:
                messages.error(request, 'Invalid username or password.')

    context = {}
    return render(request, 'login.html', context)


def logout_view(request):
    """
    Logout USER from the system - Production Ready
    Uses Django's session-based authentication
    IMPORTANT: This ONLY logs out users, NEVER touches admin authentication
    This ensures simultaneous user and admin logins work correctly
    """
    # Get user info before logout for logging
    username = request.user.username if request.user.is_authenticated else 'Unknown'
    
    # Check if admin is logged in to preserve session
    has_admin_session = bool(request.session.get('admin_user_id'))
    
    # Use safe logout to preserve admin session data
    safe_user_logout(request)
    
    # Add success message
    messages.success(request, 'You have been logged out successfully.')
    
    # Log the action
    if has_admin_session:
        logger.info(f"User '{username}' logged out (admin session preserved)")
    else:
        logger.info(f"User '{username}' logged out")
    
    # Redirect to login page
    return redirect('login_page')


@never_cache
@require_http_methods(["GET", "POST"])
def code_login(request):
    """CODE LOGIN (Username + Password) - Direct Login without OTP"""
    if request.method == 'POST':
        username = request.POST.get('user_id')
        password = request.POST.get('password')
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check if account is locked
        if UserLoginSecurity.is_account_locked(username):
            messages.error(request, 'Account temporarily locked due to too many failed attempts. Please try again later.')
            log_security_event(
                'LOGIN_BLOCKED_LOCKED_ACCOUNT',
                ip_address=ip_address,
                details=f'Blocked code login attempt for locked account: {username}'
            )
            return render(request, 'login.html')

        # Check IP rate limiting
        if UserLoginSecurity.is_ip_rate_limited(ip_address):
            messages.error(request, 'Too many requests from your IP. Please try again later.')
            return render(request, 'login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.status == 'approved':
                # Send OTP instead of immediate login
                phone = user.phone
                send_resp = otp_service.send_otp(phone)
                if send_resp.get('success', True):
                    request.session['pending_login_user_id'] = str(user.id)
                    request.session['pending_phone'] = phone
                    messages.info(request, 'OTP sent to your phone. Please verify to continue.')
                    return redirect('verify_otp')
                else:
                    messages.error(request, 'Failed to send OTP. Please try again later.')
            else:
                # Account not approved - this is not a failed authentication, so we manually log it
                UserLoginSecurity.increment_failed_attempts(
                    username, ip_address, user_agent, 'Account not approved'
                )
                messages.error(request, 'Your account is not yet approved by the admin.')
        else:
            # Check if username exists (to store for forgot password)
            try:
                existing_user = Users.objects.get(username=username)
                # Store username in session for forgot password convenience
                request.session['last_attempted_username'] = username
                logger.info(f"Stored username in session for forgot password: {username}")
            except Users.DoesNotExist:
                # Username doesn't exist, don't store it
                pass
            
            # Failed login - signals will handle LoginAttempt creation
            attempts = UserLoginSecurity.get_failed_attempts(username)
            remaining_attempts = max(0, 5 - attempts)  # Ensure non-negative
            
            if attempts >= 5:
                messages.error(request, 'Too many failed login attempts. Your account has been temporarily locked.')
            elif attempts >= 3:
                messages.error(request, f'Invalid username or password. {remaining_attempts} attempts remaining before account lock.')
            else:
                messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


@never_cache
@require_http_methods(["POST"])
def qr_login(request):
    """
    Secure web QR login endpoint with comprehensive validation
    """
    if request.method == "POST":
        try:
            # Parse and validate JSON data
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                log_security_event(
                    'QR_LOGIN_INVALID_JSON',
                    ip_address=get_client_ip(request),
                    details='Invalid JSON in QR login request'
                )
                return JsonResponse({'error': 'Invalid JSON data'}, status=400)
            
            # Input validation and sanitization
            user_id = data.get('user_id', '').strip()
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Log attempt (truncated for security)
            logger.info(f"Web QR Login attempt - User ID prefix: {user_id[:10]}...")
            
            if not user_id:
                logger.warning("Web QR Login failed: Missing user ID")
                return JsonResponse({
                    'error': 'User ID is required'
                }, status=400)
            
            # Validate user ID length and format
            if len(user_id) < 3 or len(user_id) > 100:
                logger.warning(f"Web QR Login failed: Invalid user ID length: {len(user_id)}")
                return JsonResponse({
                    'error': 'Invalid QR code format'
                }, status=400)
            
            # Sanitize user ID (allow only safe characters)
            if not re.match(r'^[a-zA-Z0-9\-_@.]+$', user_id):
                logger.warning("Web QR Login failed: User ID contains invalid characters")
                return JsonResponse({
                    'error': 'Invalid QR code format'
                }, status=400)
            
            logger.info(f"Web QR Login: Looking for user with ID: {user_id[:10]}...")

            # Check IP rate limiting for QR attempts
            if UserLoginSecurity.is_ip_rate_limited(ip_address, limit=15, window_minutes=15):
                log_security_event(
                    'QR_LOGIN_IP_RATE_LIMITED',
                    ip_address=ip_address,
                    details=f'QR login rate limited for IP: {ip_address}'
                )
                return JsonResponse({
                    'error': 'Too many QR scan attempts. Please try again later.'
                }, status=429)

            # Enhanced user lookup with multiple methods
            user = None
            search_method = None
            
            # Try UUID format first (most likely for QR codes)
            try:
                uuid.UUID(user_id)  # Validate UUID format
                user = Users.objects.get(id=user_id)
                search_method = 'user_id'
                logger.info(f"Web QR Login: User found by UUID: {user.username}")
            except (ValueError, Users.DoesNotExist):
                # If not UUID, try username
                try:
                    user = Users.objects.get(username=user_id)
                    search_method = 'username'
                    logger.info(f"Web QR Login: User found by username: {user.username}")
                except Users.DoesNotExist:
                    # Finally try family code
                    try:
                        user = Users.objects.filter(
                            family__family_code=user_id,
                            is_family_representative=True
                        ).first()
                        if user:
                            search_method = 'family_code'
                            logger.info(f"Web QR Login: User found by family code: {user.username}")
                    except Exception:
                        pass
            
            if not user:
                logger.warning(f"Web QR Login failed: User not found for ID: {user_id[:10]}...")
                log_security_event(
                    'QR_LOGIN_INVALID_ID',
                    ip_address=ip_address,
                    details=f'Invalid QR code scanned: {user_id[:10]}...'
                )
                return JsonResponse({
                    'error': 'Invalid QR Code - User not found.'
                }, status=400)
            
            logger.info(f"Web QR Login: Found user {user.username} via {search_method}")
            
            # Enhanced account validation
            if UserLoginSecurity.is_account_locked(user.username):
                logger.warning(f"Web QR Login failed: Account {user.username} is locked")
                log_security_event(
                    'QR_LOGIN_BLOCKED_LOCKED_ACCOUNT',
                    ip_address=ip_address,
                    details=f'QR login blocked for locked account: {user.username}'
                )
                return JsonResponse({
                    'error': 'Account temporarily locked. Please try again later.'
                }, status=403)
            
            # Enhanced user status validation
            if user.status != 'approved':
                logger.warning(f"Web QR Login failed: User {user.username} not approved - Status: {user.status}")
                UserLoginSecurity.increment_failed_attempts(
                    user.username, ip_address, user_agent, 'Account not approved (QR)'
                )
                return JsonResponse({
                    'error': f'Your account is not approved yet. Status: {user.status}'
                }, status=403)
            
            if not user.is_active:
                logger.warning(f"Web QR Login failed: User {user.username} is inactive")
                UserLoginSecurity.increment_failed_attempts(
                    user.username, ip_address, user_agent, 'Account inactive (QR)'
                )
                return JsonResponse({
                    'error': 'Your account is inactive. Please contact admin.'
                }, status=403)
            
            # Enhanced family status validation
            if user.family and user.family.status != 'approved':
                logger.warning(f"Web QR Login failed: Family {user.family.family_name} not approved - Status: {user.family.status}")
                UserLoginSecurity.increment_failed_attempts(
                    user.username, ip_address, user_agent, 'Family not approved (QR)'
                )
                return JsonResponse({
                    'error': f'Your family "{user.family.family_name}" is not approved yet.'
                }, status=403)
            
            # Instead of immediate login, send OTP to user's phone and return success to client
            phone = user.phone
            send_resp = otp_service.send_otp(phone)
            if not send_resp.get('success', True):
                logger.error(f"Web QR Login: Failed to send OTP to {phone}: {send_resp.get('error')}")
                return JsonResponse({'error': 'Failed to send OTP'}, status=500)

            # Store pending login in session (used when verifying OTP)
            request.session['pending_login_user_id'] = str(user.id)
            request.session['pending_phone'] = phone

            logger.info(f"Web QR Login: OTP sent to {phone} for user {user.username}")
            log_security_event(
                'QR_LOGIN_OTP_SENT',
                user=user,
                ip_address=ip_address,
                details=f'OTP sent for QR login for user: {user.username}'
            )

            return JsonResponse({
                'success': True,
                'otp_sent': True,
                'user_id': str(user.id),
                'search_method': search_method
            })
            
        except Exception as e:
            # Log error for debugging but don't expose details to client
            logger.error(f"Web QR Login unexpected error: {str(e)}")
            log_security_event(
                'QR_LOGIN_ERROR',
                ip_address=get_client_ip(request),
                details=f'QR login error: {str(e)}'
            )
            return JsonResponse({
                'error': 'Login failed due to server error. Please try again.'
            }, status=500)

    return JsonResponse({
        'error': 'Invalid request method'
    }, status=405)
