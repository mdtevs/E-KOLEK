from rest_framework import serializers
from .models import LearningVideo, QuizQuestion, QuizResult, QuizAnswer, VideoWatchHistory

class QuizQuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()
    
    class Meta:
        model = QuizQuestion
        fields = ['id', 'question_text', 'options', 'correct_answer', 'points_reward', 'explanation', 'order']
    
    def get_options(self, obj):
        """Return options as an array of strings for Flutter app"""
        options = [obj.option_a, obj.option_b, obj.option_c, obj.option_d]
        # Filter out any empty options if needed
        return [opt for opt in options if opt and opt.strip()]

class QuizAnswerInputSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_answer = serializers.CharField(max_length=1)

class QuizSubmissionSerializer(serializers.Serializer):
    answers = QuizAnswerInputSerializer(many=True)

class QuizAnswerResultSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    correct_answer = serializers.CharField(source='question.correct_answer', read_only=True)
    explanation = serializers.CharField(source='question.explanation', read_only=True)
    
    class Meta:
        model = QuizAnswer
        fields = ['question_text', 'selected_answer', 'correct_answer', 'is_correct', 'points_earned', 'explanation']

class QuizResultSerializer(serializers.ModelSerializer):
    is_passed = serializers.ReadOnlyField()
    answers = QuizAnswerResultSerializer(many=True, read_only=True)
    video_title = serializers.CharField(source='video.title', read_only=True)
    
    class Meta:
        model = QuizResult
        fields = ['id', 'video_title', 'total_questions', 'correct_answers', 'score_percentage', 
                 'total_points', 'is_passed', 'completed_at', 'answers']

class LearningVideoSerializer(serializers.ModelSerializer):
    is_watched = serializers.SerializerMethodField()
    has_quiz = serializers.SerializerMethodField()
    quiz_completed = serializers.SerializerMethodField()
    quiz_score = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningVideo
        fields = ['id', 'title', 'description', 'video_url', 'thumbnail_url', 
                 'points_reward', 'duration_seconds', 'created_at', 'is_watched', 
                 'has_quiz', 'quiz_completed', 'quiz_score']
    
    def get_is_watched(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return VideoWatchHistory.objects.filter(user=request.user, video=obj).exists()
        return False
    
    def get_has_quiz(self, obj):
        return obj.quiz_questions.filter(is_active=True).exists()
    
    def get_quiz_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return QuizResult.objects.filter(user=request.user, video=obj).exists()
        return False
    
    def get_quiz_score(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                result = QuizResult.objects.get(user=request.user, video=obj)
                return result.score_percentage
            except QuizResult.DoesNotExist:
                return None
        return None
    
    def get_thumbnail_url(self, obj):
        return obj.get_youtube_thumbnail()
