from accounts.permissions import get_admin_context

class AdminContextMiddleware:
    """
    Middleware to add admin context to all requests
    Uses Django session-based admin authentication
    Ensures admin sessions are isolated from user sessions
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check for session-based admin authentication
        admin_user_id = request.session.get('admin_user_id')
        if admin_user_id:
            try:
                from cenro.models import AdminUser
                admin_user = AdminUser.objects.get(id=admin_user_id, is_active=True)
                request.admin_user = admin_user
                request.is_admin_authenticated = True
                
                # Add admin context for templates
                request.admin_context = {
                    'admin_user': admin_user,
                    'admin_username': admin_user.username,
                    'admin_full_name': admin_user.full_name,
                    'admin_role': admin_user.role,
                    'admin_role_display': admin_user.get_role_display(),
                    'can_manage_users': admin_user.can_manage_users,
                    'can_manage_controls': getattr(admin_user, 'can_manage_controls', False),
                    'can_manage_points': admin_user.can_manage_points,
                    'can_manage_rewards': admin_user.can_manage_rewards,
                    'can_manage_schedules': admin_user.can_manage_schedules,
                    'can_manage_security': admin_user.can_manage_security,
                    'can_manage_learning': admin_user.can_manage_learning,
                    'can_manage_games': admin_user.can_manage_games,
                    'can_view_all': admin_user.can_view_all,
                }
            except AdminUser.DoesNotExist:
                request.admin_user = None
                request.is_admin_authenticated = False
                request.admin_context = {}
                # Clear invalid session data - but ONLY admin keys, not user keys
                request.session.pop('admin_user_id', None)
                request.session.pop('admin_username', None)
                request.session.pop('admin_role', None)
                request.session.pop('admin_full_name', None)
        else:
            # No admin authentication found
            request.admin_user = None
            request.is_admin_authenticated = False
            request.admin_context = {}
        
        response = self.get_response(request)
        return response
