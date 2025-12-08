from django.core.management.base import BaseCommand
from learn.models import LearningVideo

class Command(BaseCommand):
    help = 'Add sample learning videos'

    def handle(self, *args, **options):
        videos = [
            {
                'title': 'The Importance of Recycling',
                'description': 'Discover why recycling is crucial for the environment and how it helps reduce waste.',
                'video_url': 'https://youtu.be/Y2W0jPg2JBk',
                'points_reward': 50,
            },
            {
                'title': 'Composting Basics',
                'description': 'Learn the basics of composting and how it can turn organic waste into valuable soil.',
                'video_url': 'https://youtu.be/WEJDrrCsbzE',
                'points_reward': 45,
            },
            {
                'title': 'Reducing Plastic Usage',
                'description': 'Understand the impact of plastic on the environment and ways to minimize its use.',
                'video_url': 'https://youtu.be/ODni_Bey154',
                'points_reward': 40,
            },
            {
                'title': 'Sustainable Living Tips',
                'description': 'Explore practical tips for living sustainably and reducing your carbon footprint.',
                'video_url': 'https://youtu.be/6jQ7y_qQYUA',
                'points_reward': 60,
            },
            {
                'title': 'The Benefits of Tree Planting',
                'description': 'Learn how planting trees can combat climate change and improve biodiversity.',
                'video_url': 'https://youtu.be/sTsYeUXKmkI',
                'points_reward': 55,
            },
            {
                'title': 'Understanding Climate Change',
                'description': 'An overview of climate change causes, effects, and what we can do about it.',
                'video_url': 'https://youtu.be/EuwTbcPhqmU',
                'points_reward': 70,
            },
            {
                'title': 'Water Conservation Methods',
                'description': 'Learn effective ways to conserve water at home and in your community.',
                'video_url': 'https://youtu.be/AQWgMfKfNJE',
                'points_reward': 35,
            },
            {
                'title': 'Green Energy Solutions',
                'description': 'Explore renewable energy sources and their benefits for the environment.',
                'video_url': 'https://youtu.be/UrmMaLLrMDQ',
                'points_reward': 65,
            },
        ]
        
        for video_data in videos:
            video, created = LearningVideo.objects.get_or_create(
                title=video_data['title'],
                defaults=video_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created video: {video.title}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Video already exists: {video.title}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {len(videos)} videos')
        )
