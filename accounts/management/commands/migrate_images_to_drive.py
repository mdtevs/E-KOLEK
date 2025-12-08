"""
Management command to migrate existing reward images from local storage to Google Drive
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import Reward
import os


class Command(BaseCommand):
    help = 'Migrate existing reward images from local storage to Google Drive'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if Google Drive is not enabled',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Starting image migration...')
        
        if not getattr(settings, 'USE_GOOGLE_DRIVE', False) and not options['force']:
            self.stdout.write(
                self.style.ERROR('Google Drive is not enabled. Use --force to override.')
            )
            return
        
        self.stdout.write('Google Drive is enabled, proceeding...')
        
        try:
            from eko.google_drive_storage import GoogleDriveStorage
            storage = GoogleDriveStorage()
            self.stdout.write('Google Drive storage initialized successfully')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to initialize Google Drive storage: {e}')
            )
            return
        
        # Find rewards with local image paths
        rewards_with_local_images = Reward.objects.filter(
            image__isnull=False,
            image__startswith='reward_images/'
        )
        
        self.stdout.write(f'Found {rewards_with_local_images.count()} rewards with local images')
        
        migrated = 0
        failed = 0
        
        for reward in rewards_with_local_images:
            local_path = os.path.join(settings.MEDIA_ROOT, reward.image.name)
            
            if not os.path.exists(local_path):
                self.stdout.write(
                    self.style.WARNING(f'Local file not found for {reward.name}: {local_path}')
                )
                failed += 1
                continue
            
            if options['dry_run']:
                self.stdout.write(f'Would migrate: {reward.name} -> {reward.image.name}')
                continue
            
            try:
                # Read the local file
                with open(local_path, 'rb') as f:
                    file_content = f.read()
                
                # Create a file-like object
                from django.core.files.base import ContentFile
                from django.core.files.uploadedfile import SimpleUploadedFile
                
                file_name = os.path.basename(reward.image.name)
                uploaded_file = SimpleUploadedFile(
                    file_name,
                    file_content,
                    content_type='image/jpeg'  # Default, will be detected by Google Drive
                )
                
                # Upload to Google Drive
                file_id = storage._save(f"migrated_{reward.name}_{file_name}", uploaded_file)
                
                # Update the reward with the new Google Drive file ID
                reward.image.name = file_id
                reward.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Migrated {reward.name}: {file_id}')
                )
                migrated += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to migrate {reward.name}: {e}')
                )
                failed += 1
        
        if not options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f'Migration completed: {migrated} successful, {failed} failed')
            )
        else:
            self.stdout.write(f'Dry run completed: {rewards_with_local_images.count()} images would be migrated')
