"""
Admin notification API endpoints
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from django.db import transaction, IntegrityError
import logging

from accounts.models import (
    Users, Family, Barangay, PointsTransaction, Reward, GarbageSchedule, RewardCategory,
    WasteType, WasteTransaction, Redemption, Notification, RewardHistory
)
from cenro.models import AdminActionHistory
from game.models import Question, Choice, WasteCategory, WasteItem
from learn.models import LearningVideo, VideoWatchHistory

from ..admin_auth import admin_required, role_required, permission_required
from ..models import AdminNotification

logger = logging.getLogger(__name__)

from .utils import get_time_ago


# ========================
# Admin Notification API Endpoints
# ========================

@admin_required
def get_admin_notifications_unread_count(request):
    """
    Get unread notification count for current admin user
    """
    try:
        admin_user_id = request.session.get('admin_user_id')
        
        if not admin_user_id:
            return JsonResponse({'count': 0})
        
        # Count unread notifications for this admin only
        unread_count = AdminNotification.objects.filter(
            admin_user_id=admin_user_id,
            is_read=False
        ).count()
        
        return JsonResponse({'count': unread_count})
        
    except Exception as e:
        logger.error(f"Error fetching admin notification count: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@admin_required
def get_admin_notifications_list(request):
    """
    Get list of recent notifications for current admin user
    Returns last 10 notifications (read and unread)
    """
    try:
        admin_user_id = request.session.get('admin_user_id')
        
        if not admin_user_id:
            return JsonResponse({'notifications': []})
        
        # Get notifications for this admin only
        notifications = AdminNotification.objects.filter(
            admin_user_id=admin_user_id
        ).select_related('related_user', 'related_user__family', 'related_user__family__barangay').order_by('-created_at')[:10]
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': str(notification.id),
                'type': notification.notification_type,
                'type_display': notification.get_notification_type_display(),
                'message': notification.message,
                'link_url': notification.link_url,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime('%Y-%m-%d %I:%M %p'),
                'time_ago': get_time_ago(notification.created_at),
            })
        
        return JsonResponse({'notifications': notifications_data})
        
    except Exception as e:
        logger.error(f"Error fetching admin notifications: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt  # CSRF exempt because @admin_required already validates session
@admin_required
@require_POST
def mark_admin_notification_read(request, notification_id):
    """
    Mark a specific notification as read
    """
    try:
        admin_user_id = request.session.get('admin_user_id')
        
        if not admin_user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        # Get notification (must belong to this admin only)
        notification = AdminNotification.objects.filter(
            id=notification_id,
            admin_user_id=admin_user_id
        ).first()
        
        if not notification:
            return JsonResponse({'error': 'Notification not found'}, status=404)
        
        notification.mark_as_read()
        
        return JsonResponse({'success': True, 'message': 'Notification marked as read'})
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt  # CSRF exempt because @admin_required already validates session
@admin_required
@require_POST
def mark_all_admin_notifications_read(request):
    """
    Mark all notifications as read for current admin user
    """
    try:
        admin_user_id = request.session.get('admin_user_id')
        
        if not admin_user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        # Update all unread notifications for this admin only
        updated_count = AdminNotification.objects.filter(
            admin_user_id=admin_user_id,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return JsonResponse({
            'success': True, 
            'message': f'{updated_count} notifications marked as read',
            'count': updated_count
        })
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


