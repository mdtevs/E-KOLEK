"""
Admin Authentication Middleware
Automatically adds admin user information to template context
"""

class AdminUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is an admin request and user is authenticated
        if request.path.startswith('/cenro/') or request.path.startswith('/admin') or request.path in ['/dashboard/', '/adminuser/', '/admincontrol/', '/adminpoints/', '/adminrewards/', '/adminschedule/', '/admingames/', '/adminquiz/', '/adminlearn/', '/adminsecurity/']:
            admin_user_id = request.session.get('admin_user_id')
            if admin_user_id:
                try:
                    from cenro.models import AdminUser
                    admin_user = AdminUser.objects.get(id=admin_user_id, is_active=True)
                    
                    # Ensure permissions are set properly
                    if not hasattr(admin_user, 'can_manage_users') or admin_user.can_manage_users is None:
                        admin_user.save()  # This will trigger the save() method that sets permissions
                        admin_user.refresh_from_db()  # Reload from database
                    
                    request.admin_user = admin_user
                    request.is_admin_authenticated = True
                except AdminUser.DoesNotExist:
                    request.admin_user = None
                    request.is_admin_authenticated = False
                    # Clear invalid session
                    request.session.pop('admin_user_id', None)
                    request.session.pop('admin_username', None)
                    request.session.pop('admin_role', None)
                    request.session.pop('admin_full_name', None)
            else:
                request.admin_user = None
                request.is_admin_authenticated = False

        response = self.get_response(request)
        return response
