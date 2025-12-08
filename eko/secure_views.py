"""
Secure API views with proper validation and protection
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)

from accounts.models import Users, WasteType, WasteTransaction, Family
from game.models import Question, Choice  # Import Question and Choice models for quiz questions
from cenro.admin_auth import admin_required  # Import custom admin authentication
from eko.security_utils import (
    validate_user_input, validate_uuid, validate_points_amount, 
    validate_weight, safe_get_object_or_404, sanitize_query_params,
    log_security_event, get_client_ip
)


@ratelimit(key='ip', rate='10/m', method='POST')
@require_POST
@login_required  # Ensure user is logged in for transactions
@never_cache
def secure_save_waste_transaction(request):
    """
    Secure version of waste transaction saving with proper validation
    """
    if getattr(request, 'limited', False):
        log_security_event(
            'RATE_LIMIT_EXCEEDED', 
            ip_address=get_client_ip(request),
            details='waste transaction endpoint'
        )
        return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
    
    try:
        with transaction.atomic():
            # Validate and sanitize input
            user_id = validate_uuid(request.POST.get("user_id", "").strip())
            waste_type_id = validate_uuid(request.POST.get("waste_type", "").strip())
            waste_kg = validate_weight(request.POST.get("waste_kg", "0"))
            total_points = validate_points_amount(request.POST.get("total_points", "0"))

            # Verify user exists and is authorized
            user = safe_get_object_or_404(Users, id=user_id, is_active=True, status='approved')
            waste_type = safe_get_object_or_404(WasteType, id=waste_type_id)

            # Validate business logic
            expected_points = waste_kg * waste_type.points_per_kg
            if abs(total_points - expected_points) > 0.01:  # Allow for small rounding differences
                log_security_event(
                    'POINTS_MANIPULATION_ATTEMPT',
                    user=user,
                    ip_address=get_client_ip(request),
                    details=f'Expected: {expected_points}, Received: {total_points}'
                )
                return JsonResponse({'error': 'Invalid points calculation'}, status=400)

            # Save transaction
            transaction_obj = WasteTransaction.objects.create(
                user=user,
                waste_type=waste_type,
                waste_kg=waste_kg,
                total_points=total_points,
                created_at=timezone.now()
            )

            # Update user points
            user.total_points += total_points
            user.save(update_fields=['total_points'])

            # Update family points
            family = user.family
            family.total_family_points += total_points
            family.save(update_fields=['total_family_points'])

            # Create notification for waste transaction
            from accounts.models import Notification
            Notification.objects.create(
                user=user,
                type='waste',
                message=f'You earned {total_points} points from waste collection ({waste_kg}kg of {waste_type.name}).',
                points=total_points
            )

            log_security_event(
                'WASTE_TRANSACTION_SUCCESS',
                user=user,
                ip_address=get_client_ip(request),
                details=f'Points: {total_points}, Weight: {waste_kg}kg'
            )

            return JsonResponse({
                'success': True,
                'transaction_id': str(transaction_obj.id),
                'new_total_points': user.total_points
            })

    except ValidationError as e:
        log_security_event(
            'VALIDATION_ERROR',
            ip_address=get_client_ip(request),
            details=f'Waste transaction: {str(e)}'
        )
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        log_security_event(
            'TRANSACTION_ERROR',
            ip_address=get_client_ip(request),
            details=f'Waste transaction: {str(e)}'
        )
        return JsonResponse({'error': 'Transaction failed'}, status=500)


@ratelimit(key='ip', rate='20/m', method='GET')
@require_http_methods(["GET"])
@never_cache
def secure_get_user_by_id(request):
    """
    Secure version of user lookup by ID
    """
    if getattr(request, 'limited', False):
        return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
    
    try:
        # Validate and sanitize input
        user_id = validate_uuid(request.GET.get('id', '').strip())
        
        # Get user securely
        user = safe_get_object_or_404(Users, id=user_id, is_active=True, status='approved')
        
        return JsonResponse({
            'name': validate_user_input(user.full_name),
            'family_code': validate_user_input(user.family.family_code),
            'total_points': user.total_points,
            'user_id': str(user.id),
            'family_id': str(user.family.id)
        })
        
    except ValidationError as e:
        log_security_event(
            'INVALID_USER_LOOKUP',
            ip_address=get_client_ip(request),
            details=str(e)
        )
        return JsonResponse({'error': 'Invalid user ID'}, status=400)
    except Users.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


@ratelimit(key='ip', rate='20/m', method='GET')
@require_http_methods(["GET"])
@never_cache
def secure_get_user_by_family_code(request):
    """
    Secure version of user lookup by family code
    """
    if getattr(request, 'limited', False):
        return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
    
    try:
        # Validate and sanitize input
        code = validate_user_input(request.GET.get('code', '').strip(), max_length=20)
        
        if not code:
            return JsonResponse({'name': '', 'family_code': ''})
        
        # Find family by family_code
        family = Family.objects.filter(family_code=code).first()
        
        if not family:
            return JsonResponse({'name': '', 'family_code': ''})
        
        # Get the family representative or first active user
        user = family.members.filter(is_active=True, status='approved').first()
        
        if user:
            return JsonResponse({
                'name': validate_user_input(user.full_name),
                'family_code': validate_user_input(family.family_code)
            })
        
        return JsonResponse({'name': '', 'family_code': ''})
        
    except Exception as e:
        log_security_event(
            'FAMILY_CODE_LOOKUP_ERROR',
            ip_address=get_client_ip(request),
            details=str(e)
        )
        return JsonResponse({'error': 'Lookup failed'}, status=500)


@ratelimit(key='ip', rate='5/m', method='POST')
@require_POST
@require_POST  # Only allow POST requests for adding questions
@admin_required  # Use custom admin authentication
@never_cache
def secure_add_question(request):
    """
    Secure version of adding quiz questions (admin only)
    """
    if getattr(request, 'limited', False):
        return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
    
    # Admin authentication is handled by @admin_required decorator
    # No need to check is_staff or is_superuser since we're using custom admin system
    
    # Debug logging
    logger.info(f"secure_add_question called by admin: {getattr(request, 'admin_user', 'Unknown')}")
    logger.info(f"POST data keys: {list(request.POST.keys())}")
    logger.info(f"Content-Type: {request.META.get('CONTENT_TYPE', 'Unknown')}")
    logger.info(f"CSRF token in POST: {'csrfmiddlewaretoken' in request.POST}")
    logger.info(f"X-CSRFToken header: {request.META.get('HTTP_X_CSRFTOKEN', 'Not present')}")
    
    try:
        with transaction.atomic():
            # Validate and sanitize input
            question_text = validate_user_input(
                request.POST.get('question_text', ''), 
                max_length=500, 
                allow_special_chars=True
            )
            question_points = validate_points_amount(request.POST.get('question_points', '1'))
            choices_json = request.POST.get('choices', '[]')
            correct_choice_index = int(request.POST.get('correct_choice', 0))
            
            if not question_text:
                return JsonResponse({'error': 'Question text is required'}, status=400)
            
            # Validate choices JSON
            try:
                choices = json.loads(choices_json)
                if not isinstance(choices, list) or len(choices) < 2:
                    return JsonResponse({'error': 'At least 2 choices required'}, status=400)
                
                if correct_choice_index >= len(choices):
                    return JsonResponse({'error': 'Invalid correct choice index'}, status=400)
                
                # Sanitize choice texts
                choices = [validate_user_input(choice, max_length=200, allow_special_chars=True) 
                          for choice in choices]
                
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid choices format'}, status=400)
            
            # Create question and choices using Django ORM (prevents SQL injection)
            question = Question.objects.create(
                text=question_text, 
                points=int(question_points)
            )
            
            for i, choice_text in enumerate(choices):
                Choice.objects.create(
                    question=question,
                    text=choice_text,
                    is_correct=(i == correct_choice_index)
                )
            
            log_security_event(
                'QUIZ_QUESTION_ADDED',
                user=getattr(request, 'admin_user', None),  # Use admin_user set by decorator
                ip_address=get_client_ip(request),
                details=f'Question ID: {question.id}'
            )
            
            return JsonResponse({'success': True, 'question_id': question.id})
            
    except ValidationError as e:
        logger.error(f"Validation error in secure_add_question: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Exception in secure_add_question: {str(e)}")
        log_security_event(
            'QUESTION_CREATION_ERROR',
            user=getattr(request, 'admin_user', None),  # Use admin_user consistently
            ip_address=get_client_ip(request),
            details=str(e)
        )
        return JsonResponse({'error': f'Failed to create question: {str(e)}'}, status=500)
