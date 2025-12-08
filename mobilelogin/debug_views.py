"""
Debug and testing views for mobile API
Provides diagnostic endpoints for development and troubleshooting
"""
import logging
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from accounts.models import Users


logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])  # Allow access without authentication for testing
def api_test(request):
    """Enhanced API test endpoint with comprehensive endpoint information"""
    return Response({
        'status': 'success',
        'message': 'Django API is working!',
        'version': '2.0',
        'server_time': timezone.now().isoformat(),
        'server_host': str(request.META.get('HTTP_HOST', 'Unknown')),
        'method': request.method,
        'authentication': {
            'required': 'Most endpoints require Token authentication',
            'header_format': 'Authorization: Token YOUR_TOKEN_HERE',
            'get_token': 'POST /api/login/ with username and password'
        },
        'endpoints': {
            'authentication': {
                'login': '/api/login/',
                'qr_login': '/api/qr-login/',
                'logout': '/api/logout/',
                'refresh_token': '/api/refresh-token/',
                'validate_token': '/api/validate-token/'
            },
            'user_data': {
                'current_points': '/api/current_points/',
                'current_user_data': '/api/current_user_data/',
                'family_members': '/api/family_members/'
            },
            'schedule': {
                'get_schedule': '/api/schedule/',
                'today_schedule': '/api/schedule/today/',
                'all_schedules': '/api/schedule/all/',
                'barangay_schedule': '/api/schedule/barangay/<uuid>/'
            },
            'learning': {
                'get_videos': '/api/learning/videos/',
                'mark_watched': '/api/learning/videos/watched/',
                'debug_learning': '/api/learning/debug/'
            },
            'gaming': {
                'get_questions': '/api/questions/',
                'get_game_data': '/api/game/data/',
                'save_session': '/api/game/save-session/',
                'leaderboard': '/api/game/leaderboard/',
                'user_stats': '/api/game/user-stats/'
            },
            'rewards': {
                'redeem_reward': '/api/redeem-reward/'
            },
            'debug': {
                'api_test': '/api/',
                'user_debug': '/api/debug/user/'
            }
        },
        'mobile_setup': {
            'emulator_url': 'http://10.0.2.2:8000/api/',
            'physical_device': 'http://YOUR_IP:8000/api/',
            'test_connection': 'GET /api/ (this endpoint)',
            'example_login': {
                'url': '/api/login/',
                'method': 'POST',
                'body': {
                    'username': 'your_username',
                    'password': 'your_password'
                }
            }
        }
    })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def debug_user_info(request):
    """Enhanced debug endpoint to check user authentication and data"""
    try:
        user = request.user
        
        # Basic user info
        user_basic = {
            'id': str(user.id),
            'username': user.username,
            'is_authenticated': user.is_authenticated,
            'is_active': user.is_active,
            'status': user.status,
        }
        
        # Try to get points
        try:
            total_points = user.total_points
        except Exception as e:
            total_points = f"Error: {str(e)}"
        
        # Try to get family info
        family_info = {}
        try:
            if user.family:
                family_info = {
                    'has_family': True,
                    'family_name': user.family.family_name,
                    'family_code': user.family.family_code,
                    'family_status': user.family.status,
                }
                # Try to get family points
                try:
                    family_info['family_total_points'] = user.family.total_family_points
                except Exception as e:
                    family_info['family_total_points'] = f"Error: {str(e)}"
                
                # Try to get barangay
                try:
                    if user.family.barangay:
                        family_info['barangay'] = user.family.barangay.name
                    else:
                        family_info['barangay'] = 'No barangay assigned'
                except Exception as e:
                    family_info['barangay'] = f"Error: {str(e)}"
            else:
                family_info = {'has_family': False}
        except Exception as e:
            family_info = {'error': str(e)}
        
        # Try to check system access
        try:
            can_access = user.can_access_system()
        except Exception as e:
            can_access = f"Error: {str(e)}"
        
        # Try to get family rank
        try:
            family_rank = user.get_family_rank()
        except Exception as e:
            family_rank = f"Error: {str(e)}"
        
        # Test database connection
        try:
            user_count = Users.objects.count()
            db_test = f"Database accessible, {user_count} users found"
        except Exception as e:
            db_test = f"Database error: {str(e)}"
        
        return Response({
            'success': True,
            'debug_info': {
                'user_basic': user_basic,
                'total_points': total_points,
                'family_info': family_info,
                'can_access_system': can_access,
                'family_rank': family_rank,
                'database_test': db_test,
                'token_valid': True,
                'endpoint_test': 'debug endpoint working'
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'user_authenticated': request.user.is_authenticated if hasattr(request, 'user') else False
        })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def debug_simple_points(request):
    """Simple debug endpoint for points testing"""
    try:
        user = request.user
        
        # Test very basic functionality
        response_data = {
            'success': True,
            'message': 'Simple points endpoint working',
            'user_id': str(user.id),
            'username': user.username,
        }
        
        # Try to get points step by step
        try:
            points = user.total_points
            response_data['total_points'] = points
            response_data['points_status'] = 'success'
        except Exception as e:
            response_data['total_points'] = 0
            response_data['points_error'] = str(e)
            response_data['points_status'] = 'error'
        
        # Try to get family name
        try:
            if hasattr(user, 'family') and user.family:
                response_data['family_name'] = user.family.family_name
                response_data['family_status'] = 'success'
            else:
                response_data['family_name'] = 'No family'
                response_data['family_status'] = 'no_family'
        except Exception as e:
            response_data['family_name'] = 'Error getting family'
            response_data['family_error'] = str(e)
            response_data['family_status'] = 'error'
        
        return Response(response_data)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Error in simple points endpoint',
            'error': str(e),
            'error_type': type(e).__name__
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def debug_basic_auth(request):
    """Very basic authentication test - minimal functionality"""
    try:
        user = request.user
        return Response({
            'success': True,
            'message': 'Authentication working',
            'user_id': str(user.id),
            'username': user.username,
            'is_authenticated': user.is_authenticated,
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Basic authentication test failed'
        }, status=500)
