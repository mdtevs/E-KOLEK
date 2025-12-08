from django.core.management.base import BaseCommand
from django.db.models import Count
from accounts.models import LoginAttempt

class Command(BaseCommand):
    help = 'Clean up duplicate login attempts from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Find potential duplicates (same username, IP, and timestamp within 1 second)
        # This is a simplified approach - you might need more sophisticated logic
        self.stdout.write('Scanning for duplicate login attempts...')
        
        total_before = LoginAttempt.objects.count()
        self.stdout.write(f'Total login attempts before cleanup: {total_before}')
        
        # Group by username, IP, success status, and minute (to find near-duplicates)
        from django.db.models import Min
        from django.db import models
        
        duplicates_removed = 0
        
        # Find records that might be duplicates (same user, IP, status within same minute)
        potential_duplicates = (
            LoginAttempt.objects
            .extra(select={'minute': "date_trunc('minute', timestamp)"})
            .values('username', 'ip_address', 'success', 'minute')
            .annotate(
                count=Count('id'),
                min_id=Min('id')
            )
            .filter(count__gt=1)
        )
        
        for duplicate_group in potential_duplicates:
            if duplicate_group['count'] > 1:
                # Keep the first record, delete the rest
                records_to_delete = LoginAttempt.objects.filter(
                    username=duplicate_group['username'],
                    ip_address=duplicate_group['ip_address'],
                    success=duplicate_group['success'],
                    timestamp__date_trunc_minute=duplicate_group['minute']
                ).exclude(id=duplicate_group['min_id'])
                
                delete_count = records_to_delete.count()
                
                if not dry_run:
                    records_to_delete.delete()
                
                duplicates_removed += delete_count
                
                self.stdout.write(
                    f'Found {duplicate_group["count"]} duplicates for '
                    f'{duplicate_group["username"]} from {duplicate_group["ip_address"]} '
                    f'({"success" if duplicate_group["success"] else "failed"}) - '
                    f'{"Would remove" if dry_run else "Removed"} {delete_count} duplicates'
                )
        
        total_after = LoginAttempt.objects.count() if not dry_run else total_before - duplicates_removed
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'Would remove {duplicates_removed} duplicate records')
            )
            self.stdout.write(
                self.style.WARNING(f'Total would be: {total_after} (reduced by {duplicates_removed})')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully removed {duplicates_removed} duplicate records')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Total login attempts after cleanup: {total_after} (reduced by {duplicates_removed})')
            )
            
        if duplicates_removed == 0:
            self.stdout.write(
                self.style.SUCCESS('No duplicate login attempts found!')
            )
