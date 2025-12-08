from django.db import models
from accounts.models import Users
from django.core.validators import MinValueValidator, MaxValueValidator
import re

class LearningVideo(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    video_url = models.URLField(help_text="YouTube video URL")
    thumbnail_url = models.URLField(blank=True, null=True, help_text="Custom thumbnail URL (optional)")
    points_reward = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Points earned for watching")
    is_active = models.BooleanField(default=True, help_text="Whether this video is available")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    duration_seconds = models.IntegerField(default=0, help_text="Video duration in seconds")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_youtube_video_id(self):
        """Extract YouTube video ID from URL"""
        pattern = r'(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^"&?/\s]{11})'
        match = re.search(pattern, self.video_url)
        return match.group(1) if match else None
    
    def get_youtube_thumbnail(self):
        """Get YouTube thumbnail URL"""
        if self.thumbnail_url:
            return self.thumbnail_url
        video_id = self.get_youtube_video_id()
        if video_id:
            return f"https://img.youtube.com/vi/{video_id}/0.jpg"
        return None

class VideoWatchHistory(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    video = models.ForeignKey(LearningVideo, on_delete=models.CASCADE)
    points_earned = models.DecimalField(max_digits=10, decimal_places=2)
    watched_at = models.DateTimeField(auto_now_add=True)
    watch_percentage = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    class Meta:
        unique_together = ['user', 'video']
        ordering = ['-watched_at']
    
    def __str__(self):
        return f"{self.user.full_name} watched {self.video.title} ({self.watch_percentage}%)"

class QuizQuestion(models.Model):
    """Quiz questions linked to learning videos"""
    ANSWER_CHOICES = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ]
    
    video = models.ForeignKey(LearningVideo, on_delete=models.CASCADE, related_name='quiz_questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_answer = models.CharField(max_length=1, choices=ANSWER_CHOICES)
    points_reward = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    explanation = models.TextField(blank=True, help_text="Explanation for the correct answer")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Question order in quiz")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.video.title} - Q{self.order}: {self.question_text[:50]}"

class QuizResult(models.Model):
    """Store quiz completion results"""
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    video = models.ForeignKey(LearningVideo, on_delete=models.CASCADE)
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField()
    score_percentage = models.FloatField()
    total_points = models.DecimalField(max_digits=10, decimal_places=2)
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'video']
        ordering = ['-completed_at']
    
    @property
    def is_passed(self):
        return self.score_percentage >= 70.0  # 70% passing grade
    
    def __str__(self):
        return f"{self.user.full_name} - {self.video.title}: {self.score_percentage}%"

class QuizAnswer(models.Model):
    """Individual quiz answer tracking"""
    quiz_result = models.ForeignKey(QuizResult, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=1, choices=QuizQuestion.ANSWER_CHOICES)
    is_correct = models.BooleanField()
    points_earned = models.DecimalField(max_digits=10, decimal_places=2)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.quiz_result.user.full_name} - Q{self.question.id}: {self.selected_answer} ({'✓' if self.is_correct else '✗'})"
