"""
User data views for mobile API
Handles user points, profile data, and family information
Uses JWT authentication for mobile apps
"""
# Standard library
import json
import logging

# Django
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

# Django REST Framework
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Local apps
from accounts.models import Users


logger = logging.getLogger(__name__)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def current_points(request):
    """Enhanced current points endpoint with comprehensive data and error handling"""
    try:
        user = request.user
        
        # Basic response structure
        response_data = {
            'success': True,
            'message': 'Points data retrieved successfully',
            'timestamp': timezone.now().isoformat()
        }
        
        # Step 1: Get basic user info
        try:
            response_data['user_points'] = {
                'total_points': user.total_points,
                'username': user.username,
                'full_name': getattr(user, 'full_name', f"{user.first_name} {user.last_name}".strip()),
                'is_family_representative': getattr(user, 'is_family_representative', False)
            }
        except Exception as e:
            logger.error(f"Error getting user points for {request.user.username}: {str(e)}")
            response_data['user_points'] = {
                'total_points': 0,
                'username': user.username,
                'full_name': 'Unknown',
                'is_family_representative': False,
                'error': str(e)
            }
        
        # Step 2: Get family information safely
        family_info = {
            'total_family_points': 0,
            'family_name': '',
            'family_code': '',
            'family_rank': 'N/A',
            'family_members_count': 0
        }
        
        try:
            if hasattr(user, 'family') and user.family:
                family = user.family
                family_info.update({
                    'total_family_points': getattr(family, 'total_family_points', 0),
                    'family_name': getattr(family, 'family_name', ''),
                    'family_code': getattr(family, 'family_code', ''),
                })
                
                # Try to get family rank
                try:
                    if hasattr(user, 'get_family_rank'):
                        family_info['family_rank'] = user.get_family_rank()
                except Exception as e:
                    family_info['family_rank'] = 'N/A'
                    family_info['rank_error'] = str(e)
                
                # Try to get family members count
                try:
                    family_info['family_members_count'] = Users.objects.filter(
                        family=family, 
                        status='approved'
                    ).count()
                except Exception as e:
                    family_info['family_members_count'] = 0
                    family_info['count_error'] = str(e)
            else:
                family_info['status'] = 'no_family'
        except Exception as e:
            logger.error(f"Error getting family info for {request.user.username}: {str(e)}")
            family_info['error'] = str(e)
            family_info['status'] = 'error'
        
        response_data['family_points'] = family_info
        
        # Step 3: Check system access (optional)
        try:
            if hasattr(user, 'can_access_system'):
                can_access = user.can_access_system()
                if not can_access:
                    response_data['warning'] = 'Account access may be revoked'
        except Exception as e:
            response_data['access_check_error'] = str(e)
        
        return Response(response_data, status=200)
        
    except Exception as e:
        logger.error(f"Critical error in current_points for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error retrieving points data',
            'error_code': 'POINTS_FETCH_ERROR',
            'error_details': str(e),
            'fallback_data': {
                'total_points': 0,
                'family_total_points': 0,
                'username': getattr(request.user, 'username', 'unknown')
            }
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def current_user_data(request):
    """Enhanced user data endpoint with comprehensive error handling"""
    try:
        # Debug authentication
        auth_header = request.META.get('HTTP_AUTHORIZATION', 'Not provided')
        logger.info(f"Auth header in current_user_data: {auth_header}")
        logger.info(f"User authenticated: {request.user.is_authenticated}")
        logger.info(f"User: {request.user}")
        
        user = request.user
        
        # Initialize response with safe defaults
        response_data = {
            'success': True,
            'message': 'User data retrieved successfully',
            'timestamp': timezone.now().isoformat()
        }
        
        # Step 1: Get basic user information safely
        user_info = {
            'id': str(user.id),
            'username': user.username,
            'phone': getattr(user, 'phone', ''),
            'full_name': getattr(user, 'full_name', ''),
            'total_points': getattr(user, 'total_points', 0),
            'gender': getattr(user, 'gender', ''),
            'is_family_representative': getattr(user, 'is_family_representative', False),
            'status': getattr(user, 'status', 'unknown'),
            'referral_code': getattr(user, 'referral_code', '')
        }
        
        # Try to get additional user info safely
        try:
            user_info['date_of_birth'] = getattr(user, 'date_of_birth', None)
            if user_info['date_of_birth']:
                user_info['date_of_birth'] = user_info['date_of_birth'].isoformat()
        except Exception as e:
            user_info['date_of_birth'] = None
            user_info['date_of_birth_error'] = str(e)
        
        # Try to get total_points safely
        try:
            user_info['total_points'] = getattr(user, 'total_points', 0)
        except Exception as e:
            user_info['total_points'] = 0
            user_info['points_error'] = str(e)
        
        # Try to get family representative status
        try:
            user_info['is_family_representative'] = getattr(user, 'is_family_representative', False)
        except Exception as e:
            user_info['is_family_representative'] = False
            user_info['rep_status_error'] = str(e)
        
        # Try to get date fields
        try:
            user_info['date_joined'] = user.date_joined.isoformat() if user.date_joined else None
            user_info['last_login'] = user.last_login.isoformat() if user.last_login else None
        except Exception as e:
            user_info['date_joined'] = None
            user_info['last_login'] = None
            user_info['date_error'] = str(e)
        
        response_data['user_info'] = user_info
        
        # Step 2: Get family information safely
        family_info = {
            'family_name': '',
            'family_code': '',
            'family_total_points': 0,
            'family_status': 'no_family',
            'barangay': '',
            'family_members_count': 0,
            'family_rank': 'N/A'
        }
        
        try:
            if hasattr(user, 'family') and user.family:
                family = user.family
                
                # Basic family info
                family_info['family_name'] = getattr(family, 'family_name', '')
                family_info['family_code'] = getattr(family, 'family_code', '')
                family_info['family_total_points'] = getattr(family, 'total_family_points', 0)
                family_info['family_status'] = getattr(family, 'status', 'unknown')
                
                # Barangay info
                try:
                    if hasattr(family, 'barangay') and family.barangay:
                        family_info['barangay'] = family.barangay.name
                    else:
                        family_info['barangay'] = ''
                except Exception as e:
                    family_info['barangay'] = ''
                    family_info['barangay_error'] = str(e)
                
                # Family members count
                try:
                    family_info['family_members_count'] = Users.objects.filter(
                        family=family, 
                        status='approved'
                    ).count()
                except Exception as e:
                    family_info['family_members_count'] = 0
                    family_info['count_error'] = str(e)
                
                # Family rank
                try:
                    if hasattr(user, 'get_family_rank'):
                        family_info['family_rank'] = user.get_family_rank()
                except Exception as e:
                    family_info['family_rank'] = 'N/A'
                    family_info['rank_error'] = str(e)
            else:
                family_info['family_status'] = 'no_family'
                
        except Exception as e:
            family_info['error'] = str(e)
            family_info['family_status'] = 'error'
        
        response_data['family_info'] = family_info
        
        # Step 3: Get permissions safely
        permissions = {
            'can_earn_points': True,
            'can_redeem_rewards': True,
            'is_family_representative': user_info.get('is_family_representative', False)
        }
        
        try:
            if hasattr(user, 'can_access_system'):
                permissions['can_access_system'] = user.can_access_system()
            else:
                permissions['can_access_system'] = True
        except Exception as e:
            permissions['can_access_system'] = True
            permissions['access_check_error'] = str(e)
        
        response_data['permissions'] = permissions
        
        return Response(response_data, status=200)
        
    except Exception as e:
        logger.error(f"Critical error in current_user_data for user {getattr(request.user, 'username', 'unknown')}: {str(e)}")
        
        # Return minimal safe data even on error
        return Response({
            'success': False,
            'message': 'Error retrieving user data',
            'error_code': 'USER_DATA_FETCH_ERROR',
            'error_details': str(e),
            'fallback_data': {
                'user_info': {
                    'id': str(getattr(request.user, 'id', 'unknown')),
                    'username': getattr(request.user, 'username', 'unknown'),
                    'total_points': 0,
                    'is_family_representative': False
                },
                'family_info': {
                    'family_name': '',
                    'family_total_points': 0
                },
                'permissions': {
                    'can_access_system': True,
                    'can_earn_points': True,
                    'can_redeem_rewards': True
                }
            }
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def family_members(request):
    """Enhanced family members endpoint with comprehensive family data"""
    try:
        user = request.user
        
        # Verify user can access system
        if not user.can_access_system():
            return Response({
                'success': False,
                'message': 'Account access has been revoked',
                'error_code': 'ACCESS_REVOKED'
            }, status=403)
        
        if not user.family:
            return Response({
                'success': False,
                'message': 'User is not associated with any family',
                'error_code': 'NO_FAMILY_ASSOCIATION'
            }, status=400)
        
        # Get all family members with their data
        family_members_qs = Users.objects.filter(
            family=user.family
        ).select_related('family').order_by('first_name', 'last_name')
        
        members_data = []
        total_family_points = 0
        
        for member in family_members_qs:
            member_info = {
                'id': str(member.id),
                'username': member.username,
                'full_name': member.full_name,
                'first_name': member.first_name,
                'last_name': member.last_name,
                'total_points': member.total_points,
                'status': member.status,
                'is_family_representative': member.is_family_representative,
                'date_joined': member.date_joined.isoformat() if member.date_joined else None,
                'last_login': member.last_login.isoformat() if member.last_login else None,
                'is_current_user': member.id == user.id
            }
            members_data.append(member_info)
            
            # Add to total points if member is approved
            if member.status == 'approved':
                total_family_points += member.total_points
        
        # Family summary
        family_summary = {
            'family_name': user.family.family_name,
            'family_code': user.family.family_code,
            'family_status': user.family.status,
            'total_members': len(members_data),
            'approved_members': len([m for m in members_data if m['status'] == 'approved']),
            'total_family_points': total_family_points,
            'barangay': user.family.barangay.name if user.family.barangay else '',
            'family_rank': user.get_family_rank()
        }
        
        return Response({
            'success': True,
            'message': 'Family members data retrieved successfully',
            'family_summary': family_summary,
            'family_members': members_data,
            'current_user_role': 'representative' if user.is_family_representative else 'member',
            'timestamp': timezone.now().isoformat()
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error getting family members for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error retrieving family members data',
            'error_code': 'FAMILY_DATA_FETCH_ERROR'
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_points(request):
    """Update user points via JWT authenticated API"""
    try:
        user = request.user
        new_points = request.data.get('total_points')
        
        if new_points is None:
            return Response({'error': 'total_points is required'}, status=400)
        
        logger.info(f"Updating points for user {user.username} from {user.total_points} to {new_points}")
        
        # Update the user's points
        user.total_points = new_points
        user.save()  # This will automatically update family points through the custom save() method
        
        logger.info(f"Points updated successfully. New total: {user.total_points}")
        
        return Response({
            'success': True, 
            'total_points': user.total_points,
            'family_name': user.family.family_name if user.family else '',
            'message': 'Points updated successfully'
        }, status=200)
            
    except Exception as e:
        logger.error(f"Error updating points: {str(e)}")
        return Response({'error': str(e)}, status=500)
