from django.urls import path
from . import views

urlpatterns = [
    path('api/questions/', views.questions_view, name='questions'),

    path('api/game/data/', views.get_game_data, name='get_game_data'),
    path('api/game/save-session/', views.save_game_session, name='save_game_session'),
    path('api/game/leaderboard/', views.get_game_leaderboard, name='game_leaderboard'),
    path('api/game/user-stats/', views.get_user_game_stats, name='user_game_stats'),
    
    # Debug endpoints
    path('api/game/debug-auth/', views.debug_game_auth, name='debug_game_auth'),
    path('api/test-questions/', views.test_questions_no_auth, name='test_questions_no_auth'),
    
    # Admin Excel Upload/Download endpoints
    path('game-excel/download-template/', views.download_game_template, name='download_game_template'),
    path('game-excel/upload-excel/', views.upload_game_excel, name='upload_game_excel'),
    
    # Waste Category Excel endpoints
    path('category-excel/download-template/', views.download_category_template, name='download_category_template'),
    path('category-excel/upload-excel/', views.upload_category_excel, name='upload_category_excel'),
    
    # Waste Item Excel endpoints
    path('item-excel/download-template/', views.download_item_template, name='download_item_template'),
    path('item-excel/upload-excel/', views.upload_item_excel, name='upload_item_excel'),
]