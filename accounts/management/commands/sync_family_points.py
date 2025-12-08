from django.core.management.base import BaseCommand
from django.db import models
from accounts.models import Family

class Command(BaseCommand):
    help = 'Synchronize family points with the sum of active members points'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        families = Family.objects.filter(status='approved')
        updated_count = 0
        total_families = families.count()
        
        self.stdout.write(f'Checking {total_families} approved families...')
        
        for family in families:
            # Calculate actual points from active members
            actual_points = family.members.filter(is_active=True).aggregate(
                total=models.Sum('total_points')
            )['total'] or 0
            
            stored_points = family.total_family_points
            
            if actual_points != stored_points:
                self.stdout.write(
                    f'Family: {family.family_name} | '
                    f'Stored: {stored_points} | '
                    f'Calculated: {actual_points} | '
                    f'Difference: {stored_points - actual_points}'
                )
                
                if not dry_run:
                    family.total_family_points = actual_points
                    family.save(update_fields=['total_family_points'])
                
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {family.family_name}: {stored_points} pts (correct)')
                )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'Would update {updated_count} families')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} families')
            )
            
        if updated_count == 0:
            self.stdout.write(
                self.style.SUCCESS('All family points are already synchronized!')
            )
