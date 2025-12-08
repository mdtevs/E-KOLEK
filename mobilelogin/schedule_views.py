"""
Schedule views for mobile API
Handles garbage collection schedule endpoints for Flutter app
"""
import logging
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.models import GarbageSchedule, Barangay


logger = logging.getLogger(__name__)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_garbage_schedule(request):
    """
    Get garbage collection schedule for the authenticated user's barangay
    Returns all active schedules for the user's assigned barangay
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
        
        # Get user's barangay
        try:
            barangay = user.get_barangay()
            if not barangay:
                return Response({
                    'success': False,
                    'message': 'No barangay assigned to your family',
                    'error_code': 'NO_BARANGAY',
                    'schedules': []
                }, status=200)
        except Exception as e:
            logger.error(f"Error getting barangay for user {user.username}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving barangay information',
                'error_code': 'BARANGAY_ERROR',
                'schedules': []
            }, status=500)
        
        # Get active schedules for the barangay
        try:
            schedules = GarbageSchedule.objects.filter(
                barangay=barangay,
                is_active=True
            ).order_by('day', 'start_time')
            
            # Format schedule data for mobile app
            schedule_data = []
            for schedule in schedules:
                schedule_info = {
                    'id': str(schedule.id),
                    'day': schedule.day,
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'end_time': schedule.end_time.strftime('%H:%M'),
                    'waste_types': schedule.waste_types if schedule.waste_types else [],
                    'notes': schedule.notes or '',
                    'is_active': schedule.is_active
                }
                schedule_data.append(schedule_info)
            
            return Response({
                'success': True,
                'message': 'Garbage collection schedule retrieved successfully',
                'barangay': {
                    'id': str(barangay.id),
                    'name': barangay.name
                },
                'schedules': schedule_data,
                'total_schedules': len(schedule_data),
                'timestamp': timezone.now().isoformat()
            }, status=200)
            
        except Exception as e:
            logger.error(f"Error fetching schedules for barangay {barangay.name}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving garbage collection schedules',
                'error_code': 'SCHEDULE_FETCH_ERROR',
                'schedules': []
            }, status=500)
        
    except Exception as e:
        logger.error(f"Critical error in get_garbage_schedule for user {getattr(request.user, 'username', 'unknown')}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR',
            'schedules': []
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_all_schedules(request):
    """
    Get all garbage collection schedules across all barangays
    Useful for users who want to see schedules for different areas
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
        
        # Get all active schedules grouped by barangay
        try:
            schedules = GarbageSchedule.objects.filter(
                is_active=True
            ).select_related('barangay').order_by('barangay__name', 'day', 'start_time')
            
            # Group schedules by barangay
            barangay_schedules = {}
            for schedule in schedules:
                barangay_name = schedule.barangay.name
                
                if barangay_name not in barangay_schedules:
                    barangay_schedules[barangay_name] = {
                        'barangay_id': str(schedule.barangay.id),
                        'barangay_name': barangay_name,
                        'schedules': []
                    }
                
                schedule_info = {
                    'id': str(schedule.id),
                    'day': schedule.day,
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'end_time': schedule.end_time.strftime('%H:%M'),
                    'waste_types': schedule.waste_types if schedule.waste_types else [],
                    'notes': schedule.notes or '',
                    'is_active': schedule.is_active
                }
                barangay_schedules[barangay_name]['schedules'].append(schedule_info)
            
            # Convert to list for response
            schedules_list = list(barangay_schedules.values())
            
            # Get user's barangay for highlighting
            user_barangay = user.get_barangay()
            user_barangay_name = user_barangay.name if user_barangay else None
            
            return Response({
                'success': True,
                'message': 'All garbage collection schedules retrieved successfully',
                'user_barangay': user_barangay_name,
                'barangays': schedules_list,
                'total_barangays': len(schedules_list),
                'timestamp': timezone.now().isoformat()
            }, status=200)
            
        except Exception as e:
            logger.error(f"Error fetching all schedules: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving garbage collection schedules',
                'error_code': 'SCHEDULE_FETCH_ERROR',
                'barangays': []
            }, status=500)
        
    except Exception as e:
        logger.error(f"Critical error in get_all_schedules for user {getattr(request.user, 'username', 'unknown')}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR',
            'barangays': []
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_schedule_by_barangay(request, barangay_id):
    """
    Get garbage collection schedule for a specific barangay by ID
    Allows users to check schedules for any barangay
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
        
        # Get the specified barangay
        try:
            barangay = Barangay.objects.get(id=barangay_id)
        except Barangay.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Barangay not found',
                'error_code': 'BARANGAY_NOT_FOUND',
                'schedules': []
            }, status=404)
        
        # Get active schedules for the barangay
        try:
            schedules = GarbageSchedule.objects.filter(
                barangay=barangay,
                is_active=True
            ).order_by('day', 'start_time')
            
            # Format schedule data for mobile app
            schedule_data = []
            for schedule in schedules:
                schedule_info = {
                    'id': str(schedule.id),
                    'day': schedule.day,
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'end_time': schedule.end_time.strftime('%H:%M'),
                    'waste_types': schedule.waste_types if schedule.waste_types else [],
                    'notes': schedule.notes or '',
                    'is_active': schedule.is_active
                }
                schedule_data.append(schedule_info)
            
            return Response({
                'success': True,
                'message': 'Garbage collection schedule retrieved successfully',
                'barangay': {
                    'id': str(barangay.id),
                    'name': barangay.name
                },
                'schedules': schedule_data,
                'total_schedules': len(schedule_data),
                'timestamp': timezone.now().isoformat()
            }, status=200)
            
        except Exception as e:
            logger.error(f"Error fetching schedules for barangay {barangay.name}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving garbage collection schedules',
                'error_code': 'SCHEDULE_FETCH_ERROR',
                'schedules': []
            }, status=500)
        
    except Exception as e:
        logger.error(f"Critical error in get_schedule_by_barangay for user {getattr(request.user, 'username', 'unknown')}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR',
            'schedules': []
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_todays_schedule(request):
    """
    Get today's garbage collection schedule for the user's barangay
    Returns only schedules for the current day
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
        
        # Get user's barangay
        try:
            barangay = user.get_barangay()
            if not barangay:
                return Response({
                    'success': False,
                    'message': 'No barangay assigned to your family',
                    'error_code': 'NO_BARANGAY',
                    'schedules': []
                }, status=200)
        except Exception as e:
            logger.error(f"Error getting barangay for user {user.username}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving barangay information',
                'error_code': 'BARANGAY_ERROR',
                'schedules': []
            }, status=500)
        
        # Get current day name
        current_day = timezone.now().strftime('%A')  # e.g., 'Monday', 'Tuesday'
        
        # Get today's schedules for the barangay
        try:
            schedules = GarbageSchedule.objects.filter(
                barangay=barangay,
                day=current_day,
                is_active=True
            ).order_by('start_time')
            
            # Format schedule data for mobile app
            schedule_data = []
            for schedule in schedules:
                schedule_info = {
                    'id': str(schedule.id),
                    'day': schedule.day,
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'end_time': schedule.end_time.strftime('%H:%M'),
                    'waste_types': schedule.waste_types if schedule.waste_types else [],
                    'notes': schedule.notes or '',
                    'is_active': schedule.is_active
                }
                schedule_data.append(schedule_info)
            
            return Response({
                'success': True,
                'message': f"Today's garbage collection schedule retrieved successfully",
                'today': current_day,
                'barangay': {
                    'id': str(barangay.id),
                    'name': barangay.name
                },
                'schedules': schedule_data,
                'total_schedules': len(schedule_data),
                'has_collection_today': len(schedule_data) > 0,
                'timestamp': timezone.now().isoformat()
            }, status=200)
            
        except Exception as e:
            logger.error(f"Error fetching today's schedules for barangay {barangay.name}: {str(e)}")
            return Response({
                'success': False,
                'message': "Error retrieving today's garbage collection schedules",
                'error_code': 'SCHEDULE_FETCH_ERROR',
                'schedules': []
            }, status=500)
        
    except Exception as e:
        logger.error(f"Critical error in get_todays_schedule for user {getattr(request.user, 'username', 'unknown')}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR',
            'schedules': []
        }, status=500)
