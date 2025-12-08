from django.core.management.base import BaseCommand
from cenro.models import AdminUser

class Command(BaseCommand):
    help = 'Fix admin user permissions by resaving all admin users'

    def handle(self, *args, **options):
        admin_users = AdminUser.objects.all()
        
        self.stdout.write(f'Found {admin_users.count()} admin users')
        
        for admin_user in admin_users:
            # Print current permissions
            self.stdout.write(f'Fixing permissions for: {admin_user.username} ({admin_user.role})')
            
            # Save to trigger permission setting
            admin_user.save()
            
            # Verify permissions were set
            admin_user.refresh_from_db()
            self.stdout.write(f'  - can_manage_rewards: {admin_user.can_manage_rewards}')
            self.stdout.write(f'  - can_manage_learning: {admin_user.can_manage_learning}')
            self.stdout.write(f'  - can_manage_games: {admin_user.can_manage_games}')
        
        self.stdout.write(self.style.SUCCESS('Successfully fixed all admin permissions'))
