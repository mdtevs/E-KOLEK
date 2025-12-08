"""
Points and waste transaction views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from django.db import transaction, IntegrityError
import logging
import time

from accounts.models import (
    Users, Family, Barangay, PointsTransaction, Reward, GarbageSchedule, RewardCategory,
    WasteType, WasteTransaction, Redemption, Notification, RewardHistory
)
from cenro.models import AdminActionHistory
from game.models import Question, Choice, WasteCategory, WasteItem
from learn.models import LearningVideo, VideoWatchHistory

from ..admin_auth import admin_required, role_required, permission_required

logger = logging.getLogger(__name__)

import uuid
from django.utils.timezone import now


# adminpints - views for admin points
@admin_required
@permission_required('can_manage_points')
def adminpoints(request):
    waste_types = WasteType.objects.all()
    rewards = Reward.objects.filter(is_active=True, stock__gt=0)
    return render(request, 'adminpoints.html', {
        'waste_types': waste_types, 
        'rewards': rewards, 
        'timestamp': int(time.time()),
        'admin_user': request.admin_user,  # Add admin user context
    })


# adminrewards - views for admin rewards


# @ratelimit(key='ip', rate='30/m', method='POST')  # Temporarily disabled - requires Redis/Memcached for production
@admin_required
@require_POST
@csrf_exempt  # Only for admin API endpoints with admin_required decorator
def save_waste_transaction(request):
    """
    Secure admin waste transaction endpoint with proper validation
    """
    # Note: Rate limiting temporarily disabled - enable with Redis/Memcached in production
    # if getattr(request, 'limited', False):
    #     return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
    
    try:
        with transaction.atomic():
            # Input validation and sanitization
            user_id = request.POST.get("user_id", "").strip()
            waste_type_id = request.POST.get("waste_type", "").strip()
            waste_kg_str = request.POST.get("waste_kg", "0").strip()
            total_points_str = request.POST.get("total_points", "0").strip()
            
            # Validate UUIDs
            try:
                import uuid
                uuid.UUID(user_id)
                uuid.UUID(waste_type_id)
            except (ValueError, AttributeError):
                return JsonResponse({"message": "Invalid ID format"}, status=400)
            
            # Validate and convert numeric inputs
            try:
                waste_kg = float(waste_kg_str)
                total_points = float(total_points_str)
            except (ValueError, TypeError):
                return JsonResponse({"message": "Invalid numeric values"}, status=400)
            
            # Business logic validation
            if waste_kg <= 0 or waste_kg > 1000:  # Reasonable limits
                return JsonResponse({"message": "Invalid waste weight"}, status=400)
            
            if total_points <= 0 or total_points > 100000:  # Reasonable limits
                return JsonResponse({"message": "Invalid points amount"}, status=400)
            
            # Find user and waste type with safe lookups
            try:
                user = Users.objects.get(id=user_id, is_active=True, status='approved')
                waste_type = WasteType.objects.get(id=waste_type_id)
            except Users.DoesNotExist:
                return JsonResponse({"message": "User not found"}, status=404)
            except WasteType.DoesNotExist:
                return JsonResponse({"message": "Invalid waste type"}, status=404)
            
            # Validate points calculation (prevent manipulation)
            expected_points = waste_kg * waste_type.points_per_kg
            if abs(total_points - expected_points) > 0.01:  # Allow for small rounding differences
                return JsonResponse({"message": "Points calculation mismatch"}, status=400)
            
            # Get barangay from user's family
            barangay = user.family.barangay if user.family else None
            
            # Create transaction record with new fields
            transaction_obj = WasteTransaction.objects.create(
                user=user,
                waste_type=waste_type,
                waste_kg=waste_kg,
                total_points=total_points,
                processed_by=request.admin_user,
                barangay=barangay,
                created_at=now()
            )
            
            # Update user points
            user.total_points += total_points
            user.save(update_fields=['total_points'])
            
            # Update family points
            family = user.family
            family.total_family_points += total_points
            family.save(update_fields=['total_family_points'])
            
            # Create notification
            Notification.objects.create(
                user=user,
                type='waste',
                message=f"You earned {int(total_points)} points for your waste collection.",
                points=int(total_points)
            )
            
            # Log admin action for audit trail
            from cenro.models import AdminActionHistory
            AdminActionHistory.objects.create(
                admin_user=request.admin_user,
                action='manage_controls',  # Using existing action choice
                description=f'Added waste transaction: {waste_kg}kg of {waste_type.name} for {total_points} points',
                details={
                    'user_id': str(user.id),
                    'user_name': user.full_name,
                    'waste_type': waste_type.name,
                    'waste_kg': waste_kg,
                    'total_points': total_points
                },
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
                user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')[:500]
            )
            
            return JsonResponse({
                "message": "Transaction saved successfully!",
                "transaction_id": str(transaction_obj.id),
                "new_total_points": user.total_points
            })
            
    except Exception as e:
        # Log error for debugging but don't expose details to client
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in save_waste_transaction: {str(e)}")
        return JsonResponse({"message": "Transaction failed"}, status=500)


