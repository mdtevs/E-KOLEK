from django.core.management.base import BaseCommand
from accounts.models import Users
import string
import random


class Command(BaseCommand):
    help = 'Generate referral codes for existing users who don\'t have one'

    def handle(self, *args, **options):
        users_without_codes = Users.objects.filter(referral_code__isnull=True)
        count = 0
        
        for user in users_without_codes:
            if not user.referral_code:
                user.referral_code = user.generate_referral_code()
                user.save(update_fields=['referral_code'])
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Generated referral code {user.referral_code} for user {user.username}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated referral codes for {count} users'
            )
        )
