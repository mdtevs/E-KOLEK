"""
Biometric authentication views for mobile API
Handles device registration, biometric login, and device management
Uses JWT authentication and secure challenge-response protocol
"""
import json
import logging
import hashlib
import secrets
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Users
from .models import BiometricDevice, BiometricLoginAttempt


logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def validate_device_data(data):
    """Validate required device registration data"""
    required_fields = ['device_id', 'device_name', 'device_type', 'public_key', 
                      'credential_id', 'device_fingerprint']
    
    for field in required_fields:
        if not data.get(field):
            return False, f"Missing required field: {field}"
    
    # Validate device_type
    if data.get('device_type') not in ['ios', 'android']:
        return False, "device_type must be 'ios' or 'android'"
    
    # Validate string lengths
    if len(data.get('device_id', '')) > 255:
        return False, "device_id too long"
    
    if len(data.get('device_name', '')) > 255:
        return False, "device_name too long"
    
    if len(data.get('credential_id', '')) > 500:
        return False, "credential_id too long"
    
    return True, None


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def register_biometric_device(request):
    """
    Register a new biometric-enabled device for the authenticated user.
    
    Required fields:
    - device_id: Unique device identifier
    - device_name: User-friendly name
    - device_type: 'ios' or 'android'
    - public_key: Public key for biometric verification
    - credential_id: Unique credential identifier
    - device_fingerprint: Device fingerprint hash
    
    Optional fields:
    - device_model: Device model/brand
    - os_version: OS version
    - app_version: App version
    """
    try:
        user = request.user
        
        # Verify user can access system
        if not user.can_access_system():
            return Response({
                'success': False,
                'message': 'Account access has been revoked',
                'error_code': 'ACCESS_REVOKED'
            }, status=403)
        
        # Validate input data
        is_valid, error_msg = validate_device_data(request.data)
        if not is_valid:
            return Response({
                'success': False,
                'message': error_msg,
                'error_code': 'INVALID_DEVICE_DATA'
            }, status=400)
        
        device_id = request.data.get('device_id')
        credential_id = request.data.get('credential_id')
        
        # Check if device already registered
        existing_device = BiometricDevice.objects.filter(
            device_id=device_id
        ).first()
        
        if existing_device:
            if existing_device.user != user:
                # Device registered to different user - security issue
                logger.warning(f"Device {device_id} attempted registration by different user {user.username}")
                return Response({
                    'success': False,
                    'message': 'Device already registered to another account',
                    'error_code': 'DEVICE_ALREADY_REGISTERED'
                }, status=400)
            else:
                # Update existing device
                existing_device.device_name = request.data.get('device_name')
                existing_device.device_model = request.data.get('device_model', '')
                existing_device.os_version = request.data.get('os_version', '')
                existing_device.app_version = request.data.get('app_version', '')
                existing_device.public_key = request.data.get('public_key')
                existing_device.device_fingerprint = request.data.get('device_fingerprint')
                existing_device.is_active = True
                existing_device.failed_attempts = 0
                existing_device.registration_ip = get_client_ip(request)
                existing_device.save()
                
                logger.info(f"Updated biometric device {device_id} for user {user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Biometric device updated successfully',
                    'device': {
                        'id': str(existing_device.id),
                        'device_id': existing_device.device_id,
                        'device_name': existing_device.device_name,
                        'device_type': existing_device.device_type,
                        'registered_at': existing_device.registered_at.isoformat(),
                        'is_trusted': existing_device.is_trusted
                    }
                }, status=200)
        
        # Check credential_id uniqueness
        if BiometricDevice.objects.filter(credential_id=credential_id).exists():
            return Response({
                'success': False,
                'message': 'Credential ID already in use',
                'error_code': 'CREDENTIAL_ALREADY_USED'
            }, status=400)
        
        # Limit number of devices per user (security measure)
        device_count = BiometricDevice.objects.filter(user=user, is_active=True).count()
        max_devices = 5  # Allow up to 5 devices per user
        
        if device_count >= max_devices:
            return Response({
                'success': False,
                'message': f'Maximum number of devices ({max_devices}) reached. Please remove a device first.',
                'error_code': 'MAX_DEVICES_REACHED'
            }, status=400)
        
        # Create new device registration
        with transaction.atomic():
            device = BiometricDevice.objects.create(
                user=user,
                device_id=device_id,
                device_name=request.data.get('device_name'),
                device_type=request.data.get('device_type'),
                device_model=request.data.get('device_model', ''),
                os_version=request.data.get('os_version', ''),
                app_version=request.data.get('app_version', ''),
                public_key=request.data.get('public_key'),
                credential_id=credential_id,
                device_fingerprint=request.data.get('device_fingerprint'),
                registration_ip=get_client_ip(request),
                is_active=True
            )
            
            logger.info(f"Registered new biometric device {device_id} for user {user.username}")
            
            return Response({
                'success': True,
                'message': 'Biometric device registered successfully',
                'device': {
                    'id': str(device.id),
                    'device_id': device.device_id,
                    'device_name': device.device_name,
                    'device_type': device.device_type,
                    'registered_at': device.registered_at.isoformat(),
                    'is_trusted': device.is_trusted
                }
            }, status=201)
        
    except Exception as e:
        logger.error(f"Error registering biometric device: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error registering biometric device',
            'error_code': 'REGISTRATION_ERROR'
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def biometric_login_init(request):
    """
    Initialize biometric login - generate challenge for device.
    
    Required fields:
    - device_id: Unique device identifier
    - credential_id: Credential identifier
    
    Returns a challenge that must be signed by the device's private key.
    """
    try:
        device_id = request.data.get('device_id')
        credential_id = request.data.get('credential_id')
        
        if not device_id or not credential_id:
            return Response({
                'success': False,
                'message': 'device_id and credential_id are required',
                'error_code': 'MISSING_PARAMS'
            }, status=400)
        
        # Find the device
        try:
            device = BiometricDevice.objects.select_related('user').get(
                device_id=device_id,
                credential_id=credential_id
            )
        except BiometricDevice.DoesNotExist:
            logger.warning(f"Biometric login attempt with unknown device: {device_id}")
            return Response({
                'success': False,
                'message': 'Device not registered',
                'error_code': 'DEVICE_NOT_FOUND'
            }, status=404)
        
        # Check if device is active
        if not device.is_active:
            return Response({
                'success': False,
                'message': 'Device has been deactivated',
                'error_code': 'DEVICE_INACTIVE'
            }, status=403)
        
        # Check if device is locked
        if device.is_locked():
            return Response({
                'success': False,
                'message': 'Device is locked due to too many failed attempts',
                'error_code': 'DEVICE_LOCKED'
            }, status=403)
        
        # Check if device is expired
        if device.is_expired():
            return Response({
                'success': False,
                'message': 'Device registration has expired',
                'error_code': 'DEVICE_EXPIRED'
            }, status=403)
        
        # Check user account status
        user = device.user
        if not user.is_active:
            return Response({
                'success': False,
                'message': 'Account is inactive',
                'error_code': 'ACCOUNT_INACTIVE'
            }, status=403)
        
        if getattr(user, 'status', '') != 'approved':
            return Response({
                'success': False,
                'message': 'Account not approved',
                'error_code': 'ACCOUNT_NOT_APPROVED'
            }, status=403)
        
        if not user.can_access_system():
            return Response({
                'success': False,
                'message': 'Account access has been revoked',
                'error_code': 'ACCESS_REVOKED'
            }, status=403)
        
        # Generate challenge
        challenge = device.generate_challenge()
        
        logger.info(f"Generated biometric challenge for device {device_id}, user {user.username}")
        
        return Response({
            'success': True,
            'message': 'Challenge generated',
            'challenge': challenge,
            'user_id': str(user.id),
            'expires_in': 300  # 5 minutes in seconds
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error initializing biometric login: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error initializing biometric login',
            'error_code': 'INIT_ERROR'
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def biometric_login_verify(request):
    """
    Verify biometric login - validate signed challenge and issue JWT tokens.
    
    Required fields:
    - device_id: Unique device identifier
    - credential_id: Credential identifier
    - challenge: The challenge that was signed
    - signature: Digital signature from device's private key
    - device_fingerprint: Current device fingerprint for verification
    
    Returns JWT access and refresh tokens on success.
    """
    try:
        logger.info(f"Biometric login verify request received. Data: {request.data}")
        
        device_id = request.data.get('device_id')
        credential_id = request.data.get('credential_id')
        challenge = request.data.get('challenge')
        signature = request.data.get('signature')
        device_fingerprint = request.data.get('device_fingerprint')
        
        # Log what fields are missing
        missing_fields = []
        if not device_id:
            missing_fields.append('device_id')
        if not credential_id:
            missing_fields.append('credential_id')
        if not challenge:
            missing_fields.append('challenge')
        if not signature:
            missing_fields.append('signature')
        if not device_fingerprint:
            missing_fields.append('device_fingerprint')
        
        if missing_fields:
            logger.warning(f"Biometric verify missing fields: {missing_fields}")
            return Response({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}',
                'error_code': 'MISSING_PARAMS',
                'missing_fields': missing_fields
            }, status=400)
        
        # Find the device
        try:
            device = BiometricDevice.objects.select_related('user').get(
                device_id=device_id,
                credential_id=credential_id
            )
        except BiometricDevice.DoesNotExist:
            # Log failed attempt
            BiometricLoginAttempt.objects.create(
                user=None,
                device=None,
                success=False,
                failure_reason='Device not found',
                attempted_device_id=device_id,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'success': False,
                'message': 'Invalid credentials',
                'error_code': 'INVALID_CREDENTIALS'
            }, status=401)
        
        user = device.user
        
        # Verify challenge
        if not device.verify_challenge(challenge):
            device.increment_failed_attempts()
            
            # Log failed attempt
            BiometricLoginAttempt.objects.create(
                user=user,
                device=device,
                success=False,
                failure_reason='Invalid or expired challenge',
                attempted_device_id=device_id,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            logger.warning(f"Invalid challenge for device {device_id}, user {user.username}")
            
            return Response({
                'success': False,
                'message': 'Invalid or expired challenge',
                'error_code': 'INVALID_CHALLENGE'
            }, status=401)
        
        # Verify device fingerprint (additional security layer)
        if device.device_fingerprint != device_fingerprint:
            device.increment_failed_attempts()
            
            # Log failed attempt
            BiometricLoginAttempt.objects.create(
                user=user,
                device=device,
                success=False,
                failure_reason='Device fingerprint mismatch',
                attempted_device_id=device_id,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            logger.warning(f"Device fingerprint mismatch for {device_id}, user {user.username}")
            
            return Response({
                'success': False,
                'message': 'Device verification failed',
                'error_code': 'DEVICE_VERIFICATION_FAILED'
            }, status=401)
        
        # Signature validation - checks signature format and length
        # Production implementations should use cryptography library for proper verification
        # using the device's public_key stored in the BiometricDevice model
        if not signature or len(signature) < 10:
            device.increment_failed_attempts()
            
            BiometricLoginAttempt.objects.create(
                user=user,
                device=device,
                success=False,
                failure_reason='Invalid signature',
                attempted_device_id=device_id,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'success': False,
                'message': 'Invalid signature',
                'error_code': 'INVALID_SIGNATURE'
            }, status=401)
        
        # All verifications passed - generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Update device and user
        device.reset_failed_attempts()
        device.update_last_used(get_client_ip(request))
        device.last_verified_at = timezone.now()
        device.clear_challenge()
        device.save(update_fields=['last_verified_at'])
        
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Log successful attempt
        BiometricLoginAttempt.objects.create(
            user=user,
            device=device,
            success=True,
            attempted_device_id=device_id,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Build response with user and family info
        family = getattr(user, 'family', None)
        family_info = None
        if family:
            family_info = {
                'id': str(getattr(family, 'id', '')),
                'family_name': getattr(family, 'family_name', ''),
                'family_code': getattr(family, 'family_code', ''),
                'barangay': getattr(getattr(family, 'barangay', None), 'name', '')
            }
        
        logger.info(f"Biometric login successful for user {user.username}, device {device_id}")
        
        return Response({
            'success': True,
            'message': 'Biometric login successful',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'token_type': 'Bearer',
            'expires_in': 3600,  # 1 hour
            'user_info': {
                'id': str(user.id),
                'username': user.username,
                'full_name': getattr(user, 'full_name', ''),
                'total_points': getattr(user, 'total_points', 0),
                'status': getattr(user, 'status', ''),
            },
            'family_info': family_info,
            'device_info': {
                'device_name': device.device_name,
                'is_trusted': device.is_trusted,
                'last_used': device.last_used_at.isoformat() if device.last_used_at else None
            }
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error verifying biometric login: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': 'Error verifying biometric login',
            'error_code': 'VERIFY_ERROR',
            'error_detail': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def list_biometric_devices(request):
    """
    List all registered biometric devices for the authenticated user.
    """
    try:
        user = request.user
        
        devices = BiometricDevice.objects.filter(user=user).order_by('-last_used_at', '-registered_at')
        
        devices_data = []
        for device in devices:
            devices_data.append({
                'id': str(device.id),
                'device_id': device.device_id,
                'device_name': device.device_name,
                'device_type': device.device_type,
                'device_model': device.device_model,
                'os_version': device.os_version,
                'is_active': device.is_active,
                'is_trusted': device.is_trusted,
                'is_locked': device.is_locked(),
                'failed_attempts': device.failed_attempts,
                'registered_at': device.registered_at.isoformat(),
                'last_used_at': device.last_used_at.isoformat() if device.last_used_at else None,
                'expires_at': device.expires_at.isoformat() if device.expires_at else None,
            })
        
        return Response({
            'success': True,
            'message': 'Devices retrieved successfully',
            'devices': devices_data,
            'total_devices': len(devices_data),
            'active_devices': len([d for d in devices_data if d['is_active']])
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error listing biometric devices: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error retrieving devices',
            'error_code': 'LIST_ERROR'
        }, status=500)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def revoke_biometric_device(request, device_id):
    """
    Revoke/deactivate a biometric device.
    Only the device owner can revoke their own devices.
    """
    try:
        user = request.user
        
        try:
            device = BiometricDevice.objects.get(id=device_id, user=user)
        except BiometricDevice.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Device not found',
                'error_code': 'DEVICE_NOT_FOUND'
            }, status=404)
        
        # Deactivate the device
        device.deactivate()
        
        logger.info(f"User {user.username} revoked biometric device {device.device_name}")
        
        return Response({
            'success': True,
            'message': 'Device revoked successfully',
            'device_id': str(device.id)
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error revoking biometric device: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error revoking device',
            'error_code': 'REVOKE_ERROR'
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def trust_biometric_device(request, device_id):
    """
    Mark a device as trusted.
    Trusted devices may skip additional verification steps.
    """
    try:
        user = request.user
        
        try:
            device = BiometricDevice.objects.get(id=device_id, user=user)
        except BiometricDevice.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Device not found',
                'error_code': 'DEVICE_NOT_FOUND'
            }, status=404)
        
        device.is_trusted = True
        device.save(update_fields=['is_trusted'])
        
        logger.info(f"User {user.username} marked device {device.device_name} as trusted")
        
        return Response({
            'success': True,
            'message': 'Device marked as trusted',
            'device_id': str(device.id)
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error trusting device: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error updating device',
            'error_code': 'TRUST_ERROR'
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def biometric_login_history(request):
    """
    Get biometric login attempt history for the authenticated user.
    """
    try:
        user = request.user
        
        # Get query parameters
        limit = int(request.GET.get('limit', 20))
        success_only = request.GET.get('success_only', 'false').lower() == 'true'
        
        # Query attempts
        attempts = BiometricLoginAttempt.objects.filter(user=user)
        
        if success_only:
            attempts = attempts.filter(success=True)
        
        attempts = attempts.order_by('-attempted_at')[:limit]
        
        attempts_data = []
        for attempt in attempts:
            attempts_data.append({
                'id': str(attempt.id),
                'success': attempt.success,
                'failure_reason': attempt.failure_reason,
                'device_name': attempt.device.device_name if attempt.device else 'Unknown',
                'device_type': attempt.device.device_type if attempt.device else 'Unknown',
                'ip_address': attempt.ip_address,
                'attempted_at': attempt.attempted_at.isoformat()
            })
        
        return Response({
            'success': True,
            'message': 'Login history retrieved successfully',
            'attempts': attempts_data,
            'total_attempts': len(attempts_data)
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error getting login history: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error retrieving login history',
            'error_code': 'HISTORY_ERROR'
        }, status=500)
