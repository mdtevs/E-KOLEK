"""
Game and quiz management views
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
from game.models import Question, Choice, WasteCategory, WasteItem, GameConfiguration
from learn.models import LearningVideo, VideoWatchHistory

from ..admin_auth import admin_required, role_required, permission_required

logger = logging.getLogger(__name__)

import json
import time


@admin_required
@permission_required('can_manage_games')
def admingames(request):
    """View for admin games management"""
    categories = WasteCategory.objects.all().prefetch_related('items')
    items = WasteItem.objects.all().select_related('category')
    questions = Question.objects.all().prefetch_related('choices')
    
    # Get or create game configurations
    game_configs = {}
    admin_username = request.session.get('admin_user', {}).get('username', 'system')
    
    for game_type, _ in GameConfiguration.GAME_TYPE_CHOICES:
        try:
            config = GameConfiguration.objects.get(game_type=game_type)
            game_configs[game_type] = config
        except GameConfiguration.DoesNotExist:
            # Create with minimal defaults - admin will set actual values
            config = GameConfiguration.objects.create(
                game_type=game_type,
                cooldown_hours=0,
                cooldown_minutes=0,
                is_active=False,
                updated_by=admin_username
            )
            game_configs[game_type] = config
    
    return render(request, 'admingames.html', {
        'categories': categories,
        'items': items,
        'questions': questions,
        'game_configs': game_configs,
        'timestamp': int(time.time()),
    })


@admin_required
@permission_required('can_manage_games')
def adminquiz(request):
    """View for admin quiz management"""
    questions = Question.objects.all().prefetch_related('choices')
    return render(request, 'adminquiz.html', {'questions': questions, 'timestamp': int(time.time()),})


def add_question(request):
    if request.method == 'POST':
        from decimal import Decimal
        
        question_text = request.POST.get('question_text')
        question_points = Decimal(request.POST.get('question_points', '1'))
        choices_json = request.POST.get('choices')
        correct_choice_index = int(request.POST.get('correct_choice'))
        
        # Create question
        question = Question.objects.create(text=question_text, points=question_points)
        
        # Create choices
        choices = json.loads(choices_json)
        for i, choice_text in enumerate(choices):
            Choice.objects.create(
                question=question,
                text=choice_text,
                is_correct=(i == correct_choice_index)
            )
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


def delete_question(request, question_id):
    if request.method == 'DELETE':
        try:
            question = Question.objects.get(id=question_id)
            question.delete()
            return JsonResponse({'success': True})
        except Question.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Question not found'})
    
    return JsonResponse({'success': False})

# Category management views


# Category management views
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        color_hex = request.POST.get('color_hex')
        icon_name = request.POST.get('icon_name')
        description = request.POST.get('description', '')
        
        try:
            category = WasteCategory.objects.create(
                name=name,
                color_hex=color_hex,
                icon_name=icon_name,
                description=description
            )
            return JsonResponse({'success': True, 'id': str(category.id)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False})


def delete_category(request, category_id):
    if request.method == 'DELETE':
        try:
            category = WasteCategory.objects.get(id=category_id)
            category.delete()
            return JsonResponse({'success': True})
        except WasteCategory.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Category not found'})
    
    return JsonResponse({'success': False})

# Item management views


# Item management views
def add_item(request):
    if request.method == 'POST':
        from decimal import Decimal
        
        name = request.POST.get('name')
        emoji = request.POST.get('emoji', '')
        category_id = request.POST.get('category')
        points = Decimal(request.POST.get('points', '10'))
        difficulty_level = request.POST.get('difficulty_level', 'easy')
        is_active = request.POST.get('is_active') == 'true'
        
        try:
            category = WasteCategory.objects.get(id=category_id)
            item = WasteItem.objects.create(
                name=name,
                emoji=emoji,
                category=category,
                points=points,
                difficulty_level=difficulty_level,
                is_active=is_active
            )
            return JsonResponse({'success': True, 'id': str(item.id)})
        except WasteCategory.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Category not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False})


def delete_item(request, item_id):
    if request.method == 'DELETE':
        try:
            item = WasteItem.objects.get(id=item_id)
            item.delete()
            return JsonResponse({'success': True})
        except WasteItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not found'})
    
    return JsonResponse({'success': False})


# Game Configuration Management
@csrf_exempt  # Exempt from default CSRF, we'll check manually
@admin_required
def update_game_cooldown(request):
    """Update game cooldown configuration"""
    # Manual CSRF token verification for AJAX requests
    if request.method == 'POST':
        csrf_token = request.headers.get('X-CSRFToken') or request.POST.get('csrfmiddlewaretoken')
        if not csrf_token:
            logger.error("CSRF token missing in request")
            return JsonResponse({'success': False, 'error': 'CSRF token missing'}, status=403)
        
        # Verify the CSRF token matches
        from django.middleware.csrf import get_token
        expected_token = get_token(request)
        if csrf_token != expected_token:
            logger.error(f"CSRF token mismatch. Got: {csrf_token[:10]}..., Expected: {expected_token[:10]}...")
            return JsonResponse({'success': False, 'error': 'CSRF verification failed'}, status=403)
    
    # Log incoming request for debugging
    logger.info(f"Cooldown update request received from {request.session.get('admin_username', 'unknown')}")
    logger.info(f"POST data: {dict(request.POST)}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    if request.method == 'POST':
        try:
            game_type = request.POST.get('game_type', 'all')
            cooldown_hours = int(request.POST.get('cooldown_hours', 0))
            cooldown_minutes = int(request.POST.get('cooldown_minutes', 0))
            # Checkbox value is 'on' when checked, None when unchecked
            is_active = request.POST.get('is_active') == 'on'
            
            logger.info(f"Parsed values - Type: {game_type}, Hours: {cooldown_hours}, Minutes: {cooldown_minutes}, Active: {is_active}")
            
            # Validate input
            if cooldown_hours < 0 or cooldown_hours > 720:  # Max 30 days
                return JsonResponse({
                    'success': False, 
                    'error': 'Hours must be between 0 and 720 (30 days)'
                })
            
            if cooldown_minutes < 0 or cooldown_minutes > 59:
                return JsonResponse({
                    'success': False, 
                    'error': 'Minutes must be between 0 and 59'
                })
            
            # Get admin information from session (set during login)
            admin_username = request.session.get('admin_username', 'unknown')
            admin_full_name = request.session.get('admin_full_name', admin_username)
            
            # Update or create configuration
            config, created = GameConfiguration.objects.update_or_create(
                game_type=game_type,
                defaults={
                    'cooldown_hours': cooldown_hours,
                    'cooldown_minutes': cooldown_minutes,
                    'is_active': is_active,
                    'updated_by': admin_full_name  # Use full name for better tracking
                }
            )
            
            # Log action with detailed information
            action_status = 'created' if created else 'updated'
            status_text = 'ACTIVE' if is_active else 'INACTIVE'
            logger.info(
                f"Game cooldown {action_status} by {admin_full_name} ({admin_username}): "
                f"{game_type} - {cooldown_hours}h {cooldown_minutes}m ({status_text})"
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Game cooldown configuration updated successfully',
                'config': {
                    'game_type': config.game_type,
                    'cooldown_hours': config.cooldown_hours,
                    'cooldown_minutes': config.cooldown_minutes,
                    'is_active': config.is_active,
                    'formatted_duration': config.get_formatted_duration(),
                    'total_milliseconds': config.total_cooldown_milliseconds
                }
            })
            
        except ValueError as e:
            logger.error(f"ValueError in cooldown update: {str(e)}")
            logger.error(f"POST data that caused error: {dict(request.POST)}")
            return JsonResponse({'success': False, 'error': f'Invalid numeric value: {str(e)}'})
        except Exception as e:
            logger.error(f"Exception in cooldown update: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"POST data: {dict(request.POST)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'{type(e).__name__}: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@admin_required
@permission_required('can_manage_games')
def get_game_cooldown(request, game_type):
    """Get game cooldown configuration for a specific game type"""
    try:
        config = GameConfiguration.objects.get(game_type=game_type)
        return JsonResponse({
            'success': True,
            'config': {
                'game_type': config.game_type,
                'game_type_display': config.get_game_type_display(),
                'cooldown_hours': config.cooldown_hours,
                'cooldown_minutes': config.cooldown_minutes,
                'is_active': config.is_active,
                'formatted_duration': config.get_formatted_duration(),
                'total_minutes': config.total_cooldown_minutes,
                'total_milliseconds': config.total_cooldown_milliseconds,
                'updated_by': config.updated_by,
                'updated_at': config.updated_at.isoformat()
            }
        })
    except GameConfiguration.DoesNotExist:
        # Return unconfigured state
        return JsonResponse({
            'success': True,
            'config': {
                'game_type': game_type,
                'cooldown_hours': 0,
                'cooldown_minutes': 0,
                'is_active': False,
                'formatted_duration': 'Not configured',
                'total_minutes': 0,
                'total_milliseconds': 0
            }
        })
    except Exception as e:
        logger.error(f"Error getting game cooldown: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


# def function for adminuser edit user, delete user, and view user


