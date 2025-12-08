"""
Reward management and redemption views
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
from django.core.paginator import Paginator


# adminrewards - views for admin rewards
@admin_required
@permission_required('can_manage_rewards')
def adminrewards(request):
    rewards = Reward.objects.all()
    categories = RewardCategory.objects.filter(is_active=True)
    
    # Get recent history for the dashboard
    recent_history = RewardHistory.objects.select_related('reward', 'admin_user', 'user').order_by('-timestamp')[:20]
    
    return render(request, 'adminrewards.html', {
        'rewards': rewards,
        'categories': categories,
        'recent_history': recent_history,
        'timestamp': int(time.time()),
    })


@admin_required
@permission_required('can_manage_rewards')
def reward_history(request):
    """View for displaying detailed reward and stock history"""
    # Get filter parameters
    reward_id = request.GET.get('reward')
    action_filter = request.GET.get('action')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Build query
    history = RewardHistory.objects.select_related('reward', 'admin_user', 'user', 'redemption').order_by('-timestamp')
    
    # Apply filters
    if reward_id:
        history = history.filter(reward_id=reward_id)
    if action_filter:
        history = history.filter(action=action_filter)
    if date_from:
        from datetime import datetime
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        history = history.filter(timestamp__date__gte=date_from_obj.date())
    if date_to:
        from datetime import datetime
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        history = history.filter(timestamp__date__lte=date_to_obj.date())
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(history, 50)  # Show 50 entries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get rewards for filter dropdown
    rewards = Reward.objects.all().order_by('name')
    
    # Get admin permissions for sidebar
    admin_user = request.admin_user
    can_manage_users = admin_user.can_manage_users
    can_manage_controls = admin_user.can_manage_controls
    can_manage_points = admin_user.can_manage_points
    can_manage_rewards = admin_user.can_manage_rewards
    can_manage_schedules = admin_user.can_manage_schedules
    can_manage_security = admin_user.can_manage_security
    can_manage_learning = admin_user.can_manage_learning
    can_manage_games = admin_user.can_manage_games
    
    context = {
        'page_obj': page_obj,
        'rewards': rewards,
        'selected_reward': reward_id,
        'selected_action': action_filter,
        'date_from': date_from,
        'date_to': date_to,
        'action_choices': RewardHistory.ACTION_CHOICES,
        'timestamp': int(time.time()),
        'admin_user': admin_user,
        'can_manage_users': can_manage_users,
        'can_manage_controls': can_manage_controls,
        'can_manage_points': can_manage_points,
        'can_manage_rewards': can_manage_rewards,
        'can_manage_schedules': can_manage_schedules,
        'can_manage_security': can_manage_security,
        'can_manage_learning': can_manage_learning,
        'can_manage_games': can_manage_games,
    }
    
    return render(request, 'reward_history.html', context)

# Stock management views


@admin_required
@permission_required('can_manage_rewards')
def add_reward(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            category_id = request.POST.get('category')
            points_required = request.POST.get('points')
            stock = request.POST.get('stock')
            description = request.POST.get('description')
            image = request.FILES.get('image')

            # Log received data for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"=== ADD REWARD REQUEST ===")
            logger.info(f"Name: {name}")
            logger.info(f"Category ID: {category_id}")
            logger.info(f"Points: {points_required}")
            logger.info(f"Stock: {stock}")
            logger.info(f"Has image: {bool(image)}")
            if image:
                logger.info(f"Image filename: {image.name}")
                logger.info(f"Image size: {image.size} bytes")
                logger.info(f"Image content type: {image.content_type}")
            
            if image:
                logger.info(f"ADD REWARD - Name: {name}, Image: {image.name} ({image.size} bytes)")
            else:
                logger.info(f"ADD REWARD - Name: {name}, No image")

            if not all([name, category_id, points_required, stock, description, image]):
                missing_fields = []
                if not name: missing_fields.append('name')
                if not category_id: missing_fields.append('category')
                if not points_required: missing_fields.append('points')
                if not stock: missing_fields.append('stock')
                if not description: missing_fields.append('description')
                if not image: missing_fields.append('image')
                error_msg = f'Missing required fields: {", ".join(missing_fields)}'
                logger.warning(f"Add reward validation failed: {error_msg}")
                logger.warning(f"Validation failed: {error_msg}")
                return JsonResponse({'success': False, 'error': error_msg})

            try:
                category = RewardCategory.objects.get(id=category_id)
            except RewardCategory.DoesNotExist:
                error_msg = f'Category with ID {category_id} not found.'
                logger.error(error_msg)
                logger.error(error_msg)
                return JsonResponse({'success': False, 'error': error_msg})
            
            # Create reward - Django will automatically use the configured storage backend
            # If Google Drive fails, Django will fallback to local storage
            logger.info(f"Creating reward: {name}")
            logger.debug("Creating reward in database...")
            
            reward = Reward.objects.create(
                name=name,
                category=category,
                points_required=points_required,
                stock=stock,
                description=description,
                image=image  # Django handles storage backend automatically
            )
            
            logger.info(f"✅ Reward created successfully: {reward.id}")
            logger.info(f"Reward created! ID: {reward.id}")
            
            # Check if image was saved
            if reward.image:
                logger.info(f"✅ Image saved: {reward.image.name}")
                logger.info(f"Image saved to: {reward.image.name}")
                logger.info(f"Image URL: {reward.image_url}")
            else:
                logger.error("❌ Image field is NULL after save!")
                logger.warning("Image field is NULL after save!")
            
            # Create history record for reward creation
            admin_user = getattr(request, 'admin_user', None)
            reward.create_history(
                action='created',
                admin_user=admin_user,
                notes=f"Reward created with initial stock of {stock}"
            )
            
            # 🎁 Send email notifications to all users about the new reward
            try:
                from accounts.reward_notification_service import send_new_reward_notification
                notification_result = send_new_reward_notification(reward)
                
                if notification_result['success']:
                    logger.info(f"✅ Notification sent to {notification_result['recipients_count']} users")
                else:
                    logger.warning(f"⚠️ Notification failed: {notification_result.get('error', 'Unknown error')}")
            except Exception as notif_error:
                # Don't fail the reward creation if notification fails
                logger.error(f"Failed to send reward notifications: {str(notif_error)}")
            
            return JsonResponse({'success': True, 'id': str(reward.id)})
            
        except Exception as e:
            # Log the error for debugging
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Error creating reward: {str(e)}")
            logger.error(traceback.format_exc())
            logger.error(f"Error creating reward: {str(e)}")
            logger.debug(f"Full traceback: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'Error creating reward: {str(e)}'})
            
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@admin_required
@permission_required('can_manage_rewards')
def edit_reward(request):
    if request.method == 'POST':
        try:
            reward_id = request.POST.get('id')
            reward = Reward.objects.get(id=reward_id)
            
            # Track changes for history
            changes = []
            if reward.name != request.POST.get('name'):
                changes.append(f"Name: {reward.name} → {request.POST.get('name')}")
            
            reward.name = request.POST.get('name')
            category_id = request.POST.get('category')
            if category_id:
                new_category = RewardCategory.objects.get(id=category_id)
                if reward.category != new_category:
                    changes.append(f"Category: {reward.category} → {new_category}")
                reward.category = new_category
            
            new_points = request.POST.get('points')
            if str(reward.points_required) != new_points:
                changes.append(f"Points: {reward.points_required} → {new_points}")
            reward.points_required = new_points
            
            reward.description = request.POST.get('description')
            
            # Handle image update - Django will automatically use configured storage
            if request.FILES.get('image'):
                image = request.FILES.get('image')
                reward.image = image  # Django handles storage backend automatically
                changes.append("Image updated")
            
            reward.save()
            
            # Create history record for reward update
            if changes:
                admin_user = getattr(request, 'admin_user', None)
                reward.create_history(
                    action='updated',
                    admin_user=admin_user,
                    notes=f"Updated: {', '.join(changes)}"
                )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error updating reward: {str(e)}'})
            
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@admin_required
@permission_required('can_manage_rewards')
def delete_reward(request):
    if request.method == 'POST':
        try:
            reward_id = request.POST.get('id')
            reward = Reward.objects.get(id=reward_id)
            
            # Create history record before deletion
            admin_user = getattr(request, 'admin_user', None)
            reward.create_history(
                action='deleted',
                admin_user=admin_user,
                notes=f"Reward deleted (had {reward.stock} stock remaining)"
            )
            
            reward.delete()
            return JsonResponse({'success': True})
        except Reward.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Reward not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error deleting reward: {str(e)}'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


# Stock management views
@admin_required
@permission_required('can_manage_rewards')
def add_stock(request):
    if request.method == 'POST':
        try:
            reward_id = request.POST.get('reward_id')
            quantity = int(request.POST.get('quantity', 0))
            notes = request.POST.get('notes', '')
            
            if not reward_id or quantity <= 0:
                return JsonResponse({'success': False, 'error': 'Invalid data provided'})
            
            reward = Reward.objects.get(id=reward_id)
            
            # Get current admin user (assuming the admin is logged in as a Users object)
            admin_user = getattr(request, 'admin_user', None)
            
            # Use the new add_stock method which includes history tracking
            new_stock = reward.add_stock(
                quantity=quantity,
                admin_user=admin_user,
                notes=notes or f"Stock added via admin panel"
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'Added {quantity} units to {reward.name}. New stock: {new_stock}',
                'new_stock': new_stock
            })
        except Reward.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Reward not found'})
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid quantity'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})


@admin_required
@permission_required('can_manage_rewards')
def remove_stock(request):
    if request.method == 'POST':
        try:
            reward_id = request.POST.get('reward_id')
            quantity = int(request.POST.get('quantity', 0))
            notes = request.POST.get('notes', '')
            
            if not reward_id or quantity <= 0:
                return JsonResponse({'success': False, 'error': 'Invalid data provided'})
            
            reward = Reward.objects.get(id=reward_id)
            
            # Get current admin user
            admin_user = getattr(request, 'admin_user', None)
            
            # Use the new remove_stock method which includes history tracking
            new_stock = reward.remove_stock(
                quantity=quantity,
                admin_user=admin_user,
                notes=notes or f"Stock removed via admin panel"
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'Removed {quantity} units from {reward.name}. New stock: {new_stock}',
                'new_stock': new_stock
            })
        except ValueError as e:
            return JsonResponse({'success': False, 'error': str(e)})
        except Reward.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Reward not found'})
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid quantity'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})


# adminschedule - views for admin schedule


# Redeem Reward API
def redeem_reward_api(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        reward_id = request.POST.get("reward_id")

        try:
            # Find user directly by ID
            user = Users.objects.get(id=user_id, is_active=True, status='approved')
            reward = get_object_or_404(Reward, id=reward_id)

            if user.total_points < reward.points_required:
                return JsonResponse({"error": "Not enough points to redeem this reward."}, status=400)

            if reward.stock <= 0:
                return JsonResponse({"error": "This reward is out of stock."}, status=400)

            # Deduct points
            user.total_points -= reward.points_required
            user.save()
            
            # Update family points as well
            family = user.family
            family.total_family_points -= reward.points_required
            family.save()

            # Create redemption (this will automatically reduce stock and create history)
            redemption = Redemption.objects.create(
                user=user,
                reward=reward,
                points_used=reward.points_required,
                requested_by=user
            )

            # Log points transaction
            PointsTransaction.objects.create(
                user=user,
                transaction_type="redeemed",
                points_amount=reward.points_required,
                description=f"Redeemed reward: {reward.name}",
                reference_id=redemption.id
            )

            # Notify user
            Notification.objects.create(
                user=redemption.user,
                type='redeem',
                message=f"You redeemed {redemption.reward.name} for {redemption.points_used} points.",
                points=redemption.points_used,
                reward_name=redemption.reward.name
            )

            return JsonResponse({"message": f"Successfully redeemed {reward.name}!"})
        
        except Users.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

    return JsonResponse({"error": "Invalid request."}, status=400)


# Learning Videos Management Views


