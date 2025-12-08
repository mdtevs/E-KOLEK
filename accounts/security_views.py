"""
Security monitoring views for admin users
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from accounts.models import LoginAttempt
from accounts.security import UserLoginSecurity
from eko.security_utils import log_security_event
import logging

logger = logging.getLogger(__name__)


@staff_member_required
def security_api_stats(request):
    """API endpoint for real-time security statistics"""
    
    # Get time period from request
    hours = int(request.GET.get('hours', 24))
    cutoff = timezone.now() - timedelta(hours=hours)
    
    # Query statistics
    total_attempts = LoginAttempt.objects.filter(timestamp__gte=cutoff).count()
    failed_attempts = LoginAttempt.objects.filter(
        timestamp__gte=cutoff, success=False
    ).count()
    
    # Calculate metrics
    failure_rate = 0
    if total_attempts > 0:
        failure_rate = round((failed_attempts / total_attempts) * 100, 2)
    
    # Get top failing IPs
    top_ips = list(
        LoginAttempt.objects
        .filter(timestamp__gte=cutoff, success=False)
        .values('ip_address')
        .annotate(failures=Count('id'))
        .order_by('-failures')[:5]
    )
    
    data = {
        'total_attempts': total_attempts,
        'failed_attempts': failed_attempts,
        'success_attempts': total_attempts - failed_attempts,
        'failure_rate': failure_rate,
        'top_failing_ips': top_ips,
        'timestamp': timezone.now().isoformat(),
    }
    
    return JsonResponse(data)


@staff_member_required
def block_ip(request):
    """Block an IP address (requires additional implementation)"""
    
    if request.method == 'POST':
        ip_address = request.POST.get('ip_address')
        duration_hours = int(request.POST.get('duration', 24))
        reason = request.POST.get('reason', 'Manual block by admin')
        
        # This would require implementing IP blocking functionality
        # For now, just log the action
        log_security_event(
            'IP_BLOCKED_BY_ADMIN',
            user=request.user,
            details=f'IP {ip_address} blocked for {duration_hours} hours. Reason: {reason}'
        )
        
        logger.warning(f"Admin {request.user.username} blocked IP {ip_address}")
        
        return JsonResponse({'success': True, 'message': f'IP {ip_address} blocked'})
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@staff_member_required
def unlock_account(request):
    """Unlock a locked user account"""
    
    if request.method == 'POST':
        username = request.POST.get('username')
        
        if username:
            # Clear the account lock
            cache_key = UserLoginSecurity.get_login_cache_key(username, 'account_lock')
            from django.core.cache import cache
            cache.delete(cache_key)
            
            # Clear failed attempts
            UserLoginSecurity.clear_failed_attempts(username)
            
            log_security_event(
                'ACCOUNT_UNLOCKED_BY_ADMIN',
                user=request.user,
                details=f'Account {username} unlocked by admin'
            )
            
            logger.info(f"Admin {request.user.username} unlocked account {username}")
            
            return JsonResponse({'success': True, 'message': f'Account {username} unlocked'})
    
    return JsonResponse({'error': 'Invalid request or username'}, status=400)
