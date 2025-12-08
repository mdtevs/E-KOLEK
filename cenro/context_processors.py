"""
Admin context processor to automatically add admin user information to all templates
"""

def admin_context(request):
    """
    Add admin user context to all templates
    """
    context = {}
    
    # Check if user is authenticated via AdminUser system
    admin_user_id = request.session.get('admin_user_id')
    if admin_user_id:
        try:
            from cenro.models import AdminUser
            admin_user = AdminUser.objects.get(id=admin_user_id, is_active=True)
            
            # Force refresh permissions if they seem unset (defensive programming)
            if not hasattr(admin_user, 'can_manage_users') or admin_user.can_manage_users is None:
                admin_user.save()  # This will trigger the save() method that sets permissions
                admin_user.refresh_from_db()  # Reload from database
            
            context.update({
                'admin_user': admin_user,
                'admin_username': admin_user.username,
                'admin_full_name': admin_user.full_name,
                'admin_role': admin_user.role,
                'admin_role_display': admin_user.get_role_display(),
                'is_admin_authenticated': True,
                'can_manage_users': getattr(admin_user, 'can_manage_users', False),
                'can_manage_controls': getattr(admin_user, 'can_manage_controls', False),
                'can_manage_points': getattr(admin_user, 'can_manage_points', False),
                'can_manage_rewards': getattr(admin_user, 'can_manage_rewards', False),
                'can_manage_schedules': getattr(admin_user, 'can_manage_schedules', False),
                'can_manage_security': getattr(admin_user, 'can_manage_security', False),
                'can_manage_learning': getattr(admin_user, 'can_manage_learning', False),
                'can_manage_games': getattr(admin_user, 'can_manage_games', False),
                'can_view_all': getattr(admin_user, 'can_view_all', False),
            })
        except Exception as e:
            # Log the specific error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Admin context error: {str(e)}")
            context.update({
                'admin_user': None,
                'is_admin_authenticated': False,
            })
    else:
        context.update({
            'admin_user': None,
            'is_admin_authenticated': False,
        })
    
    return context
