"""
Signal handlers for the accounts app
Handles automatic notification creation for admin users
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Users


@receiver(post_save, sender=Users)
def create_admin_notification_on_user_registration(sender, instance, created, **kwargs):
    """
    Create admin notification when a new user registers (status='pending')
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[SIGNAL] post_save triggered for User: {instance.username} | Created: {created} | Status: {instance.status}")
    
    # Only trigger for new users with pending status
    if created and instance.status == 'pending':
        try:
            from cenro.models import AdminNotification
            
            logger.info(f"[SIGNAL] Creating admin notifications for new user: {instance.username}")
            
            # Create notifications for all admins with user management permission
            notifications = AdminNotification.create_new_registration_notification(instance)
            
            logger.info(f"[SIGNAL] ✅ Created {len(notifications)} admin notifications for user: {instance.username}")
            
        except Exception as e:
            logger.error(f"[SIGNAL] ❌ Failed to create admin notification for user {instance.id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    else:
        logger.info(f"[SIGNAL] Skipping notification creation | Created: {created} | Status: {instance.status}")
