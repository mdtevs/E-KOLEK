"""
Management command to enable user management permissions for all Super Admins
"""
from django.core.management.base import BaseCommand
from cenro.models import AdminUser


class Command(BaseCommand):
    help = 'Enable can_manage_users permission for all Super Admins'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== Fixing Admin Permissions ===\n'))
        
        # Get all Super Admins
        super_admins = AdminUser.objects.filter(role='super_admin', is_active=True)
        
        self.stdout.write(f'Found {super_admins.count()} Super Admin(s)')
        
        updated_count = 0
        for admin in super_admins:
            self.stdout.write(f'\nAdmin: {admin.username}')
            self.stdout.write(f'  Role: {admin.role}')
            self.stdout.write(f'  can_manage_users (before): {admin.can_manage_users}')
            
            if not admin.can_manage_users:
                admin.can_manage_users = True
                admin.save(update_fields=['can_manage_users'])
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ Updated can_manage_users to True'))
            else:
                self.stdout.write(f'  ℹ️  Already has permission')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Updated {updated_count} admin(s)'))
        self.stdout.write(self.style.SUCCESS('Admin notifications will now be created for new user registrations!\n'))
