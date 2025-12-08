from django.urls import path
from .views import (
    # Dashboard views
    dashboard, admin_preview_user_dashboard, get_dashboard_metrics,
    # User views
    adminuser, view_user, view_single_idcard, edit_user, delete_user,
    approve_user, reject_user, get_user_by_id, get_user_by_family_code,
    # Control views
    admincontrol, add_waste_type, edit_waste_type, delete_waste_type,
    add_barangay, edit_barangay, delete_barangay,
    add_reward_category, edit_reward_category, delete_reward_category,
    add_terms, edit_terms, delete_terms, toggle_active_terms, extract_file_content, get_terms_data,
    # Points views
    adminpoints, save_waste_transaction,
    # Reward views
    adminrewards, reward_history, add_reward, edit_reward, delete_reward,
    add_stock, remove_stock, redeem_reward_api,
    # Schedule views
    adminschedule, add_schedule, edit_schedule, delete_schedule,
    # Game views
    admingames, adminquiz, add_question, delete_question,
    add_category, delete_category, add_item, delete_item,
    update_game_cooldown, get_game_cooldown,
    # Learning views
    adminlearn, add_video, edit_video, toggle_video, delete_video,
    quiz_management, quiz_questions, quiz_results,
    add_quiz_question, edit_quiz_question, delete_quiz_question, toggle_quiz_question,
    # Security views
    adminsecurity, generate_security_report,
    # Notification views
    get_admin_notifications_unread_count, get_admin_notifications_list,
    mark_admin_notification_read, mark_all_admin_notifications_read,
)
from . import admin_auth
from . import analytics_views
from django.conf import settings
from django.conf.urls.static import static
from eko.secure_views import (
    secure_save_waste_transaction, 
    secure_get_user_by_id, 
    secure_get_user_by_family_code,
    secure_add_question
)

app_name = 'cenro'

