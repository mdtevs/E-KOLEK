from django.core.management.base import BaseCommand
from accounts.models import Family

class Command(BaseCommand):
    help = 'Clean up orphaned families that have no active members'

    def handle(self, *args, **options):
        self.stdout.write('Checking for orphaned families...')
        
        # Find families with no active members
        orphaned_families = []
        for family in Family.objects.all():
            if family.members.filter(is_active=True).count() == 0:
                orphaned_families.append(family)
        
        if orphaned_families:
            self.stdout.write(f'Found {len(orphaned_families)} orphaned families:')
            for family in orphaned_families:
                self.stdout.write(f'  - {family.family_name} (Phone: {family.representative_phone})')
            
            # Delete orphaned families
            for family in orphaned_families:
                self.stdout.write(f'Deleting family: {family.family_name}')
                family.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {len(orphaned_families)} orphaned families')
            )
        else:
            self.stdout.write('No orphaned families found.')
