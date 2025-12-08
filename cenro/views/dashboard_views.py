"""
Dashboard views for CENRO admin panel
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime, timedelta

from accounts.models import (
    Users, Family, Barangay, PointsTransaction, Reward, GarbageSchedule,
    WasteType, WasteTransaction, Redemption, Notification, RewardHistory
)
from cenro.models import AdminActionHistory
from learn.models import LearningVideo

from ..admin_auth import admin_required, permission_required


@admin_required
def dashboard(request):
    """Main admin landing page with quick access to all features"""
    admin_user = request.admin_user
    
    # Get quick stats for dashboard cards
    stats = {
        'total_users': Users.objects.filter(status='approved').count(),
        'pending_users': Users.objects.filter(status='pending').count(),
        'total_families': Family.objects.filter(status='approved').count(),
        'total_points_distributed': PointsTransaction.objects.filter(transaction_type='add').aggregate(Sum('points_amount'))['points_amount__sum'] or 0,
        'active_rewards': Reward.objects.filter(is_active=True).count(),
        'total_redemptions': Redemption.objects.count(),
        'waste_types': WasteType.objects.count(),
        'learning_videos': LearningVideo.objects.filter(is_active=True).count(),
        
        # Waste Collection Analytics
        'total_waste_collected': WasteTransaction.objects.aggregate(Sum('waste_kg'))['waste_kg__sum'] or 0,
        'waste_transactions_count': WasteTransaction.objects.count(),
        'waste_collected_this_month': WasteTransaction.objects.filter(
            transaction_date__gte=timezone.now().replace(day=1).date()
        ).aggregate(Sum('waste_kg'))['waste_kg__sum'] or 0,
    }
    
    # Recent activities (last 10 actions)
    recent_actions = AdminActionHistory.objects.select_related('admin_user').order_by('-timestamp')[:10]
    
    context = {
        'admin_user': admin_user,
        'stats': stats,
        'recent_actions': recent_actions,
    }
    
    return render(request, 'admin_landing.html', context)


@admin_required
def admin_preview_user_dashboard(request, user_id=None):
    """
    Allow admins to preview the user dashboard without affecting admin session.
    Admins remain logged in as admin while viewing user's dashboard data.
    
    Security:
    - Admin must be authenticated via @admin_required
    - Admin must have 'can_view_all' permission OR be a super_admin
    - Admin session is preserved (no session switching)
    - Only approved users can be previewed
    - All preview actions are logged for audit
    """
    admin_user = request.admin_user
    
    # Verify admin has permission to preview (super_admin or can_view_all)
    if not (admin_user.role == 'super_admin' or admin_user.can_view_all):
        messages.error(request, 'You do not have permission to preview user dashboards.')
        return redirect('cenro:dashboard')
    
    # Verify admin session is still active and hasn't been compromised
    if not request.session.get('admin_user_id'):
        messages.error(request, 'Admin session expired. Please log in again.')
        return redirect('cenro:admin_login')
    
    # Get a user to preview (either specified or first approved user)
    if user_id:
        try:
            preview_user = Users.objects.select_related('family', 'family__barangay').get(
                id=user_id, 
                status='approved'
            )
        except Users.DoesNotExist:
            messages.error(request, 'User not found or not approved.')
            return redirect('cenro:dashboard')
    else:
        # Get first approved user as sample
        preview_user = Users.objects.filter(status='approved').select_related('family', 'family__barangay').first()
        if not preview_user:
            messages.warning(request, 'No approved users found to preview.')
            return redirect('cenro:dashboard')
    
    # Build context similar to user dashboard
    schedules = GarbageSchedule.objects.filter(barangay=preview_user.get_barangay()).order_by('day', 'start_time')
    
    today = datetime.now().strftime('%A')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%A')
    
    enhanced_schedules = []
    for schedule in schedules:
        schedule.is_today = schedule.day == today
        schedule.is_tomorrow = schedule.day == tomorrow
        enhanced_schedules.append(schedule)
    
    enhanced_schedules.sort(key=lambda x: (not x.is_today, not x.is_tomorrow, x.day, x.start_time))
    
    rewards = Reward.objects.filter(is_active=True)
    notifications = Notification.objects.filter(user=preview_user).order_by('-created_at')[:20]
    
    # User Leaderboard
    user_leaderboard_qs = Users.objects.filter(
        status='approved',
        total_points__gt=0
    ).order_by('-total_points')[:10]
    
    user_leaderboard = []
    for i, leaderboard_user in enumerate(user_leaderboard_qs):
        user_leaderboard.append({
            'rank': i + 1,
            'full_name': leaderboard_user.full_name,
            'points': leaderboard_user.total_points,
            'family_name': leaderboard_user.family.family_name if leaderboard_user.family else 'No Family',
            'is_current_user': leaderboard_user.id == preview_user.id
        })
    
    # Barangay Leaderboard
    barangay_leaderboard_qs = (
        Family.objects.filter(status='approved', total_family_points__gt=0)
        .values('barangay__name')
        .annotate(points=Sum('total_family_points'))
        .filter(points__gt=0)
        .order_by('-points')[:10]
    )
    
    barangay_leaderboard = []
    for i, entry in enumerate(barangay_leaderboard_qs):
        barangay_leaderboard.append({
            'rank': i + 1,
            'barangay_name': entry['barangay__name'],
            'points': entry['points']
        })
    
    family_member_leaderboard = preview_user.family.members.filter(is_active=True).order_by('-total_points')[:5]
    
    referred_users_count = Users.objects.filter(referred_by_code=preview_user.referral_code, status='approved').count()
    referral_points_earned = referred_users_count * 10
    
    # Log admin action for security audit
    AdminActionHistory.objects.create(
        admin_user=admin_user,
        action='view_users',
        description=f"Previewed user dashboard for {preview_user.full_name} ({preview_user.family.family_code if preview_user.family else 'No Family'})",
        details={
            'user_id': str(preview_user.id),
            'user_name': preview_user.full_name,
            'family_code': preview_user.family.family_code if preview_user.family else None,
            'action_type': 'preview_dashboard'
        },
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
        user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')[:255] if request.META.get('HTTP_USER_AGENT') else 'Unknown'
    )
    
    context = {
        'user': preview_user,  # The user being previewed
        'schedules': enhanced_schedules,
        'rewards': rewards,
        'notifications': notifications,
        'user_leaderboard': user_leaderboard,
        'barangay_leaderboard': barangay_leaderboard,
        'family_member_leaderboard': family_member_leaderboard,
        'referred_users_count': referred_users_count,
        'referral_points_earned': referral_points_earned,
        'is_admin_preview': True,  # Flag to indicate this is admin preview
        'admin_user': admin_user,  # The admin who is viewing (maintains admin identity)
        'preview_mode': True,  # Additional flag for template logic
    }
    
    return render(request, 'admin_user_dashboard_preview.html', context)


@admin_required
def get_dashboard_metrics(request):
    """
    API endpoint to get dashboard metrics for AJAX refresh
    Available to all admin users
    """
    from accounts.models import LoginAttempt
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        last_24h = now - timedelta(hours=24)
        
        metrics = {
            'total_users': Users.objects.filter(is_active=True).count(),
            'new_users_today': Users.objects.filter(created_at__gte=today_start).count(),
            'login_attempts_24h': LoginAttempt.objects.filter(timestamp__gte=last_24h).count(),
            'redemptions_today': Redemption.objects.filter(redemption_date__gte=today_start).count(),
            'admin_actions_today': AdminActionHistory.objects.filter(timestamp__gte=today_start).count(),
            'pending_redemptions': Redemption.objects.filter(claim_date__isnull=True).count(),
        }
        
        return JsonResponse(metrics)
        
    except Exception as e:
        logger.error(f"Error fetching dashboard metrics: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
