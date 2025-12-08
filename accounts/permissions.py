from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from cenro.models import AdminUser

def admin_required(permission=None, view_only=False):
    """
    Decorator to check if user is admin and has required permissions
    
    Args:
        permission: Required permission (e.g., 'can_manage_users')
        view_only: If True, allows view_all permission as alternative
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated and is admin
            if not request.user.is_authenticated:
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'error': 'Authentication required'}, status=401)
                return redirect('admin_login')
            
            try:
                admin_user = AdminUser.objects.get(username=request.user.username, is_active=True)
            except AdminUser.DoesNotExist:
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'error': 'Admin access required'}, status=403)
                messages.error(request, 'Admin access required')
                return redirect('admin_login')
            
            # Check specific permission if required
            if permission:
                has_permission = getattr(admin_user, permission, False)
                
                # Allow view_all as alternative for view-only access
                if view_only and not has_permission:
                    has_permission = admin_user.can_view_all
                
                if not has_permission:
                    if request.headers.get('Content-Type') == 'application/json':
                        return JsonResponse({'error': 'Insufficient permissions'}, status=403)
                    messages.error(request, 'You do not have permission to access this section')
                    return redirect('admin_dashboard')
            
            # Add admin_user to request for easy access in views
            request.admin_user = admin_user
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator

def get_admin_context(request):
    """
    Get admin context data for templates
    """
    try:
        admin_user = AdminUser.objects.get(username=request.user.username, is_active=True)
        return {
            'admin_user': admin_user,
            'is_super_admin': admin_user.role == 'super_admin',
            'can_manage_users': admin_user.can_manage_users,
            'can_manage_controls': admin_user.can_manage_controls,
            'can_manage_points': admin_user.can_manage_points,
            'can_manage_rewards': admin_user.can_manage_rewards,
            'can_manage_schedules': admin_user.can_manage_schedules,
            'can_manage_security': admin_user.can_manage_security,
            'can_manage_learning': admin_user.can_manage_learning,
            'can_manage_games': admin_user.can_manage_games,
            'can_view_all': admin_user.can_view_all,
        }
    except AdminUser.DoesNotExist:
        return {}

def check_admin_permission(user, permission, view_only=False):
    """
    Check if user has admin permission
    
    Args:
        user: User object
        permission: Permission to check (e.g., 'can_manage_users')
        view_only: If True, allows view_all permission as alternative
    
    Returns:
        bool: True if user has permission
    """
    try:
        admin_user = AdminUser.objects.get(username=user.username, is_active=True)
        has_permission = getattr(admin_user, permission, False)
        
        # Allow view_all as alternative for view-only access
        if view_only and not has_permission:
            has_permission = admin_user.can_view_all
        
        return has_permission
    except AdminUser.DoesNotExist:
        return False
