"""
Garbage schedule management views
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

logger = logging.getLogger(__name__)

import time


# adminschedule - views for admin schedule
@admin_required
@permission_required('can_manage_schedules')
def adminschedule(request):
    schedules = GarbageSchedule.objects.all()
    barangays = Barangay.objects.all()
    waste_types = WasteType.objects.all()
    return render(request, 'adminschedule.html', {
        'schedules': schedules, 
        'barangays': barangays, 
        'waste_types': waste_types,
        'timestamp': int(time.time()),
    })


def add_schedule(request):
    if request.method == 'POST':
        try:
            barangay_id = request.POST.get('barangay')
            day = request.POST.get('day')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            # Handle multiple selected waste types
            waste_types = request.POST.getlist('waste_types')
            notes = request.POST.get('notes')
            barangay = Barangay.objects.get(id=barangay_id)
            
            # Create schedule
            schedule = GarbageSchedule.objects.create(
                barangay=barangay,
                day=day,
                start_time=start_time,
                end_time=end_time,
                waste_types=waste_types,
                notes=notes
            )
            
            # Send email notifications to users in this barangay
            try:
                from accounts import schedule_notification_service
                
                logger.info(f"SENDING SCHEDULE NOTIFICATION - Barangay: {barangay.name}, Action: ADDED")
                
                notification_result = schedule_notification_service.send_schedule_added_notification(schedule)
                
                logger.info(f"Schedule notification result: {notification_result}")
                
                # Add notification info to response
                return JsonResponse({
                    'success': True, 
                    'id': str(schedule.id),
                    'notification_sent': notification_result.get('success', False),
                    'recipients_count': notification_result.get('recipients_count', 0),
                    'warning': notification_result.get('warning'),
                    'message': f"Schedule added successfully. {notification_result.get('message', '')}"
                })
            except Exception as notif_error:
                logger.error(f"Notification error: {str(notif_error)}")
                import traceback
                traceback.print_exc()
                logger.error(f"Failed to send schedule notification: {str(notif_error)}")
                # Still return success for schedule creation even if notification fails
                return JsonResponse({
                    'success': True, 
                    'id': str(schedule.id),
                    'notification_sent': False,
                    'message': 'Schedule added successfully but notifications failed to send',
                    'error': str(notif_error)
                })
                
        except Exception as e:
            logger.error(f"Error adding schedule: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False})


def edit_schedule(request):
    if request.method == 'POST':
        try:
            schedule_id = request.POST.get('id')
            schedule = GarbageSchedule.objects.get(id=schedule_id)
            barangay_id = request.POST.get('barangay')
            schedule.barangay = Barangay.objects.get(id=barangay_id)
            schedule.day = request.POST.get('day')
            schedule.start_time = request.POST.get('start_time')
            schedule.end_time = request.POST.get('end_time')
            # Handle multiple selected waste types
            schedule.waste_types = request.POST.getlist('waste_types')
            schedule.notes = request.POST.get('notes')
            schedule.save()
            
            # Send email notifications to users in this barangay
            try:
                from accounts import schedule_notification_service
                notification_result = schedule_notification_service.send_schedule_updated_notification(schedule)
                
                logger.info(f"Schedule update notification result: {notification_result}")
                
                # Add notification info to response
                return JsonResponse({
                    'success': True,
                    'notification_sent': notification_result.get('success', False),
                    'recipients_count': notification_result.get('recipients_count', 0),
                    'message': f"Schedule updated successfully. {notification_result.get('message', '')}"
                })
            except Exception as notif_error:
                logger.error(f"Failed to send schedule update notification: {str(notif_error)}")
                # Still return success for schedule update even if notification fails
                return JsonResponse({
                    'success': True,
                    'notification_sent': False,
                    'message': 'Schedule updated successfully but notifications failed to send'
                })
                
        except Exception as e:
            logger.error(f"Error editing schedule: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False})


def delete_schedule(request):
    if request.method == 'POST':
        try:
            schedule_id = request.POST.get('id')
            schedule = GarbageSchedule.objects.get(id=schedule_id)
            
            # Send email notifications before deleting
            try:
                from accounts import schedule_notification_service
                notification_result = schedule_notification_service.send_schedule_deleted_notification(schedule)
                
                logger.info(f"Schedule deletion notification result: {notification_result}")
            except Exception as notif_error:
                logger.error(f"Failed to send schedule deletion notification: {str(notif_error)}")
            
            # Delete the schedule
            schedule.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Schedule deleted and users notified'
            })
            
        except Exception as e:
            logger.error(f"Error deleting schedule: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False})


