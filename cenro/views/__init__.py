"""
CENRO Views Package
Organized view modules for better maintainability
"""

# Import all views to maintain backward compatibility with urls.py
from .dashboard_views import (
    dashboard,
    admin_preview_user_dashboard,
    get_dashboard_metrics,
)

from .user_views import (
    adminuser,
    view_user,
    view_single_idcard,
    edit_user,
    delete_user,
    approve_user,
    reject_user,
    get_user_by_id,
    get_user_by_family_code,
)

from .control_views import (
    admincontrol,
    add_waste_type,
    edit_waste_type,
    delete_waste_type,
    add_barangay,
    edit_barangay,
    delete_barangay,
    add_reward_category,
    edit_reward_category,
    delete_reward_category,
    # Terms and Conditions management
    add_terms,
    edit_terms,
    delete_terms,
    toggle_active_terms,
    extract_file_content,
    get_terms_data,
)

from .points_views import (
    adminpoints,
    save_waste_transaction,
)

from .reward_views import (
    adminrewards,
    reward_history,
    add_reward,
    edit_reward,
    delete_reward,
    add_stock,
    remove_stock,
    redeem_reward_api,
)

from .schedule_views import (
    adminschedule,
    add_schedule,
    edit_schedule,
    delete_schedule,
)

from .game_views import (
    admingames,
    adminquiz,
    add_question,
    delete_question,
    add_category,
    delete_category,
    add_item,
    delete_item,
    update_game_cooldown,
    get_game_cooldown,
    test_session_debug,
)

from .learning_views import (
    adminlearn,
    add_video,
    edit_video,
    toggle_video,
    delete_video,
    quiz_management,
    quiz_questions,
    quiz_results,
    add_quiz_question,
    edit_quiz_question,
    delete_quiz_question,
    toggle_quiz_question,
)

from .security_views import (
    adminsecurity,
    generate_security_report,
)

from .notification_views import (
    get_admin_notifications_unread_count,
    get_admin_notifications_list,
    mark_admin_notification_read,
    mark_all_admin_notifications_read,
)

from .utils import (
    generate_qr_code_base64,
    get_time_ago,
)

# Export all views for urls.py
__all__ = [
    # Dashboard
    'dashboard',
    'admin_preview_user_dashboard',
    'get_dashboard_metrics',
    
    # Users
    'adminuser',
    'view_user',
    'view_single_idcard',
    'edit_user',
    'delete_user',
    'approve_user',
    'reject_user',
    'get_user_by_id',
    'get_user_by_family_code',
    
    # Controls
    'admincontrol',
    'add_waste_type',
    'edit_waste_type',
    'delete_waste_type',
    'add_barangay',
    'edit_barangay',
    'delete_barangay',
    'add_reward_category',
    'edit_reward_category',
    'delete_reward_category',
    'add_terms',
    'edit_terms',
    'delete_terms',
    'toggle_active_terms',
    'extract_file_content',
    
    # Points
    'adminpoints',
    'save_waste_transaction',
    
    # Rewards
    'adminrewards',
    'reward_history',
    'add_reward',
    'edit_reward',
    'delete_reward',
    'add_stock',
    'remove_stock',
    'redeem_reward_api',
    
    # Schedules
    'adminschedule',
    'add_schedule',
    'edit_schedule',
    'delete_schedule',
    
    # Games
    'admingames',
    'adminquiz',
    'add_question',
    'delete_question',
    'add_category',
    'delete_category',
    'add_item',
    'delete_item',
    
    # Learning
    'adminlearn',
    'add_video',
    'edit_video',
    'toggle_video',
    'delete_video',
    'quiz_management',
    'quiz_questions',
    'quiz_results',
    'add_quiz_question',
    'edit_quiz_question',
    'delete_quiz_question',
    'toggle_quiz_question',
    
    # Security
    'adminsecurity',
    'generate_security_report',
    
    # Notifications
    'get_admin_notifications_unread_count',
    'get_admin_notifications_list',
    'mark_admin_notification_read',
    'mark_all_admin_notifications_read',
    
    # Utils
    'generate_qr_code_base64',
    'get_time_ago',
]
