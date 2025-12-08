"""
Notification views for mobile API
Handles notification fetching and marking as read/viewed
Uses JWT authentication for mobile apps
"""
# Standard library
import logging

# Django
from django.utils import timezone

# Django REST Framework
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Local apps
from accounts.models import Notification


logger = logging.getLogger(__name__)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """
    Get all notifications for the authenticated user
    
    Query Parameters:
    - limit: Maximum number of notifications to return (default: 20, max: 100)
    - offset: Number of notifications to skip for pagination (default: 0)
    - unread_only: If 'true', only return unread notifications (default: false)
    
    Returns:
    - success: Boolean indicating success
    - message: Success message
    - notifications: List of notification objects
    - unread_count: Total count of unread notifications
    - total_count: Total count of all notifications
    - timestamp: Current server timestamp
    """
    try:
        user = request.user
        
        # Get query parameters
        try:
            limit = min(int(request.query_params.get('limit', 20)), 100)
        except (ValueError, TypeError):
            limit = 20
            
        try:
            offset = max(int(request.query_params.get('offset', 0)), 0)
        except (ValueError, TypeError):
            offset = 0
        
        unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
        
        # Build query
        notifications_query = Notification.objects.filter(user=user)
        
        if unread_only:
            notifications_query = notifications_query.filter(viewed_at__isnull=True)
        
        # Get total counts
        total_count = notifications_query.count()
        unread_count = Notification.objects.filter(user=user, viewed_at__isnull=True).count()
        
        # Apply pagination and ordering
        notifications = notifications_query.order_by('-created_at')[offset:offset + limit]
        
        # Format notifications data
        notifications_data = []
        for notif in notifications:
            notif_data = {
                'id': str(notif.id),
                'type': notif.type,
                'message': notif.message,
                'is_read': notif.is_read,
                'viewed_at': notif.viewed_at.isoformat() if notif.viewed_at else None,
                'created_at': notif.created_at.isoformat(),
            }
            
            # Add optional fields based on notification type
            if notif.points is not None:
                notif_data['points'] = float(notif.points)
            
            if notif.reward_name:
                notif_data['reward_name'] = notif.reward_name
            
            if notif.video_title:
                notif_data['video_title'] = notif.video_title
            
            if notif.game_score is not None:
                notif_data['game_score'] = notif.game_score
            
            notifications_data.append(notif_data)
        
        return Response({
            'success': True,
            'message': 'Notifications retrieved successfully',
            'notifications': notifications_data,
            'unread_count': unread_count,
            'total_count': total_count,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total_count
            },
            'timestamp': timezone.now().isoformat()
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error getting notifications for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error retrieving notifications',
            'error_code': 'NOTIFICATIONS_FETCH_ERROR',
            'error_details': str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def mark_notifications_viewed(request):
    """
    Mark notifications as viewed when user opens the notifications tab
    
    Request Body (optional):
    - notification_ids: Array of notification IDs to mark as viewed (if not provided, marks all unviewed)
    
    Returns:
    - success: Boolean indicating success
    - message: Success message
    - updated_count: Number of notifications marked as viewed
    - timestamp: Current server timestamp
    """
    try:
        user = request.user
        notification_ids = request.data.get('notification_ids', None)
        
        # Build query
        query = Notification.objects.filter(user=user, viewed_at__isnull=True)
        
        # If specific notification IDs are provided, filter by them
        if notification_ids and isinstance(notification_ids, list):
            query = query.filter(id__in=notification_ids)
        
        # Update viewed_at timestamp
        updated_count = query.update(viewed_at=timezone.now())
        
        return Response({
            'success': True,
            'message': f'{updated_count} notification(s) marked as viewed',
            'updated_count': updated_count,
            'timestamp': timezone.now().isoformat()
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error marking notifications as viewed for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error marking notifications as viewed',
            'error_code': 'NOTIFICATIONS_UPDATE_ERROR',
            'error_details': str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """
    Mark a specific notification as read
    
    URL Parameters:
    - notification_id: UUID of the notification to mark as read
    
    Returns:
    - success: Boolean indicating success
    - message: Success message
    - timestamp: Current server timestamp
    """
    try:
        user = request.user
        
        # Get the notification
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
        except Notification.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Notification not found',
                'error_code': 'NOTIFICATION_NOT_FOUND'
            }, status=404)
        
        # Mark as read and viewed
        notification.is_read = True
        if not notification.viewed_at:
            notification.viewed_at = timezone.now()
        notification.save()
        
        return Response({
            'success': True,
            'message': 'Notification marked as read',
            'timestamp': timezone.now().isoformat()
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error marking notification as read for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error marking notification as read',
            'error_code': 'NOTIFICATION_READ_ERROR',
            'error_details': str(e)
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    """
    Get the count of unread notifications for the authenticated user
    
    Returns:
    - success: Boolean indicating success
    - unread_count: Number of unread notifications
    - timestamp: Current server timestamp
    """
    try:
        user = request.user
        unread_count = Notification.objects.filter(
            user=user,
            viewed_at__isnull=True
        ).count()
        
        return Response({
            'success': True,
            'unread_count': unread_count,
            'timestamp': timezone.now().isoformat()
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error getting unread count for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error retrieving unread count',
            'error_code': 'UNREAD_COUNT_ERROR',
            'error_details': str(e)
        }, status=500)
