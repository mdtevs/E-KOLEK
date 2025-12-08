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
    # Only trigger for new users with pending status
    if created and instance.status == 'pending':
        try:
            from cenro.models import AdminNotification
            
            # Create notifications for all admins with user management permission
            AdminNotification.create_new_registration_notification(instance)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create admin notification for user {instance.id}: {str(e)}")
