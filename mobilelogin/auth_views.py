"""
Authentication views for mobile API
Handles login, logout, OTP verification, and JWT token management
"""
# Standard library
import json
import logging
import re
import uuid

# Django
from django.http import JsonResponse
from django.utils import timezone

# Django REST Framework
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

# Local apps
from accounts.models import Users
from accounts import otp_service


logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Mobile login: validate username/password then send OTP to the user's phone.
    Client must call /api/login/verify-otp/ with user_id and otp to obtain token.
    """
    try:
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not username:
            return Response({'success': False, 'message': 'Username is required', 'error_code': 'MISSING_USERNAME'}, status=400)
        if not password:
            return Response({'success': False, 'message': 'Password is required', 'error_code': 'MISSING_PASSWORD'}, status=400)

        if len(password) < 6:
            return Response({'success': False, 'message': 'Invalid credentials format', 'error_code': 'INVALID_FORMAT'}, status=400)

        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)
        if not user:
            logger.warning(f"Failed login attempt for username: {username}")
            return Response({'success': False, 'message': 'Invalid username or password', 'error_code': 'INVALID_CREDENTIALS'}, status=401)

        if not user.is_active:
            return Response({'success': False, 'message': 'Account deactivated', 'error_code': 'ACCOUNT_INACTIVE'}, status=403)

        # Require that user status be approved for login
        if getattr(user, 'status', '') != 'approved':
            return Response({'success': False, 'message': 'Account not approved', 'error_code': 'ACCOUNT_NOT_APPROVED', 'user_status': user.status}, status=403)

        # Family/system access check
        if hasattr(user, 'can_access_system') and not user.can_access_system():
            return Response({'success': False, 'message': 'Account or family not approved', 'error_code': 'FAMILY_NOT_APPROVED'}, status=403)

        phone = getattr(user, 'phone', None)
        if not phone:
            logger.error(f"No phone number for user {user.username}")
            return Response({'success': False, 'message': 'No phone number on record', 'error_code': 'NO_PHONE'}, status=500)

        send_resp = otp_service.send_otp(phone)
        if not send_resp.get('success', False):
            logger.error(f"Failed to send OTP to {phone}: {send_resp}")
            return Response({'success': False, 'message': 'Failed to send OTP', 'error_code': 'OTP_SEND_FAILED'}, status=500)

        # Respond with user id so client can call verify endpoint
        return Response({'success': True, 'otp_sent': True, 'user_id': str(user.id)}, status=200)

    except Exception as e:
        logger.exception(f"Unexpected error during login: {e}")
        return Response({'success': False, 'message': 'Internal error', 'error_code': 'INTERNAL_ERROR'}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def qr_login(request):
    """
    QR login: identify user by QR payload (username | user_id | family_code), then send OTP.
    Client must call /api/login/verify-otp/ with user_id and otp to obtain token.
    """
    try:
        qr_code = (request.data.get('qr_code', '') or '').strip()
        logger.info(f"QR Login attempt - prefix: {qr_code[:10]}...")

        if not qr_code:
            return Response({'success': False, 'message': 'QR code is required', 'error_code': 'MISSING_QR_CODE'}, status=400)

        if len(qr_code) < 3 or len(qr_code) > 200:
            return Response({'success': False, 'message': 'Invalid QR code format', 'error_code': 'INVALID_QR_FORMAT'}, status=400)

        if not re.match(r'^[a-zA-Z0-9\-_@.]+$', qr_code):
            return Response({'success': False, 'message': 'Invalid QR code characters', 'error_code': 'INVALID_QR_CHARACTERS'}, status=400)

        user = None
        # try username
        try:
            user = Users.objects.get(username=qr_code, is_active=True)
            search_method = 'username'
        except Users.DoesNotExist:
            user = None

        # try uuid id
        if not user:
            try:
                uuid.UUID(qr_code)
                user = Users.objects.get(id=qr_code, is_active=True)
                search_method = 'user_id'
            except Exception:
                user = None

        # try family representative by family code
        if not user:
            user = Users.objects.filter(family__family_code=qr_code, is_active=True, is_family_representative=True).first()
            search_method = 'family_code' if user else None

        if not user:
            logger.warning(f"QR Login: user not found for qr prefix {qr_code[:10]}")
            return Response({'success': False, 'message': 'User not found', 'error_code': 'USER_NOT_FOUND'}, status=404)

        if getattr(user, 'status', '') != 'approved':
            return Response({'success': False, 'message': f'Account not approved ({user.status})', 'error_code': 'ACCOUNT_NOT_APPROVED'}, status=403)

        if not user.is_active:
            return Response({'success': False, 'message': 'Account inactive', 'error_code': 'ACCOUNT_INACTIVE'}, status=403)

        if user.family and getattr(user.family, 'status', '') != 'approved':
            return Response({'success': False, 'message': 'Family not approved', 'error_code': 'FAMILY_NOT_APPROVED'}, status=403)

        phone = getattr(user, 'phone', None)
        if not phone:
            return Response({'success': False, 'message': 'No phone number on record', 'error_code': 'NO_PHONE'}, status=500)

        send_resp = otp_service.send_otp(phone)
        if not send_resp.get('success', False):
            logger.error(f"Failed to send OTP for QR login to {phone}: {send_resp}")
            return Response({'success': False, 'message': 'Failed to send OTP', 'error_code': 'OTP_SEND_FAILED'}, status=500)

        return Response({'success': True, 'otp_sent': True, 'user_id': str(user.id), 'via': search_method}, status=200)

    except Exception as e:
        logger.exception(f"Unexpected QR login error: {e}")
        return Response({'success': False, 'message': 'Internal error', 'error_code': 'INTERNAL_ERROR'}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_verify_otp(request):
    """
    Verify OTP and issue token. Expects {user_id, otp}.
    Returns token and user data on success.
    """
    try:
        user_id = request.data.get('user_id')
        otp = request.data.get('otp')

        if not user_id or not otp:
            return Response({'success': False, 'message': 'user_id and otp required', 'error_code': 'MISSING_PARAMS'}, status=400)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({'success': False, 'message': 'User not found', 'error_code': 'USER_NOT_FOUND'}, status=404)

        phone = getattr(user, 'phone', None)
        if not phone:
            return Response({'success': False, 'message': 'No phone number on record', 'error_code': 'NO_PHONE'}, status=500)

        verify_resp = otp_service.verify_otp(phone, otp)
        if not verify_resp.get('success', False):
            logger.warning(f"OTP verify failed for user {user.username}: {verify_resp}")
            return Response({'success': False, 'message': 'OTP verification failed', 'error_code': 'OTP_VERIFY_FAILED'}, status=400)

        # OTP verified - generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        # Build user response with family info
        family = getattr(user, 'family', None)
        family_info = None
        if family:
            family_info = {
                'id': str(getattr(family, 'id', '')),
                'family_name': getattr(family, 'family_name', ''),
                'family_code': getattr(family, 'family_code', ''),
                'barangay': getattr(getattr(family, 'barangay', None), 'name', '')
            }

        response_data = {
            'success': True,
            'message': 'Login successful',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'token_type': 'Bearer',
            'expires_in': 3600,  # 1 hour in seconds
            'user_info': {
                'id': str(user.id),
                'username': user.username,
                'full_name': getattr(user, 'full_name', ''),
                'total_points': getattr(user, 'total_points', 0),
                'status': getattr(user, 'status', ''),
            },
            'family_info': family_info
        }

        logger.info(f"OTP login successful for user {user.username} - JWT tokens issued")
        return Response(response_data, status=200)

    except Exception as e:
        logger.exception(f"Error in OTP verification: {e}")
        return Response({'success': False, 'message': 'Internal error', 'error_code': 'INTERNAL_ERROR'}, status=500)


@api_view(['POST', 'GET'])  # Allow both POST and GET for browser compatibility
@authentication_classes([JWTAuthentication])
@permission_classes([])  # Allow unauthenticated requests (authentication is optional)
def logout_view(request):
    """
    Enhanced logout endpoint that handles JWT token blacklisting
    IMPORTANT: Authentication is optional - works both authenticated and unauthenticated
    - If authenticated: blacklists the refresh token
    - If unauthenticated: returns success (client-side token cleanup)
    """
    # Check if this is a browser request that should redirect
    is_browser_request = 'text/html' in request.META.get('HTTP_ACCEPT', '')
    
    # Check if user is authenticated
    is_authenticated = request.user and request.user.is_authenticated
    
    try:
        # If not authenticated, just return success for client-side cleanup
        if not is_authenticated:
            logger.info("Logout called without authentication - client-side cleanup")
            
            if is_browser_request:
                from django.shortcuts import redirect
                return redirect('login_page')
            
            return Response({
                'success': True,
                'message': 'Logged out successfully (client-side)',
                'redirect_url': '/accounts/login/',
                'note': 'No server-side session to clear'
            }, status=200)
        
        # Blacklist the refresh token to invalidate it (for authenticated users)
        refresh_token = request.data.get('refresh_token') or request.GET.get('refresh_token')
        
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info(f"JWT refresh token blacklisted for user {request.user.username}")
                
                if is_browser_request:
                    from django.shortcuts import redirect
                    return redirect('login_page')
                
                return Response({
                    'success': True,
                    'message': 'Logged out successfully',
                    'redirect_url': '/accounts/login/',
                }, status=200)
                
            except TokenError as e:
                logger.error(f"Error blacklisting token for {request.user.username}: {str(e)}")
                
                if is_browser_request:
                    from django.shortcuts import redirect
                    return redirect('login_page')
                
                return Response({
                    'success': False,
                    'message': 'Invalid or expired refresh token',
                    'error_code': 'INVALID_REFRESH_TOKEN'
                }, status=400)
        else:
            # No refresh token provided - just acknowledge logout
            logger.info(f"Logout without refresh token for user {request.user.username}")
            
            if is_browser_request:
                from django.shortcuts import redirect
                return redirect('login_page')
            
            return Response({
                'success': True,
                'message': 'Logged out successfully',
                'redirect_url': '/accounts/login/',
                'note': 'No refresh token provided for blacklisting'
            }, status=200)
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        
        if is_browser_request:
            from django.shortcuts import redirect
            return redirect('login_page')
            
        return Response({
            'success': False,
            'message': 'An error occurred during logout',
            'redirect_url': '/accounts/login/',
            'error_code': 'LOGOUT_ERROR',
            'error_details': str(e)
        }, status=500)
            
        return Response({
            'success': False,
            'message': 'An error occurred during logout',
            'redirect_url': '/accounts/login/',
            'error_code': 'LOGOUT_ERROR',
            'error_details': str(e)
        }, status=500)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def logout_debug(request):
    """
    Debug endpoint to check JWT authentication status
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', 'None')
    
    debug_info = {
        'method': request.method,
        'user': str(request.user),
        'user_authenticated': request.user.is_authenticated,
        'has_auth_attr': hasattr(request, 'auth'),
        'auth_value': str(getattr(request, 'auth', None)),
        'auth_header': auth_header[:50] + '...' if len(auth_header) > 50 else auth_header,
        'session_exists': bool(request.session.session_key),
        'csrf_token': request.META.get('HTTP_X_CSRFTOKEN', 'None')
    }
    
    return Response({
        'message': 'JWT authentication debug information',
        'debug_info': debug_info,
        'instructions': {
            'api_logout': 'POST /api/logout/ with Authorization: Bearer YOUR_ACCESS_TOKEN and refresh_token in body',
            'api_login': 'POST /api/login/ with username/password to get OTP',
            'verify_otp': 'POST /api/login/verify-otp/ with user_id and otp to get JWT tokens',
            'refresh_token': 'POST /api/refresh-token/ with refresh_token in body'
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """
    Refresh JWT tokens - returns new access token and refresh token
    """
    try:
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'success': False,
                'message': 'Refresh token is required',
                'error_code': 'MISSING_REFRESH_TOKEN'
            }, status=400)
        
        try:
            # Validate and refresh the token
            refresh = RefreshToken(refresh_token)
            
            # Get new tokens (old refresh token is blacklisted automatically due to ROTATE_REFRESH_TOKENS=True)
            new_access_token = str(refresh.access_token)
            new_refresh_token = str(refresh)
            
            logger.info(f"JWT tokens refreshed successfully")
            
            return Response({
                'success': True,
                'message': 'Tokens refreshed successfully',
                'access_token': new_access_token,
                'refresh_token': new_refresh_token,
                'token_type': 'Bearer',
                'expires_in': 3600,  # 1 hour
                'timestamp': timezone.now().isoformat()
            }, status=200)
            
        except TokenError as e:
            logger.error(f"Invalid or expired refresh token: {str(e)}")
            return Response({
                'success': False,
                'message': 'Invalid or expired refresh token',
                'error_code': 'INVALID_REFRESH_TOKEN'
            }, status=401)
        
    except Exception as e:
        logger.error(f"Error refreshing JWT token: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error refreshing token',
            'error_code': 'TOKEN_REFRESH_ERROR'
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def validate_token_view(request):
    """
    Validate if current JWT access token is still valid and return user info
    """
    try:
        user = request.user
        
        # Check if user can still access system
        if not user.can_access_system():
            return Response({
                'success': False,
                'message': 'Account access has been revoked',
                'error_code': 'ACCESS_REVOKED'
            }, status=403)
        
        return Response({
            'success': True,
            'message': 'JWT token is valid',
            'token_type': 'Bearer',
            'user_info': {
                'id': str(user.id),
                'username': user.username,
                'full_name': user.full_name,
                'total_points': user.total_points,
                'status': user.status,
                'last_login': user.last_login.isoformat() if user.last_login else None
            },
            'timestamp': timezone.now().isoformat()
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error validating JWT token: {str(e)}")
        return Response({
            'success': False,
            'message': 'Token validation error',
            'error_code': 'TOKEN_VALIDATION_ERROR'
        }, status=500)
