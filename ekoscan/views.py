from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from functools import wraps
import json
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from accounts.models import (
    Users, Family, WasteType, WasteTransaction, 
    PointsTransaction, Reward, Redemption, RewardHistory
)
from cenro.models import AdminUser

# Import JWT utilities for admin authentication
from .jwt_utils import (
    AdminJWTAuthentication, 
    AdminRefreshToken,
    create_admin_tokens,
    refresh_admin_token
)
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

logger = logging.getLogger(__name__)

# ============================================================================
# RATE LIMITING FOR ADMIN LOGIN
# ============================================================================

# Rate limiting storage (IP-based)
LOGIN_ATTEMPTS = {}  # {ip_address: {'count': int, 'last_attempt': datetime}}

def check_rate_limit(request, max_attempts=10, window_minutes=15):
    """Check if IP is rate limited for login attempts"""
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', 
                               request.META.get('REMOTE_ADDR', '127.0.0.1'))
    
    if client_ip in LOGIN_ATTEMPTS:
        attempt_data = LOGIN_ATTEMPTS[client_ip]
        time_diff = datetime.now() - attempt_data['last_attempt']
        
        # Reset counter if window expired
        if time_diff.total_seconds() > (window_minutes * 60):
            LOGIN_ATTEMPTS[client_ip] = {'count': 1, 'last_attempt': datetime.now()}
            return True
        
        # Check if over limit
        if attempt_data['count'] >= max_attempts:
            logger.warning(f"Rate limit exceeded for IP {client_ip}")
            return False
        
        # Increment counter
        LOGIN_ATTEMPTS[client_ip]['count'] += 1
        LOGIN_ATTEMPTS[client_ip]['last_attempt'] = datetime.now()
    else:
        LOGIN_ATTEMPTS[client_ip] = {'count': 1, 'last_attempt': datetime.now()}
    
    return True

# ============================================================================
# JWT-BASED ADMIN AUTHENTICATION DECORATOR
# ============================================================================

