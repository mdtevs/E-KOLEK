"""
Django Management Command: Create Superadmin (Easiest Method)
Usage: python manage.py createsuperadmin

This is the SIMPLEST way to create a superadmin - no .bat files needed!
Just run: python manage.py createsuperadmin
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from cenro.models import AdminUser
from accounts.models import Barangay
import getpass


class Command(BaseCommand):
    help = 'Create a superadmin with all permissions (Quick and Easy!)'

    def add_arguments(self, parser):
        # Make it work with or without arguments
        parser.add_argument('--username', type=str, help='Superadmin username')
        parser.add_argument('--email', type=str, help='Superadmin email')
        parser.add_argument('--password', type=str, help='Superadmin password')
        parser.add_argument('--full-name', type=str, help='Full name')
        parser.add_argument('--quick', action='store_true', help='Create with default credentials (admin/Admin@123456)')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('   🚀 CENRO E-KOLEK - SUPERADMIN CREATION (QUICK METHOD)'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        # Quick mode - create with defaults
        if options.get('quick'):
            username = 'admin'
            password = 'Admin@123456'
            email = 'admin@ekolek.com'
            full_name = 'Super Administrator'
            
            self.stdout.write(self.style.WARNING('⚡ QUICK MODE - Using default credentials:'))
            self.stdout.write(f'   Username: {username}')
            self.stdout.write(f'   Password: {password}')
            self.stdout.write(f'   Email: {email}')
            self.stdout.write('')
        else:
            # Interactive mode
            username = options.get('username') or input('👤 Username (default: admin): ').strip() or 'admin'
            
            # Check if username exists
            if AdminUser.objects.filter(username=username).exists():
                self.stdout.write(self.style.ERROR(f'❌ Username "{username}" already exists!'))
                existing = AdminUser.objects.get(username=username)
                self.stdout.write(f'   Role: {existing.role}')
                self.stdout.write(f'   Email: {existing.email}')
                self.stdout.write(f'   Created: {existing.created_at}')
                return

            email = options.get('email') or input('📧 Email (default: admin@ekolek.com): ').strip() or 'admin@ekolek.com'
            full_name = options.get('full_name') or input('🏷️  Full Name (default: Super Administrator): ').strip() or 'Super Administrator'
            
            # Password
            password = options.get('password')
            if not password:
                password = getpass.getpass('🔐 Password: ')
                confirm_password = getpass.getpass('🔐 Confirm Password: ')
                
                if password != confirm_password:
                    self.stdout.write(self.style.ERROR('❌ Passwords do not match!'))
                    return
                
                if len(password) < 8:
                    self.stdout.write(self.style.ERROR('❌ Password must be at least 8 characters!'))
                    return

        try:
            # Create superadmin
            admin = AdminUser.objects.create(
                username=username,
                email=email,
                full_name=full_name,
                role='super_admin',
                status='approved',
                is_active=True,
                # ALL PERMISSIONS ENABLED
                can_manage_users=True,
                can_manage_points=True,
                can_manage_rewards=True,
                can_manage_schedules=True,
                can_manage_learning=True,
                can_manage_games=True,
                can_manage_security=True,
                can_manage_controls=True,
            )
            admin.set_password(password)
            admin.save()
            
            # Assign ALL barangays
            all_barangays = Barangay.objects.all()
            if all_barangays.exists():
                admin.barangays.set(all_barangays)
                barangay_count = all_barangays.count()
            else:
                barangay_count = 0
                self.stdout.write(self.style.WARNING('⚠️  No barangays found - you may need to run: python manage.py create_barangays'))
            
            # Success message
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.SUCCESS('   ✅ SUPERADMIN CREATED SUCCESSFULLY!'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write('')
            self.stdout.write(f'👤 Username:  {username}')
            self.stdout.write(f'📧 Email:     {email}')
            self.stdout.write(f'🏷️  Full Name: {full_name}')
            self.stdout.write(f'👑 Role:      {admin.role}')
            self.stdout.write(f'🌐 Barangays: {barangay_count} assigned')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎯 LOGIN INSTRUCTIONS:'))
            self.stdout.write('   1. Start server: python manage.py runserver')
            self.stdout.write('   2. Open: http://localhost:8000/cenro/admin/login/')
            self.stdout.write(f'   3. Login with username: {username}')
            self.stdout.write('')
            
            if options.get('quick'):
                self.stdout.write(self.style.WARNING('⚠️  SECURITY WARNING: Change the default password immediately!'))
            
            self.stdout.write(self.style.SUCCESS('=' * 70))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            import traceback
            traceback.print_exc()
