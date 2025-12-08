"""
Learning videos and quiz management views
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

import json
import time
from django.db import models
from learn.models import QuizQuestion, QuizResult, QuizAnswer


# Learning Videos Management Views
@admin_required
@permission_required('can_manage_learning')
def adminlearn(request):
    """View for admin learning videos management"""
    videos = LearningVideo.objects.all().order_by('-created_at')
    return render(request, 'adminlearn.html', {'videos': videos, 'timestamp': int(time.time()),})


def add_video(request):
    """Add a new learning video"""
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            description = request.POST.get('description')
            video_url = request.POST.get('video_url')
            thumbnail_url = request.POST.get('thumbnail_url')
            points_reward = int(request.POST.get('points_reward', 0))
            is_active = request.POST.get('is_active') == 'true'
            
            if not all([title, description, video_url]):
                return JsonResponse({'success': False, 'error': 'Title, description, and video URL are required'})
            
            video = LearningVideo.objects.create(
                title=title,
                description=description,
                video_url=video_url,
                thumbnail_url=thumbnail_url if thumbnail_url else None,
                points_reward=points_reward,
                is_active=is_active
            )
            
            return JsonResponse({'success': True, 'message': 'Video added successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def edit_video(request):
    """Edit an existing learning video"""
    if request.method == 'POST':
        try:
            video_id = request.POST.get('video_id')
            title = request.POST.get('title')
            description = request.POST.get('description')
            video_url = request.POST.get('video_url')
            thumbnail_url = request.POST.get('thumbnail_url')
            points_reward = int(request.POST.get('points_reward', 0))
            is_active = request.POST.get('is_active') == 'true'
            
            if not video_id:
                return JsonResponse({'success': False, 'error': 'Video ID is required'})
            
            video = get_object_or_404(LearningVideo, id=video_id)
            
            video.title = title
            video.description = description
            video.video_url = video_url
            video.thumbnail_url = thumbnail_url if thumbnail_url else None
            video.points_reward = points_reward
            video.is_active = is_active
            video.save()
            
            return JsonResponse({'success': True, 'message': 'Video updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def toggle_video(request):
    """Toggle video active status"""
    if request.method == 'POST':
        try:
            video_id = request.POST.get('video_id')
            is_active = request.POST.get('is_active') == 'true'
            
            video = get_object_or_404(LearningVideo, id=video_id)
            video.is_active = is_active
            video.save()
            
            status = 'activated' if is_active else 'deactivated'
            return JsonResponse({'success': True, 'message': f'Video {status} successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def delete_video(request):
    """Delete a learning video"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            video_id = data.get('video_id')
            
            if not video_id:
                return JsonResponse({'success': False, 'error': 'Video ID is required'})
            
            video = get_object_or_404(LearningVideo, id=video_id)
            video.delete()
            
            return JsonResponse({'success': True, 'message': 'Video deleted successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# Security Dashboard - Admin Security Management


# ===============================
# QUIZ MANAGEMENT VIEWS
# ===============================

@admin_required
@permission_required('can_manage_learning')
def quiz_management(request):
    """Enhanced quiz management interface"""
    from learn.models import LearningVideo, QuizQuestion, QuizResult
    
    # Get all videos with quiz statistics
    videos = LearningVideo.objects.all().prefetch_related('quiz_questions')
    
    video_stats = []
    for video in videos:
        questions = video.quiz_questions.filter(is_active=True)
        quiz_results = QuizResult.objects.filter(video=video)
        
        video_stats.append({
            'video': video,
            'question_count': questions.count(),
            'total_attempts': quiz_results.count(),
            'pass_rate': quiz_results.filter(score_percentage__gte=70).count() / max(quiz_results.count(), 1) * 100,
            'avg_score': quiz_results.aggregate(avg_score=models.Avg('score_percentage'))['avg_score'] or 0,
            'has_quiz': questions.exists()
        })
    
    # Overall statistics
    total_questions = QuizQuestion.objects.filter(is_active=True).count()
    total_attempts = QuizResult.objects.count()
    total_passes = QuizResult.objects.filter(score_percentage__gte=70).count()
    overall_pass_rate = (total_passes / max(total_attempts, 1)) * 100
    
    context = {
        'video_stats': video_stats,
        'total_videos': videos.count(),
        'total_questions': total_questions,
        'total_attempts': total_attempts,
        'overall_pass_rate': overall_pass_rate,
        'timestamp': int(time.time()),
        'admin_user': request.admin_user,
        'page_name': 'quiz_management',
    }
    
    return render(request, 'admin_quiz_management.html', context)


@admin_required
@permission_required('can_manage_learning')
def quiz_questions(request, video_id):
    """Manage quiz questions for a specific video"""
    from learn.models import LearningVideo, QuizQuestion
    
    video = get_object_or_404(LearningVideo, id=video_id)
    questions = QuizQuestion.objects.filter(video=video).order_by('order')
    
    context = {
        'video': video,
        'questions': questions,
        'timestamp': int(time.time()),
        'admin_user': request.admin_user,
        'page_name': 'quiz_questions',
    }
    
    return render(request, 'admin_quiz_questions.html', context)


@admin_required
@permission_required('can_manage_learning')
def quiz_results(request, video_id=None):
    """View quiz results and analytics"""
    from learn.models import LearningVideo, QuizResult, QuizAnswer
    
    videos = LearningVideo.objects.all()
    results = QuizResult.objects.all().select_related('user', 'video')
    
    # Check for video_id from GET parameter or URL parameter
    video_id = request.GET.get('video_id') or video_id
    selected_video = None
    
    if video_id:
        try:
            selected_video = LearningVideo.objects.get(id=video_id)
            results = results.filter(video=selected_video)
        except LearningVideo.DoesNotExist:
            pass
    
    # Calculate analytics
    total_attempts = results.count()
    passed_attempts = results.filter(score_percentage__gte=70).count()
    failed_attempts = total_attempts - passed_attempts
    pass_rate = (passed_attempts / max(total_attempts, 1)) * 100
    
    # Score distribution
    score_ranges = {
        '90-100%': results.filter(score_percentage__gte=90).count(),
        '80-89%': results.filter(score_percentage__gte=80, score_percentage__lt=90).count(),
        '70-79%': results.filter(score_percentage__gte=70, score_percentage__lt=80).count(),
        '60-69%': results.filter(score_percentage__gte=60, score_percentage__lt=70).count(),
        'Below 60%': results.filter(score_percentage__lt=60).count(),
    }
    
    context = {
        'videos': videos,
        'selected_video': selected_video,
        'results': results[:50],  # Limit to recent 50 results
        'total_attempts': total_attempts,
        'passed_attempts': passed_attempts,
        'failed_attempts': failed_attempts,
        'pass_rate': pass_rate,
        'score_ranges': score_ranges,
        'timestamp': int(time.time()),
        'admin_user': request.admin_user,
        'page_name': 'quiz_results',
    }
    
    return render(request, 'admin_quiz_results.html', context)


# ===============================
# SECURITY DASHBOARD API VIEWS
# ===============================


@admin_required
@permission_required('can_manage_learning')
@require_POST
def add_quiz_question(request):
    """Add a new quiz question"""
    from learn.models import LearningVideo, QuizQuestion
    
    try:
        video_id = request.POST.get('video_id')
        video = get_object_or_404(LearningVideo, id=video_id)
        
        # Get the highest order number for this video
        max_order = QuizQuestion.objects.filter(video=video).aggregate(
            max_order=models.Max('order')
        )['max_order'] or 0
        
        question = QuizQuestion.objects.create(
            video=video,
            question_text=request.POST.get('question_text'),
            option_a=request.POST.get('option_a'),
            option_b=request.POST.get('option_b'),
            option_c=request.POST.get('option_c'),
            option_d=request.POST.get('option_d'),
            correct_answer=request.POST.get('correct_answer'),
            points_reward=int(request.POST.get('points_reward', 10)),
            explanation=request.POST.get('explanation', ''),
            order=max_order + 1,
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Question added successfully to "{video.title}"',
            'question_id': question.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@admin_required
@permission_required('can_manage_learning')
@require_POST
def edit_quiz_question(request):
    """Edit an existing quiz question"""
    from learn.models import QuizQuestion
    
    try:
        question_id = request.POST.get('question_id')
        question = get_object_or_404(QuizQuestion, id=question_id)
        
        question.question_text = request.POST.get('question_text')
        question.option_a = request.POST.get('option_a')
        question.option_b = request.POST.get('option_b')
        question.option_c = request.POST.get('option_c')
        question.option_d = request.POST.get('option_d')
        question.correct_answer = request.POST.get('correct_answer')
        question.points_reward = int(request.POST.get('points_reward', 10))
        question.explanation = request.POST.get('explanation', '')
        question.order = int(request.POST.get('order', question.order))
        question.is_active = request.POST.get('is_active') == 'true'
        question.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Question updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@admin_required
@permission_required('can_manage_learning')
@require_POST
def delete_quiz_question(request):
    """Delete a quiz question"""
    from learn.models import QuizQuestion
    
    try:
        question_id = request.POST.get('question_id')
        question = get_object_or_404(QuizQuestion, id=question_id)
        video_title = question.video.title
        question.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Question deleted from "{video_title}"'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@admin_required
@permission_required('can_manage_learning')
@require_POST
def toggle_quiz_question(request):
    """Toggle quiz question active status"""
    from learn.models import QuizQuestion
    
    try:
        question_id = request.POST.get('question_id')
        question = get_object_or_404(QuizQuestion, id=question_id)
        question.is_active = not question.is_active
        question.save()
        
        status = "activated" if question.is_active else "deactivated"
        
        return JsonResponse({
            'success': True,
            'message': f'Question {status} successfully',
            'new_status': question.is_active
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