def admin_jwt_required(view_func):
    """
    Decorator to check admin JWT authentication for ekoscan mobile app
    Compatible with both DRF and regular Django views
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        logger.info(f"=== ADMIN JWT AUTH for {view_func.__name__} ===")
        logger.info(f"Auth header present: {bool(auth_header)}, Length: {len(auth_header) if auth_header else 0}")
        
        if not auth_header:
            logger.warning(f"Missing Authorization header")
            return Response({
                'success': False,
                'error': 'Authentication required. Please login again.',
                'error_code': 'AUTH_REQUIRED',
                'requires_login': True
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not auth_header.startswith('Bearer '):
            logger.warning(f"Invalid auth header format: {auth_header[:20]}")
            return Response({
                'success': False,
                'error': 'Invalid authorization format. Please login again.',
                'error_code': 'INVALID_AUTH_FORMAT',
                'requires_login': True
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token = auth_header.split(' ')[1]
        
        # Validate JWT token using AdminJWTAuthentication
        auth = AdminJWTAuthentication()
        
        try:
            # Validate the token
            validated_token = auth.get_validated_token(token)
            admin_user = auth.get_user(validated_token)
            
            # Check if admin is active
            if not admin_user.is_active:
                logger.warning(f"Inactive admin tried to authenticate: {admin_user.username}")
                return Response({
                    'success': False,
                    'error': 'Admin account is inactive',
                    'error_code': 'ACCOUNT_INACTIVE'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if admin has mobile access (super_admin or operations_manager only)
            if admin_user.role not in ['super_admin', 'operations_manager']:
                logger.warning(f"Unauthorized role tried to access mobile API: {admin_user.role}")
                return Response({
                    'success': False,
                    'error': 'Access denied. Only super admins and operations managers can use this app.',
                    'error_code': 'INSUFFICIENT_PERMISSIONS'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if account is locked
            if admin_user.account_locked_until and admin_user.account_locked_until > timezone.now():
                logger.warning(f"Locked admin tried to authenticate: {admin_user.username}")
                return Response({
                    'success': False,
                    'error': f'Account is locked until {admin_user.account_locked_until.strftime("%Y-%m-%d %H:%M")}',
                    'error_code': 'ACCOUNT_LOCKED'
                }, status=status.HTTP_423_LOCKED)
            
            # Attach admin user to request
            request.admin_user = admin_user
            logger.info(f"Admin JWT authenticated: {admin_user.username}")
            
            return view_func(request, *args, **kwargs)
            
        except InvalidToken as e:
            logger.error(f"Invalid JWT token: {str(e)}")
            return Response({
                'success': False,
                'error': 'Your session has expired. Please login again.',
                'error_code': 'TOKEN_EXPIRED',
                'requires_login': True
            }, status=status.HTTP_401_UNAUTHORIZED)
        except TokenError as e:
            logger.error(f"Token error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Authentication error. Please login again.',
                'error_code': 'TOKEN_ERROR',
                'requires_login': True
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Unexpected auth error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Authentication failed. Please login again.',
                'error_code': 'AUTH_FAILED',
                'requires_login': True
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    return wrapper

# Old custom token decorator removed - using JWT authentication only

# ============================================================================
# ADMIN AUTHENTICATION FOR MOBILE (Super Admin & Operations Manager Only)
# ============================================================================

@csrf_exempt
def admin_mobile_login(request):
    """Admin mobile login endpoint - only for super_admin and operations_manager"""
    logger.info(f"=== ADMIN LOGIN ENDPOINT HIT ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"Path: {request.path}")
    logger.info(f"Content-Type: {request.content_type}")
    
    if request.method != 'POST':
        logger.warning(f"Invalid method: {request.method}")
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Check rate limiting first
        if not check_rate_limit(request):
            return JsonResponse({
                'success': False,
                'error': 'Too many login attempts. Please try again later.',
                'debug': 'Rate limit exceeded'
            }, status=429)
        
        # Enhanced security logging
        client_ip = request.META.get('HTTP_X_FORWARDED_FOR', 
                                   request.META.get('REMOTE_ADDR', '127.0.0.1'))
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        logger.info(f"=== ADMIN LOGIN REQUEST from {client_ip} ===")
        logger.info(f"User-Agent: {user_agent}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Request body length: {len(request.body) if request.body else 0}")
        
        # Parse JSON data
        try:
            if not request.body:
                logger.warning("Empty request body received")
                return JsonResponse({
                    'success': False,
                    'error': 'Request body is empty. Please send JSON data with username and password.',
                    'debug': 'Empty request body'
                }, status=400)
            
            data = json.loads(request.body.decode('utf-8'))
            logger.info(f"Parsed JSON data keys: {list(data.keys()) if data else 'None'}")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Raw request body: {request.body[:200]}...")  # Log first 200 chars
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data. Please check your request format.',
                'debug': f'JSON decode error: {str(e)}'
            }, status=400)
        
        username = data.get('username')
        password = data.get('password')
        
        logger.info(f"Username provided: {'Yes' if username else 'No'}")
        logger.info(f"Password provided: {'Yes' if password else 'No'}")
        logger.info(f"Username value: {username if username else 'None'}")
        logger.info(f"Full data received: {data}")
        
        if not username or not password:
            missing_fields = []
            if not username:
                missing_fields.append('username')
            if not password:
                missing_fields.append('password')
            
            logger.info(f"Missing required fields: {missing_fields} (normal validation)")
            return JsonResponse({
                'success': False,
                'error': 'Username and password are required',
                'debug': f'Missing fields: {", ".join(missing_fields)}'
            }, status=400)
        
        # Authenticate admin user
        try:
            admin_user = AdminUser.objects.get(username=username, is_active=True, status='approved')
            
            # Check if admin has permission for mobile operations
            if admin_user.role not in ['super_admin', 'operations_manager']:
                # Log unauthorized access attempt
                logger.warning(f"Unauthorized mobile access attempt by {username} with role {admin_user.role}")
                return JsonResponse({
                    'success': False,
                    'error': 'Access denied. Only super admins and operations managers can use this app.'
                }, status=403)
            
            # Verify password
            if admin_user.check_password(password):
                # Check if account is locked
                if admin_user.account_locked_until and admin_user.account_locked_until > timezone.now():
                    return JsonResponse({
                        'success': False,
                        'error': f'Account is locked until {admin_user.account_locked_until.strftime("%Y-%m-%d %H:%M")}'
                    }, status=423)
                
                # Check if password needs to be changed
                if admin_user.must_change_password:
                    return JsonResponse({
                        'success': False,
                        'error': 'Password must be changed before using the mobile app. Please login via web admin panel first.'
                    }, status=403)
                
                # ========================================
                # JWT TOKEN GENERATION (NEW)
                # ========================================
                # Generate JWT tokens for admin
                try:
                    token_data = create_admin_tokens(admin_user)
                except Exception as token_error:
                    logger.error(f"Failed to create JWT tokens: {str(token_error)}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Token generation failed'
                    }, status=500)
                
                # Reset failed login attempts and update last login
                admin_user.failed_login_attempts = 0
                admin_user.last_login = timezone.now()
                admin_user.save()
                
                # Clear rate limit for successful login
                if client_ip in LOGIN_ATTEMPTS:
                    del LOGIN_ATTEMPTS[client_ip]
                
                # Log successful login
                from cenro.admin_utils import log_admin_action
                log_admin_action(admin_user, None, 'mobile_login', f'Admin logged in via mobile app from {client_ip}', request)
                
                logger.info(f"JWT login successful for admin: {admin_user.username}")
                return JsonResponse(token_data, status=200)
            else:
                # Increment failed login attempts
                admin_user.failed_login_attempts += 1
                
                # Lock account after 5 failed attempts
                if admin_user.failed_login_attempts >= 5:
                    admin_user.account_locked_until = timezone.now() + timezone.timedelta(minutes=30)
                    admin_user.save()
                    
                    # Log account lockout
                    from cenro.admin_utils import log_admin_action
                    log_admin_action(admin_user, None, 'account_locked', f'Account locked due to failed login attempts from {client_ip}', request)
                    
                    return JsonResponse({
                        'success': False,
                        'error': 'Account has been locked due to multiple failed login attempts. Please try again in 30 minutes.'
                    }, status=423)
                else:
                    admin_user.save()
                    remaining_attempts = 5 - admin_user.failed_login_attempts
                    logger.warning(f"Failed login attempt for {username} from {client_ip}. {remaining_attempts} attempts remaining.")
                    return JsonResponse({
                        'success': False,
                        'error': f'Invalid credentials. {remaining_attempts} attempts remaining before account lockout.'
                    }, status=401)
                    
        except AdminUser.DoesNotExist:
            logger.warning(f"Login attempt with non-existent username: {username} from {client_ip}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid credentials'
            }, status=401)
            
    except Exception as e:
        logger.error(f"Admin mobile login error: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Check if this is the "You cannot access body after reading from request's data stream" error
        if "cannot access body after reading" in str(e).lower():
            return JsonResponse({
                'success': False,
                'error': 'Invalid request format. Please send JSON data, not form data.',
                'debug': 'Request body was already read. Use Content-Type: application/json'
            }, status=400)
        
        return JsonResponse({
            'success': False,
            'error': 'Login failed',
            'debug': f'Server error: {str(e)}'
        }, status=500)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def admin_mobile_logout(request):
    """
    Admin mobile logout endpoint with JWT blacklisting
    Does not require valid token - accepts refresh token for blacklisting
    """
    try:
        # Try to get admin info from token if available (for logging)
        admin_username = None
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                auth = AdminJWTAuthentication()
                validated_token = auth.get_validated_token(token)
                admin_user = auth.get_user(validated_token)
                admin_username = admin_user.username
            except:
                # Token might be invalid, that's okay for logout
                pass
        
        # Blacklist the refresh token
        refresh_token_str = request.data.get('refresh_token')
        
        if refresh_token_str:
            try:
                refresh = AdminRefreshToken(refresh_token_str)
                refresh.blacklist()
                logger.info(f"Refresh token blacklisted for admin {admin_username or 'unknown'}")
            except TokenError as e:
                # Token might already be blacklisted, log but don't fail
                logger.warning(f"Token already blacklisted or invalid: {str(e)}")
                # Continue with logout even if blacklisting fails
        
        # Log logout if we have admin info
        if admin_username:
            try:
                from cenro.admin_utils import log_admin_action
                from cenro.models import AdminUser
                admin = AdminUser.objects.get(username=admin_username)
                log_admin_action(admin, None, 'mobile_logout', 'Admin logged out from mobile app', request)
            except:
                pass
        
        return Response({
            'success': True,
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Admin mobile logout error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Logout failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_refresh_token(request):
    """Refresh admin JWT tokens"""
    try:
        refresh_token_str = request.data.get('refresh_token')
        
        if not refresh_token_str:
            return Response({
                'success': False,
                'error': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token_data = refresh_admin_token(refresh_token_str)
            logger.info("Admin JWT tokens refreshed successfully")
            return Response(token_data, status=status.HTTP_200_OK)
            
        except TokenError as e:
            logger.error(f"Invalid refresh token: {str(e)}")
            return Response({
                'success': False,
                'error': 'Invalid or expired refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
    except Exception as e:
        logger.error(f"Error refreshing admin JWT token: {str(e)}")
        return Response({
            'success': False,
            'error': 'Token refresh failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
def debug_token(request):
    """Debug endpoint - DEPRECATED (JWT doesn't use custom token storage)"""
    return JsonResponse({
        'deprecated': True,
        'message': 'This endpoint is deprecated. JWT authentication is now used.',
        'suggestion': 'Use /ekoscan/api/admin/refresh-token/ to refresh JWT tokens'
    }, status=410)


# ============================================================================
# MOBILE API ENDPOINTS FOR ADMIN USE (Super Admin & Operations Manager)
# ============================================================================

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_jwt_required
def get_admin_profile(request):
    """Get current admin profile for mobile app"""
    try:
        admin = request.admin_user
        
        admin_data = {
            'id': admin.id,
            'username': admin.username,
            'full_name': admin.full_name,
            'role': admin.role,
            'role_display': admin.get_role_display(),
            'permissions': {
                'can_manage_users': admin.can_manage_users,
                'can_manage_points': admin.can_manage_points,
                'can_manage_rewards': admin.can_manage_rewards,
                'can_manage_schedules': admin.can_manage_schedules,
            },
            'assigned_barangays': list(admin.assigned_barangays.values('id', 'name')) if admin.role == 'operations_manager' else None,
            'last_login': admin.last_login.isoformat() if admin.last_login else None,
        }
        
        return Response({
            'success': True,
            'admin': admin_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting admin profile: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get admin profile'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_jwt_required
def get_user_by_qr(request):
    """Get user information by QR code scan (user ID) - Admin only"""
    try:
        logger.info(f"Scan user endpoint called by admin: {request.admin_user.username}")
        
        user_id = request.GET.get('user_id')
        logger.info(f"Received user_id: {user_id}")
        
        if not user_id:
            logger.warning("No user_id provided in request")
            return Response({
                'success': False,
                'error': 'User ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Looking up user with ID: {user_id}")
        try:
            user = Users.objects.get(id=user_id, status='approved', is_active=True)
            logger.info(f"User found: {user.full_name} ({user.username})")
        except Users.DoesNotExist:
            logger.error(f"User not found with ID: {user_id}")
            return Response({
                'success': False,
                'error': 'User not found or not approved'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if operations manager can access this user's barangay
        admin = request.admin_user
        logger.info(f"Admin role: {admin.role}")
        
        if admin.role == 'operations_manager':
            if user.family and user.family.barangay:
                if not admin.assigned_barangays.filter(id=user.family.barangay.id).exists():
                    logger.warning(f"Operations manager {admin.username} denied access to user from barangay {user.family.barangay.name}")
                    return Response({
                        'success': False,
                        'error': 'You do not have permission to access users from this barangay'
                    }, status=status.HTTP_403_FORBIDDEN)
        
        # Build the display name - use full_name if available, otherwise combine first_name and last_name
        display_name = user.full_name
        if not display_name and user.first_name:
            display_name = f"{user.first_name} {user.last_name}".strip()
        
        # Build user data response
        user_data = {
            'id': str(user.id),  # Ensure UUID is converted to string
            'name': display_name or '',
            'username': user.username,
            'current_points': user.total_points,  # Use total_points field
            'family_code': user.family.family_code if user.family else '',
            'family_name': user.family.family_name if user.family else '',
            'barangay': user.family.barangay.name if user.family and user.family.barangay else None,
            'phone': user.phone,
            'is_family_representative': user.is_family_representative
        }
        
        logger.info(f"Returning user data for: {display_name}")
        return Response({
            'success': True,
            'user': user_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting user by QR: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': 'Failed to get user information',
            'debug_error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_jwt_required
def get_waste_types(request):
    """Get all active waste types for mobile app - Admin only"""
    try:
        logger.info(f"Getting waste types for admin: {request.admin_user.username}")
        
        # Check if WasteType model exists and get count
        total_waste_types = WasteType.objects.count()
        logger.info(f"Total waste types: {total_waste_types}")
        
        # Get all waste types (no is_active field exists in this model)
        waste_types = WasteType.objects.values(
            'id', 'name', 'points_per_kg'
        ).order_by('name')
        
        waste_types_list = list(waste_types)
        logger.info(f"Retrieved {len(waste_types_list)} waste types")
        
        return Response({
            'success': True,
            'waste_types': waste_types_list,
            'count': len(waste_types_list)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting waste types: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': 'Failed to get waste types',
            'debug_error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_jwt_required
def create_waste_transaction(request):
    """Create a new waste transaction (admin mobile version)"""
    try:
        data = request.data
        admin = request.admin_user
        
        # Get user from QR scan
        user_id = data.get('user_id')
        if not user_id:
            return Response({
                'success': False,
                'error': 'User ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = get_object_or_404(Users, id=user_id, status='approved', is_active=True)
        
        # Check if operations manager can access this user's barangay
        if admin.role == 'operations_manager':
            if user.family and user.family.barangay:
                if not admin.assigned_barangays.filter(id=user.family.barangay.id).exists():
                    return Response({
                        'success': False,
                        'error': 'You do not have permission to process transactions for users from this barangay'
                    }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate required fields
        waste_type_id = data.get('waste_type_id')
        weight_kg = data.get('weight_kg')
        
        if not waste_type_id or not weight_kg:
            return Response({
                'success': False,
                'error': 'Waste type and weight are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            weight_kg = Decimal(str(weight_kg))
            if weight_kg <= 0:
                raise ValueError("Weight must be positive")
        except (ValueError, InvalidOperation):
            return Response({
                'success': False,
                'error': 'Invalid weight value'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        waste_type = get_object_or_404(WasteType, id=waste_type_id)
        
        # Calculate points (keep as Decimal for database operations)
        points_earned = weight_kg * waste_type.points_per_kg
        
        # Create transaction
        with transaction.atomic():
            # Create waste transaction (using correct field names from model)
            waste_transaction = WasteTransaction.objects.create(
                user=user,
                waste_type=waste_type,
                waste_kg=weight_kg,  # Field name is waste_kg, not weight_kg
                total_points=points_earned,  # Field name is total_points, not points_earned
                processed_by=admin,  # Track which admin processed this
                barangay=user.family.barangay if user.family else None,  # Auto-populate from family
                # Note: created_at and transaction_date are auto-generated
            )
            
            # Create points transaction (using correct field names)
            points_transaction = PointsTransaction.objects.create(
                user=user,
                transaction_type='earned',
                points_amount=points_earned,  # Field name is points_amount, not points
                description=f"Waste collection: {weight_kg}kg {waste_type.name}",
                processed_by=admin,  # Track which admin processed this
                # transaction_date and created_at are auto-generated
            )
            
            # Update user's total points (correct field name)
            user.total_points += points_earned
            user.save()
            
            # Update family points if user has a family
            if user.family:
                user.family.total_family_points += points_earned
                user.family.save(update_fields=['total_family_points'])
            
            # Create notification for user dashboard
            try:
                from accounts.models import Notification
                notification = Notification.objects.create(
                    user=user,
                    type='waste',
                    message=f'You earned {int(points_earned)} points from waste collection! ({weight_kg}kg of {waste_type.name} processed by {admin.full_name})',
                    points=int(points_earned)
                )
                logger.info(f"Notification created for user {user.username}: {notification.message}")
            except Exception as notif_error:
                logger.warning(f"Failed to create notification: {str(notif_error)}")
                # Don't fail the transaction for notification issues
        
        # Log admin action
        from cenro.admin_utils import log_admin_action
        log_admin_action(
            admin, None, 'waste_transaction', 
            f"Created waste transaction for {user.full_name}: {weight_kg}kg {waste_type.name} (+{points_earned} points)",
            request
        )
        
        return Response({
            'success': True,
            'transaction': {
                'id': waste_transaction.id,
                'user_name': user.full_name,
                'waste_type': waste_type.name,
                'weight_kg': float(weight_kg),
                'points_earned': float(points_earned),
                'timestamp': waste_transaction.created_at.isoformat(),  # Use created_at
                'processed_by': admin.full_name
            },
            'user_new_points': float(user.total_points)  # Convert Decimal to float for JSON
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating waste transaction: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create waste transaction'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_jwt_required
def get_available_rewards(request):
    """Get all available rewards for mobile app - Admin only"""
    try:
        logger.info(f"Getting rewards for admin: {request.admin_user.username}")
        
        # Check if Reward model exists and get count
        total_rewards = Reward.objects.count()
        logger.info(f"Total rewards: {total_rewards}")
        
        # First, let's try a simple query to see what fields exist
        try:
            # Get all rewards without filtering first to see what's available
            all_rewards = Reward.objects.values(
                'id', 'name', 'points_required'
            ).order_by('points_required')
            
            logger.info(f"Basic rewards query successful, found {len(all_rewards)} rewards")
            
            # Now try with additional fields
            rewards = Reward.objects.filter(
                is_active=True,
                stock__gt=0
            ).values(
                'id', 'name', 'description', 'points_required', 
                'stock', 'image'
            ).order_by('points_required')
            
            rewards_list = list(rewards)
            logger.info(f"Retrieved {len(rewards_list)} active rewards with stock")
            
        except Exception as field_error:
            logger.error(f"Error with field query: {str(field_error)}")
            # Fallback to basic fields only
            rewards = Reward.objects.values(
                'id', 'name', 'points_required'
            ).order_by('points_required')
            
            rewards_list = list(rewards)
            logger.info(f"Using fallback query, retrieved {len(rewards_list)} rewards")
        
        return Response({
            'success': True,
            'rewards': rewards_list,
            'count': len(rewards_list)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting rewards: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': 'Failed to get rewards',
            'debug_error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_jwt_required
def redeem_reward(request):
    """Redeem a reward (admin mobile version)"""
    try:
        data = request.data
        admin = request.admin_user
        
        # Get user from QR scan
        user_id = data.get('user_id')
        if not user_id:
            return Response({
                'success': False,
                'error': 'User ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = get_object_or_404(Users, id=user_id, status='approved', is_active=True)
        
        # Check if operations manager can access this user's barangay
        if admin.role == 'operations_manager':
            if user.family and user.family.barangay:
                if not admin.assigned_barangays.filter(id=user.family.barangay.id).exists():
                    return Response({
                        'success': False,
                        'error': 'You do not have permission to process redemptions for users from this barangay'
                    }, status=status.HTTP_403_FORBIDDEN)
        
        reward_id = data.get('reward_id')
        if not reward_id:
            logger.error("Redemption failed: No reward_id provided")
            return Response({
                'success': False,
                'error': 'Reward ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reward = Reward.objects.get(id=reward_id, is_active=True)
            logger.info(f"Found reward for redemption: {reward.name} (Stock: {reward.stock}, Points: {reward.points_required})")
        except Reward.DoesNotExist:
            logger.error(f"Redemption failed: Reward not found with ID: {reward_id}")
            return Response({
                'success': False,
                'error': 'Reward not found or not available'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if reward is in stock
        if reward.stock <= 0:
            logger.warning(f"Redemption failed: Reward {reward.name} is out of stock")
            return Response({
                'success': False,
                'error': 'Reward is out of stock'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user has enough points (use total_points field)
        user_points = user.total_points
        if user_points < reward.points_required:
            logger.warning(f"Redemption failed: User {user.username} has insufficient points. Need {reward.points_required}, have {user_points}")
            return Response({
                'success': False,
                'error': f'Insufficient points. Need {reward.points_required}, have {user_points}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Processing redemption: User {user.username} redeeming {reward.name} for {reward.points_required} points")
        
        # Process redemption
        with transaction.atomic():
            # Create redemption record (using correct field names)
            redemption = Redemption.objects.create(
                user=user,
                reward=reward,
                points_used=reward.points_required,
                requested_by=user,  # User who requested the redemption
                approved_by=admin,  # Admin who approved/processed the redemption
                # created_at is auto-generated
            )
            
            # Create points transaction (using correct field names)
            points_transaction = PointsTransaction.objects.create(
                user=user,
                transaction_type='redeemed',
                points_amount=-reward.points_required,  # Field name is points_amount
                description=f"Redeemed: {reward.name}",
                processed_by=admin,  # Track which admin processed this
                # transaction_date and created_at are auto-generated
            )
            
            # Update user's points (use total_points field)
            user.total_points -= reward.points_required
            user.save()
            
            # Update family points if user has a family
            if user.family:
                user.family.total_family_points -= reward.points_required
                user.family.save(update_fields=['total_family_points'])
            
            # Update reward stock
            reward.stock -= 1
            reward.save()
            
            # Create reward history
            RewardHistory.objects.create(
                reward=reward,
                action='stock_redeemed',  # Use correct action choice
                admin_user=admin,
                user=user,
                redemption=redemption,
                stock_change=-1,  # Reducing stock by 1
                previous_stock=reward.stock + 1,  # Stock before redemption
                new_stock=reward.stock,  # Stock after redemption
                notes=f"Redeemed {reward.name} for {reward.points_required} points",
                timestamp=timezone.now()
            )
            
            # Create notification for user dashboard
            try:
                from accounts.models import Notification
                notification = Notification.objects.create(
                    user=user,
                    type='redeem',
                    message=f'Your reward "{reward.name}" has been processed successfully! {reward.points_required} points deducted by {admin.full_name}.',
                    points=-reward.points_required,
                    reward_name=reward.name
                )
                logger.info(f"Redemption notification created for user {user.username}: {notification.message}")
            except Exception as notif_error:
                logger.warning(f"Failed to create redemption notification: {str(notif_error)}")
                # Don't fail the transaction for notification issues
        
        # Log admin action
        from cenro.admin_utils import log_admin_action
        log_admin_action(
            admin, None, 'reward_redemption',
            f"Processed redemption for {user.full_name}: {reward.name} (-{reward.points_required} points)",
            request
        )
        
        return Response({
            'success': True,
            'redemption': {
                'id': redemption.id,
                'user_name': user.full_name,
                'reward_name': reward.name,
                'points_used': reward.points_required,
                'timestamp': redemption.created_at.isoformat(),  # Use created_at
                'processed_by': admin.full_name
            },
            'user_new_points': user.total_points  # Use total_points
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        import traceback
        logger.error(f"Error redeeming reward: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Provide more specific error information
        error_message = 'Failed to redeem reward'
        if 'DoesNotExist' in str(e):
            error_message = 'Reward not found or not available'
        elif 'IntegrityError' in str(e):
            error_message = 'Database integrity error during redemption'
        elif 'ValidationError' in str(e):
            error_message = 'Invalid data provided for redemption'
        
        return Response({
            'success': False,
            'error': error_message,
            'debug_error': str(e) if logger.level <= 10 else None  # Only show in debug mode
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_jwt_required
def get_user_by_id(request, user_id):
    """Get user information by user ID - Admin only (for refreshing user data)"""
    try:
        logger.info(f"Get user by ID endpoint called by admin: {request.admin_user.username} for user: {user_id}")
        
        try:
            user = Users.objects.get(id=user_id, status='approved', is_active=True)
            logger.info(f"User found: {user.full_name} ({user.username})")
        except Users.DoesNotExist:
            logger.error(f"User not found with ID: {user_id}")
            return Response({
                'success': False,
                'error': 'User not found or not approved'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if operations manager can access this user's barangay
        admin = request.admin_user
        if admin.role == 'operations_manager':
            if user.family and user.family.barangay:
                if not admin.assigned_barangays.filter(id=user.family.barangay.id).exists():
                    logger.warning(f"Operations manager {admin.username} denied access to user from barangay {user.family.barangay.name}")
                    return Response({
                        'success': False,
                        'error': 'You do not have permission to access users from this barangay'
                    }, status=status.HTTP_403_FORBIDDEN)
        
        # Build the display name - use full_name if available, otherwise combine first_name and last_name
        display_name = user.full_name
        if not display_name and user.first_name:
            display_name = f"{user.first_name} {user.last_name}".strip()
        
        # Build user data response
        user_data = {
            'id': str(user.id),  # Ensure UUID is converted to string
            'name': display_name or '',
            'username': user.username,
            'current_points': user.total_points,  # Use total_points field
            'family_code': user.family.family_code if user.family else '',
            'family_name': user.family.family_name if user.family else '',
            'barangay': user.family.barangay.name if user.family and user.family.barangay else None,
            'phone': user.phone,
            'is_family_representative': user.is_family_representative
        }
        
        logger.info(f"Returning user data for: {display_name}")
        return Response({
            'success': True,
            'user': user_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting user by ID: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': 'Failed to get user information',
            'debug_error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_jwt_required
def get_recent_transactions(request):
    """Get recent transactions for mobile app - all transactions since model doesn't track admin"""
    try:
        admin = request.admin_user
        limit = int(request.GET.get('limit', 20))
        
        # Since WasteTransaction doesn't have collected_by field, get all recent transactions
        # Get recent waste transactions
        waste_transactions = WasteTransaction.objects.select_related(
            'user', 'waste_type'
        ).order_by('-created_at')[:limit]
        
        # Get recent redemptions - use approved_by instead of redeemed_by
        redemptions = Redemption.objects.filter(
            approved_by=admin
        ).select_related('user', 'reward').order_by('-created_at')[:limit]
        
        waste_data = [{
            'id': wt.id,
            'type': 'waste_collection',
            'user_name': wt.user.full_name,
            'waste_type': wt.waste_type.name,
            'weight_kg': wt.waste_kg,  # Use waste_kg instead of weight_kg
            'points_earned': wt.total_points,  # Use total_points instead of points_earned
            'timestamp': wt.created_at.isoformat(),  # Use created_at instead of timestamp
            'family_code': wt.user.family.family_code if wt.user.family else None
        } for wt in waste_transactions]
        
        redemption_data = [{
            'id': r.id,
            'type': 'redemption',
            'user_name': r.user.full_name,
            'reward_name': r.reward.name,
            'points_used': r.points_used,
            'status': 'completed',  # Redemption model doesn't have status field
            'timestamp': r.created_at.isoformat(),  # Use created_at
            'family_code': r.user.family.family_code if r.user.family else None
        } for r in redemptions]
        
        return Response({
            'success': True,
            'waste_transactions': waste_data,
            'redemptions': redemption_data,
            'admin_name': admin.full_name,
            'note': 'Waste transactions show all recent transactions (no admin tracking in model)'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting recent transactions: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get transaction history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
def health_check(request):
    """Simple health check endpoint"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    return JsonResponse({
        'status': 'ok',
        'message': 'Ekoscan API is running',
        'timestamp': timezone.now().isoformat(),
        'authentication': 'JWT'
    }, status=200)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_user_notifications(request):
    """Get recent notifications for a user - No authentication required for dashboard integration"""
    try:
        user_id = request.GET.get('user_id')
        if not user_id:
            return Response({
                'success': False,
                'error': 'User ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = Users.objects.get(id=user_id, status='approved', is_active=True)
        except Users.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get recent notifications (last 20)
        try:
            from accounts.models import Notification
            notifications = Notification.objects.filter(
                user=user
            ).order_by('-created_at')[:20]
            
            notifications_data = [{
                'id': str(notif.id),
                'type': notif.type,
                'message': notif.message,
                'points': notif.points,
                'reward_name': notif.reward_name,
                'video_title': notif.video_title,
                'game_score': notif.game_score,
                'is_read': notif.is_read,
                'created_at': notif.created_at.isoformat(),
                'time_ago': _get_time_ago(notif.created_at)
            } for notif in notifications]
            
        except Exception as e:
            logger.error(f"Error fetching notifications: {str(e)}")
            notifications_data = []
        
        return Response({
            'success': True,
            'notifications': notifications_data,
            'unread_count': len([n for n in notifications_data if not n['is_read']]),
            'total_count': len(notifications_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting user notifications: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get notifications'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_time_ago(datetime_obj):
    """Helper function to get human-readable time difference"""
    now = timezone.now()
    diff = now - datetime_obj
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def mark_notification_read(request):
    """Mark a notification as read - No authentication required for dashboard integration"""
    try:
        data = request.data
        notification_id = data.get('notification_id')
        user_id = data.get('user_id')
        
        if not notification_id or not user_id:
            return Response({
                'success': False,
                'error': 'Notification ID and User ID are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from accounts.models import Notification
            notification = Notification.objects.get(
                id=notification_id,
                user_id=user_id
            )
            notification.is_read = True
            notification.save()
            
            return Response({
                'success': True,
                'message': 'Notification marked as read'
            }, status=status.HTTP_200_OK)
            
        except Notification.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to mark notification as read'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
