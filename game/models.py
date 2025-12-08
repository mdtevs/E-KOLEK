from django.db import models
from django.conf import settings
import uuid

class Question(models.Model):
    text = models.CharField(max_length=255)
    points = models.DecimalField(max_digits=10, decimal_places=2, default=1)

    def __str__(self):
        return self.text

class Choice(models.Model):
    question = models.ForeignKey(Question, related_name="choices", on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} ({'Correct' if self.is_correct else 'Wrong'})"


class WasteCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)  # e.g., "Recyclable", "Organic"
    color_hex = models.CharField(max_length=7, default="#000000")  # e.g., "#4CAF50"
    icon_name = models.CharField(max_length=50, default="delete")  # Material icon name
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class WasteItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)  # e.g., "Plastic Bottle"
    emoji = models.CharField(max_length=10, blank=True)  # e.g., "♻️"
    category = models.ForeignKey(WasteCategory, on_delete=models.CASCADE, related_name='items')
    points = models.DecimalField(max_digits=10, decimal_places=2, default=10)  # Points awarded for correct sorting
    difficulty_level = models.CharField(
        max_length=20, 
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
        default='easy'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.emoji} {self.name}"

class GameSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0.0)
    duration_seconds = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.score} points"


class GameConfiguration(models.Model):
    """
    Configuration for game cooldown settings
    Allows admin to control how long users must wait between game plays
    """
    GAME_TYPE_CHOICES = [
        ('quiz', 'Quiz Game'),
        ('drag_drop', 'Drag & Drop Game'),
        ('all', 'All Games (Default)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game_type = models.CharField(
        max_length=20, 
        choices=GAME_TYPE_CHOICES, 
        default='all',
        unique=True,
        help_text="Type of game this configuration applies to"
    )
    
    # Cooldown duration in minutes
    cooldown_hours = models.IntegerField(
        default=72,
        help_text="Hours users must wait before playing again"
    )
    cooldown_minutes = models.IntegerField(
        default=0,
        help_text="Additional minutes to wait (0-59)"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this cooldown is currently active"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=255, blank=True, help_text="Admin who last updated")
    
    class Meta:
        verbose_name = "Game Configuration"
        verbose_name_plural = "Game Configurations"
        ordering = ['game_type']
    
    def __str__(self):
        return f"{self.get_game_type_display()} - {self.cooldown_hours}h {self.cooldown_minutes}m"
    
    @property
    def total_cooldown_minutes(self):
        """Get total cooldown in minutes"""
        return (self.cooldown_hours * 60) + self.cooldown_minutes
    
    @property
    def total_cooldown_seconds(self):
        """Get total cooldown in seconds"""
        return self.total_cooldown_minutes * 60
    
    @property
    def total_cooldown_milliseconds(self):
        """Get total cooldown in milliseconds (for Flutter app)"""
        return self.total_cooldown_seconds * 1000
    
    def get_formatted_duration(self):
        """Get human-readable duration format"""
        if self.cooldown_hours > 0 and self.cooldown_minutes > 0:
            return f"{self.cooldown_hours} hours {self.cooldown_minutes} minutes"
        elif self.cooldown_hours > 0:
            return f"{self.cooldown_hours} hours"
        elif self.cooldown_minutes > 0:
            return f"{self.cooldown_minutes} minutes"
        else:
            return "No cooldown"
    
    @classmethod
    def get_cooldown_for_game(cls, game_type):
        """
        Get cooldown configuration for a specific game type
        Falls back to 'all' configuration if specific config doesn't exist
        """
        try:
            # Try to get specific game config
            config = cls.objects.get(game_type=game_type, is_active=True)
            return config
        except cls.DoesNotExist:
            try:
                # Fallback to 'all' games config
                config = cls.objects.get(game_type='all', is_active=True)
                return config
            except cls.DoesNotExist:
                # Return default if nothing is configured
                return None
    
    @classmethod
    def get_default_cooldown_milliseconds(cls):
        """Get default cooldown in milliseconds (72 hours)"""
        return 72 * 60 * 60 * 1000