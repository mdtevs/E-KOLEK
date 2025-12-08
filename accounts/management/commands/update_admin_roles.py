from django.core.management.base import BaseCommand
from cenro.models import AdminUser

class Command(BaseCommand):
    help = 'Update existing admin users with new role-based permissions'

    def handle(self, *args, **options):
        self.stdout.write('Updating admin user roles and permissions...')
        
        # Get all existing admin users
        admin_users = AdminUser.objects.all()
        updated_count = 0
        
        for admin in admin_users:
            old_role = admin.role
            
            # Map old roles to new roles
            if old_role == 'super_admin':
                admin.role = 'super_admin'
            elif old_role in ['city_admin', 'barangay_admin']:
                # Convert city/barangay admins to operations managers
                admin.role = 'operations_manager'
            else:
                # Default to operations manager for any unknown roles
                admin.role = 'operations_manager'
            
            # Save to trigger the permission setting logic
            admin.save()
            updated_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated {admin.username} ({admin.full_name}): {old_role} -> {admin.role}'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully updated {updated_count} admin users with new role system.'
            )
        )
        
        # Display role summary
        self.stdout.write('\nCurrent role distribution:')
        roles = AdminUser.objects.values_list('role', flat=True).distinct()
        for role in roles:
            count = AdminUser.objects.filter(role=role).count()
            role_display = dict(AdminUser.ROLE_CHOICES).get(role, role)
            self.stdout.write(f'  {role_display}: {count} users')
