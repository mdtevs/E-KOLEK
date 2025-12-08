"""
Management command to set up game cooldown configurations
Usage: python manage.py setup_game_cooldowns
"""

from django.core.management.base import BaseCommand
from game.models import GameConfiguration


class Command(BaseCommand):
    help = 'Set up default game cooldown configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=72,
            help='Default cooldown hours (default: 72)',
        )
        parser.add_argument(
            '--minutes',
            type=int,
            default=0,
            help='Default cooldown minutes (default: 0)',
        )
        parser.add_argument(
            '--active',
            action='store_true',
            help='Set cooldown as active (default: inactive)',
        )

    def handle(self, *args, **options):
        hours = options['hours']
        minutes = options['minutes']
        is_active = options['active']
        
        self.stdout.write(self.style.WARNING(
            f'\nSetting up game cooldowns: {hours}h {minutes}m, active={is_active}\n'
        ))
        
        # Game types to configure
        game_types = [
            ('quiz', 'Quiz Game'),
            ('drag_drop', 'Drag & Drop Game'),
            ('all', 'Default (All Games)'),
        ]
        
        for game_type, display_name in game_types:
            config, created = GameConfiguration.objects.update_or_create(
                game_type=game_type,
                defaults={
                    'cooldown_hours': hours,
                    'cooldown_minutes': minutes,
                    'is_active': is_active,
                    'updated_by': 'management_command'
                }
            )
            
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ {action} {display_name}: {config.get_formatted_duration()} '
                    f'(active: {config.is_active})'
                )
            )
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Successfully configured {len(game_types)} game types!\n'
        ))
        
        if not is_active:
            self.stdout.write(self.style.WARNING(
                '⚠️  Note: Cooldowns are INACTIVE. Games are currently unrestricted.\n'
                '   To activate, run: python manage.py setup_game_cooldowns --active\n'
                '   Or enable them in the admin dashboard.\n'
            ))
