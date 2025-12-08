from django.core.management.base import BaseCommand
from accounts.models import Barangay

class Command(BaseCommand):
    help = 'Create sample barangays for testing'

    def handle(self, *args, **options):
        barangays = [
            'Barangay 1',
            'Barangay 2', 
            'Barangay 3',
            'Barangay 4',
            'Barangay 5',
            'Poblacion',
            'San Antonio',
            'San Jose',
            'Santa Maria',
            'Santo Domingo'
        ]
        
        created_count = 0
        for barangay_name in barangays:
            barangay, created = Barangay.objects.get_or_create(name=barangay_name)
            if created:
                created_count += 1
                self.stdout.write(f'Created barangay: {barangay_name}')
            else:
                self.stdout.write(f'Barangay already exists: {barangay_name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new barangays!')
        )
