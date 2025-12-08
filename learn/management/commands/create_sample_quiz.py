from django.core.management.base import BaseCommand
from learn.models import LearningVideo, QuizQuestion

class Command(BaseCommand):
    help = 'Create sample quiz data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--video-id',
            type=int,
            help='Create quiz for specific video ID'
        )

    def handle(self, *args, **options):
        video_id = options.get('video_id')
        
        if video_id:
            try:
                video = LearningVideo.objects.get(id=video_id)
                self.create_quiz_for_video(video)
            except LearningVideo.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Video with ID {video_id} not found'))
                return
        else:
            # Create quiz for all videos that don't have quiz questions
            videos_without_quiz = LearningVideo.objects.filter(is_active=True).exclude(
                id__in=QuizQuestion.objects.values_list('video_id', flat=True)
            )
            
            if not videos_without_quiz:
                self.stdout.write(self.style.WARNING('All active videos already have quiz questions'))
                return
            
            for video in videos_without_quiz:
                self.create_quiz_for_video(video)

    def create_quiz_for_video(self, video):
        """Create sample quiz questions for a video"""
        
        # Check if quiz already exists
        existing_questions = QuizQuestion.objects.filter(video=video).count()
        if existing_questions > 0:
            self.stdout.write(self.style.WARNING(f'Video "{video.title}" already has {existing_questions} quiz questions'))
            return
        
        # Sample questions based on video content - customize as needed
        sample_questions = [
            {
                'question_text': f'What is the main topic of the video "{video.title}"?',
                'option_a': 'Environmental conservation',
                'option_b': 'Waste management',
                'option_c': 'Recycling techniques',
                'option_d': 'Community development',
                'correct_answer': 'B',
                'explanation': 'This video focuses on proper waste management practices.',
                'order': 1,
                'points_reward': 10,
            },
            {
                'question_text': 'According to the video, what is the most important step in waste management?',
                'option_a': 'Proper sorting of waste',
                'option_b': 'Using expensive equipment',
                'option_c': 'Hiring more workers',
                'option_d': 'Building more facilities',
                'correct_answer': 'A',
                'explanation': 'Proper sorting is the foundation of effective waste management.',
                'order': 2,
                'points_reward': 10,
            },
            {
                'question_text': 'How many types of waste categories are mentioned in the video?',
                'option_a': '2',
                'option_b': '3',
                'option_c': '4',
                'option_d': '5',
                'correct_answer': 'C',
                'explanation': 'The video discusses 4 main categories: biodegradable, non-biodegradable, recyclable, and hazardous.',
                'order': 3,
                'points_reward': 15,
            },
            {
                'question_text': 'What is the recommended frequency for waste collection mentioned in the video?',
                'option_a': 'Daily',
                'option_b': 'Weekly',
                'option_c': 'Bi-weekly',
                'option_d': 'Monthly',
                'correct_answer': 'B',
                'explanation': 'Weekly collection ensures proper hygiene and prevents accumulation.',
                'order': 4,
                'points_reward': 10,
            },
            {
                'question_text': 'According to the video, what should you do with hazardous waste?',
                'option_a': 'Mix it with regular waste',
                'option_b': 'Bury it in the backyard',
                'option_c': 'Bring it to designated collection points',
                'option_d': 'Burn it at home',
                'correct_answer': 'C',
                'explanation': 'Hazardous waste requires special handling at designated collection points.',
                'order': 5,
                'points_reward': 15,
            }
        ]

        # Create quiz questions
        created_count = 0
        for question_data in sample_questions:
            question = QuizQuestion.objects.create(
                video=video,
                **question_data
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} quiz questions for video: "{video.title}"'
            )
        )
