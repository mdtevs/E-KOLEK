from django.core.management.base import BaseCommand
from cenro.models import AdminUser, AdminActionHistory
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create test admin history records'

    def handle(self, *args, **options):
        try:
            # Get a test admin user
            admin_user = AdminUser.objects.filter(username='testadmin').first()
            if not admin_user:
                self.stdout.write(self.style.ERROR('Test admin user "testadmin" not found. Please create it first.'))
                return
            
            # Create some test history records
            test_records = [
                {
                    'admin_user': admin_user,
                    'action': 'login',
                    'description': 'Admin logged into the system',
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Mozilla/5.0 Test Browser'
                },
                {
                    'admin_user': admin_user,
                    'action': 'password_change',
                    'description': 'Admin changed their password',
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Mozilla/5.0 Test Browser'
                },
                {
                    'admin_user': admin_user,
                    'action': 'create_admin',
                    'description': 'Created new admin account',
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Mozilla/5.0 Test Browser'
                }
            ]
            
            created_count = 0
            for record_data in test_records:
                history_record = AdminActionHistory.objects.create(**record_data)
                created_count += 1
                self.stdout.write(f'Created history record: {history_record}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} test history records!')
            )
            
            # Show total count
            total_records = AdminActionHistory.objects.count()
            self.stdout.write(f'Total history records in database: {total_records}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating test history records: {str(e)}')
            )
