from django.core.management.base import BaseCommand
from cenro.models import AdminUser
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create a test admin account that requires password change'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='testadmin', help='Username for test admin')
        parser.add_argument('--password', type=str, default='temppass123', help='Temporary password')
        parser.add_argument('--fullname', type=str, default='Test Admin User', help='Full name')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        full_name = options['fullname']
        
        # Check if user already exists
        if AdminUser.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin user "{username}" already exists!')
            )
            return
        
        try:
            # Create admin user that must change password
            admin_user = AdminUser(
                username=username,
                full_name=full_name,
                role='operations_manager',
                status='approved',
                approval_date=timezone.now(),
                must_change_password=True,  # Force password change
                can_manage_users=True,
                can_manage_controls=True
            )
            admin_user.set_password(password)
            admin_user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created test admin: {username}')
            )
            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Temporary Password: {password}')
            self.stdout.write(f'Full Name: {full_name}')
            self.stdout.write(
                self.style.WARNING('This admin will be required to change password on first login.')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating admin: {str(e)}')
            )