urlpatterns = [
    # Admin Authentication URLs
    path('cenro/admin/login/', admin_auth.admin_login, name='admin_login'),
    path('cenro/admin/logout/', admin_auth.admin_logout, name='admin_logout'),
    path('cenro/admin/management/', admin_auth.admin_management, name='admin_management'),
    path('cenro/admin/create/', admin_auth.admin_create, name='admin_create'),
    path('cenro/admin/change-password/', admin_auth.admin_change_password, name='admin_change_password'),
    path('cenro/admin/get-barangays/<uuid:admin_id>/', admin_auth.get_admin_barangays, name='get_admin_barangays'),
    path('cenro/admin/check-email/', admin_auth.check_admin_email_availability, name='check_admin_email'),
    path('cenro/admin/security-dashboard/', admin_auth.security_dashboard, name='security_dashboard'),
    
    # Security API endpoints
    path('cenro/api/generate-report/', generate_security_report, name='generate_security_report'),
    path('cenro/api/dashboard-metrics/', get_dashboard_metrics, name='get_dashboard_metrics'),
    
    # Admin Notification API endpoints
    path('cenro/api/notifications/unread-count/', get_admin_notifications_unread_count, name='admin_notifications_unread_count'),
    path('cenro/api/notifications/list/', get_admin_notifications_list, name='admin_notifications_list'),
    path('cenro/api/notifications/mark-read/<uuid:notification_id>/', mark_admin_notification_read, name='mark_admin_notification_read'),
    path('cenro/api/notifications/mark-all-read/', mark_all_admin_notifications_read, name='mark_all_admin_notifications_read'),
    
    # Main dashboard (landing page)
    path('dashboard/', dashboard, name='dashboard'),
    
    # Admin preview of user dashboard
    path('preview/user-dashboard/', admin_preview_user_dashboard, name='admin_preview_user_dashboard'),
    path('preview/user-dashboard/<uuid:user_id>/', admin_preview_user_dashboard, name='admin_preview_user_dashboard_specific'),

    path('adminuser/', adminuser, name='adminuser'),
    path('edit_user/', edit_user, name='edit_user'),
    path('delete_user/', delete_user, name='delete_user'),
    path('idcard/', view_user, name='view_user'),
    path('idcard/<uuid:user_id>/', view_single_idcard, name='view_single_idcard'),

    path('admincontrol/', admincontrol, name='admincontrol'),

    path('adminsecurity/', adminsecurity, name='adminsecurity'),

    path('adminpoints/', adminpoints, name='adminpoints'),

    path('admingames/', admingames, name='admingames'),
    path('add_category/', add_category, name='add_category'),
    path('delete_category/<uuid:category_id>/', delete_category, name='delete_category'),
    path('add_item/', add_item, name='add_item'),
    path('delete_item/<uuid:item_id>/', delete_item, name='delete_item'),
    
    # Game configuration endpoints
    path('api/game/cooldown/update/', update_game_cooldown, name='update_game_cooldown'),
    path('api/game/cooldown/<str:game_type>/', get_game_cooldown, name='admin_get_game_cooldown'),

    path('adminquiz/', adminquiz, name='adminquiz'),
    path('add_question/', secure_add_question, name='add_question'),  # Using secure version
    path('delete_question/<int:question_id>/', delete_question, name='delete_question'),

    path('adminrewards/', adminrewards, name='adminrewards'),
    path('add_reward/', add_reward, name='add_reward'),
    path('edit_reward/', edit_reward, name='edit_reward'),
    path('delete_reward/', delete_reward, name='delete_reward'),
    path('add_stock/', add_stock, name='add_stock'),
    path('remove_stock/', remove_stock, name='remove_stock'),
    path('reward_history/', reward_history, name='reward_history'),
    
    path('adminschedule/', adminschedule, name='adminschedule'),
    path('add_schedule/', add_schedule, name='add_schedule'),
    path('edit_schedule/', edit_schedule, name='edit_schedule'),
    path('delete_schedule/', delete_schedule, name='delete_schedule'),

    path('approve_user/', approve_user, name='approve_user'),
    path('reject_user/', reject_user, name='reject_user'),

    path('admincontrol/add-waste-type/', add_waste_type, name='add_waste_type'),
    path('admincontrol/edit-waste-type/<uuid:waste_id>/', edit_waste_type, name='edit_waste_type'),
    path('admincontrol/delete-waste-type/<uuid:waste_id>/', delete_waste_type, name='delete_waste_type'),

    path('admincontrol/add-barangay/', add_barangay, name='add_barangay'),
    path('admincontrol/edit-barangay/<uuid:barangay_id>/', edit_barangay, name='edit_barangay'),
    path('admincontrol/delete-barangay/<uuid:barangay_id>/', delete_barangay, name='delete_barangay'),

    path('admincontrol/add-category/', add_reward_category, name='add_reward_category'),
    path('admincontrol/delete-category/<uuid:category_id>/', delete_reward_category, name='delete_reward_category'),
    path('admincontrol/edit-reward-category/<uuid:category_id>/', edit_reward_category, name='edit_reward_category'),

    # Terms and Conditions Management URLs
    path('admincontrol/add-terms/', add_terms, name='add_terms'),
    path('admincontrol/edit-terms/<uuid:terms_id>/', edit_terms, name='edit_terms'),
    path('admincontrol/delete-terms/<uuid:terms_id>/', delete_terms, name='delete_terms'),
    path('admincontrol/toggle-active-terms/<uuid:terms_id>/', toggle_active_terms, name='toggle_active_terms'),
    path('api/terms/<uuid:terms_id>/', get_terms_data, name='get_terms_data'),
    path('api/extract-file-content/', extract_file_content, name='extract_file_content'),

    path("api/get-user-by-family-code/", secure_get_user_by_family_code, name="get_user_by_family_code"),  # Using secure version
    path("api/get-user-by-id/", secure_get_user_by_id, name="get_user_by_id"),  # Using secure version
    path("api/save-waste-transaction/", secure_save_waste_transaction, name="save_waste_transaction"),  # Using secure version

    path('api/redeem-reward/', redeem_reward_api, name='redeem_reward_api'),

    # Learning Videos Management URLs
    path('adminlearn/', adminlearn, name='adminlearn'),
    path('add_video/', add_video, name='add_video'),
    path('edit_video/', edit_video, name='edit_video'),
    path('toggle_video/', toggle_video, name='toggle_video'),
    path('delete_video/', delete_video, name='delete_video'),
    
    # Quiz Management URLs
    path('cenro/quiz-management/', quiz_management, name='quiz_management'),
    path('cenro/quiz-questions/<int:video_id>/', quiz_questions, name='quiz_questions'),
    path('cenro/quiz-results/', quiz_results, name='quiz_results'),
    path('cenro/quiz-results/<int:video_id>/', quiz_results, name='quiz_results_video'),
    path('cenro/add-quiz-question/', add_quiz_question, name='add_quiz_question'),
    path('cenro/edit-quiz-question/', edit_quiz_question, name='edit_quiz_question'),
    path('cenro/delete-quiz-question/', delete_quiz_question, name='delete_quiz_question'),
    path('cenro/toggle-quiz-question/', toggle_quiz_question, name='toggle_quiz_question'),
    
    # Waste Analytics URLs
    path('adminanalytics/', analytics_views.waste_analytics_dashboard, name='waste_analytics'),
    path('analytics/download-template/', analytics_views.download_excel_template, name='download_excel_template'),
    path('analytics/upload-excel/', analytics_views.upload_waste_data_excel, name='upload_waste_data_excel'),
    path('analytics/export-excel/', analytics_views.export_waste_data_excel, name='export_waste_data_excel'),
    path('analytics/export-pdf/', analytics_views.export_waste_data_pdf, name='export_waste_data_pdf'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
