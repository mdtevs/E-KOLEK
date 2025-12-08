from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from cenro.models import AdminUser
import getpass

class Command(BaseCommand):
    help = 'Create a new admin user for the CENRO system'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Admin username')
        parser.add_argument('--full-name', type=str, help='Admin full name')
        parser.add_argument('--role', type=str, help='Admin role', 
                          choices=['super_admin', 'operations_manager', 'content_rewards_manager', 'security_analyst'])
        parser.add_argument('--password', type=str, help='Admin password')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== CENRO Admin User Creation ===\n'))

        # Get username
        username = options.get('username')
        if not username:
            username = input('Enter admin username: ').strip()
        
        # Check if username already exists
        if AdminUser.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'Username "{username}" already exists!'))
            return

        # Get full name
        full_name = options.get('full_name')
        if not full_name:
            full_name = input('Enter full name: ').strip()

        # Get role
        role = options.get('role')
        if not role:
            self.stdout.write('\nAvailable roles:')
            self.stdout.write('1. super_admin - Full system access')
            self.stdout.write('2. operations_manager - User, Points, Schedules')
            self.stdout.write('3. content_rewards_manager - Rewards, Learning, Games')
            self.stdout.write('4. security_analyst - Security monitoring + view-only access')
            
            role_choice = input('\nSelect role (1-4): ').strip()
            role_map = {
                '1': 'super_admin',
                '2': 'operations_manager',
                '3': 'content_rewards_manager',
                '4': 'security_analyst'
            }
            role = role_map.get(role_choice)
            if not role:
                self.stdout.write(self.style.ERROR('Invalid role selection!'))
                return

        # Get password
        password = options.get('password')
        if not password:
            password = getpass.getpass('Enter password: ')
            confirm_password = getpass.getpass('Confirm password: ')
            
            if password != confirm_password:
                self.stdout.write(self.style.ERROR('Passwords do not match!'))
                return

        if len(password) < 8:
            self.stdout.write(self.style.ERROR('Password must be at least 8 characters long!'))
            return

        try:
            # Create admin user
            admin_user = AdminUser(
                username=username,
                full_name=full_name,
                role=role
            )
            admin_user.set_password(password)
            admin_user.save()  # This will trigger the save() method which sets permissions

            self.stdout.write(self.style.SUCCESS(f'\n✅ Admin user created successfully!'))
            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Full Name: {full_name}')
            self.stdout.write(f'Role: {role}')
            
            # Show permissions assigned
            self.stdout.write(f'\n📋 Permissions assigned:')
            if admin_user.can_manage_users:
                self.stdout.write('  ✓ Manage Users')
            if admin_user.can_manage_points:
                self.stdout.write('  ✓ Manage Points')
            if admin_user.can_manage_rewards:
                self.stdout.write('  ✓ Manage Rewards')
            if admin_user.can_manage_schedules:
                self.stdout.write('  ✓ Manage Schedules')
            if admin_user.can_manage_learning:
                self.stdout.write('  ✓ Manage Learning')
            if admin_user.can_manage_games:
                self.stdout.write('  ✓ Manage Games')
            if admin_user.can_manage_security:
                self.stdout.write('  ✓ Manage Security')
            if hasattr(admin_user, 'can_manage_system') and admin_user.can_manage_system:
                self.stdout.write('  ✓ Manage System')
            if admin_user.can_view_all:
                self.stdout.write('  ✓ View All (Read-only)')
            if hasattr(admin_user, 'can_manage_controls') and admin_user.can_manage_controls:
                self.stdout.write('  ✓ Manage Controls')

            self.stdout.write(f'\n🌐 You can now login at: /admin/login/')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating admin user: {str(e)}'))
