import json
import logging
import re
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
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
            error_type = verify_resp.get('error_type', 'unknown')
            error_message = verify_resp.get('error', 'OTP verification failed')
            
            # Provide more specific error messages to mobile app
            if error_type == 'otp_not_found':
                error_message = 'OTP has expired or was already used. Please request a new code.'
            elif error_type == 'invalid_otp':
                error_message = 'Invalid OTP code. Please check and try again.'
            elif error_type == 'too_many_attempts':
                error_message = 'Too many failed attempts. Please request a new code.'
            elif error_type == 'otp_expired':
                error_message = 'OTP has expired. Please request a new code.'
            
            logger.warning(f"OTP verify failed for user {user.username}: {verify_resp}")
            return Response({
                'success': False, 
                'message': error_message,
                'error_code': 'OTP_VERIFY_FAILED',
                'error_type': error_type
            }, status=400)

        # OTP verified - check if this was already verified recently
        already_verified = verify_resp.get('already_verified', False)
        
        # Get or create token (don't rotate if already verified to avoid issues)
        if already_verified:
            # OTP was recently verified - return existing token if available
            token, created = Token.objects.get_or_create(user=user)
            if created:
                logger.info(f"Created new token for recently verified user {user.username}")
            else:
                logger.info(f"Returning existing token for recently verified user {user.username}")
        else:
            # Fresh verification - rotate token: delete existing and create new
            try:
                Token.objects.filter(user=user).delete()
            except Exception:
                logger.exception("Failed to delete existing tokens before issuing new one")
            
            token = Token.objects.create(user=user)
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

        # Build user response similar to previous implementation
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
            'token': token.key,
            'user_info': {
                'id': str(user.id),
                'username': user.username,
                'full_name': getattr(user, 'full_name', ''),
                'total_points': getattr(user, 'total_points', 0),
                'status': getattr(user, 'status', ''),
            },
            'family_info': family_info
        }

        logger.info(f"OTP login successful for user {user.username}")
        return Response(response_data, status=200)

    except Exception as e:
        logger.exception(f"Error in OTP verification: {e}")
        return Response({'success': False, 'message': 'Internal error', 'error_code': 'INTERNAL_ERROR'}, status=500)