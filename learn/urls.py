from django.urls import path
from . import views

urlpatterns = [
    # Web admin endpoints
    path('learning/test/', views.test_api, name='test_api'),
    path('learning/debug/', views.debug_learning_data, name='debug_learning_data'),
    path('learning/videos/', views.get_learning_videos, name='get_learning_videos'),
    path('learning/videos/watched/', views.mark_video_as_watched, name='mark_video_as_watched'),
    
    # API endpoints for Flutter app - Learning Videos
    path('api/learning/test/', views.test_api, name='api_test'),
    path('api/learning/debug/', views.debug_learning_data, name='api_debug_learning_data'),
    path('api/learning/videos/', views.get_learning_videos, name='api_get_learning_videos'),
    path('api/learning/videos/watched/', views.mark_video_as_watched, name='api_mark_video_as_watched'),
    
    # API endpoints for Quiz System
    path('api/learning/videos/<int:video_id>/quiz-questions/', views.get_quiz_questions, name='api_quiz_questions'),
    path('api/learning/videos/<int:video_id>/quiz-submit/', views.submit_quiz_answers, name='api_quiz_submit'),
    path('api/learning/videos/<int:video_id>/mark-watched/', views.mark_video_watched, name='api_mark_watched'),
    path('api/learning/videos/<int:video_id>/has-quiz/', views.check_quiz_availability, name='api_check_quiz'),
    path('api/learning/videos/<int:video_id>/quiz-result/', views.get_quiz_result, name='api_quiz_result'),
    path('api/learning/videos/<int:video_id>/questions/<int:question_id>/debug/', views.debug_quiz_question, name='api_debug_quiz_question'),
    
    # Admin Excel Upload/Download endpoints
    path('quiz-excel/download-template/', views.download_quiz_template, name='download_quiz_template'),
    path('quiz-excel/upload-excel/', views.upload_quiz_excel, name='upload_quiz_excel'),
]
