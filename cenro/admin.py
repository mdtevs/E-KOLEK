from django.contrib import admin
from .models import AdminUser, AdminActionHistory, AdminNotification
from django.utils.html import format_html
from django.utils import timezone


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'full_name', 'role', 'status', 'is_active', 'last_login')
    list_filter = ('role', 'status', 'is_active', 'assigned_barangays')
    search_fields = ('username', 'full_name', 'email')
    filter_horizontal = ('assigned_barangays',)
    readonly_fields = ('created_at', 'last_login', 'password_changed_date', 'account_locked_until')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'full_name', 'email', 'password_hash')
        }),
        ('Role & Permissions', {
            'fields': (
                'role', 'assigned_barangays',
                'can_manage_users', 'can_manage_controls', 'can_manage_points',
                'can_manage_rewards', 'can_manage_schedules', 'can_manage_security',
                'can_manage_learning', 'can_manage_games', 'can_view_all'
            )
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approval_date', 'rejection_reason', 'is_active')
        }),
        ('Security', {
            'fields': ('failed_login_attempts', 'account_locked_until', 'password_changed_date', 'must_change_password')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_login', 'assigned_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('approved_by', 'assigned_by')


@admin.register(AdminActionHistory)
class AdminActionHistoryAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'admin_user', 'action', 'target_admin', 'ip_address', 'short_description')
    list_filter = ('action', 'timestamp')
    search_fields = ('admin_user__username', 'target_admin__username', 'description', 'ip_address')
    readonly_fields = ('admin_user', 'target_admin', 'action', 'description', 'details', 'ip_address', 'user_agent', 'session_key', 'timestamp')
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Action Information', {
            'fields': ('timestamp', 'action', 'admin_user', 'target_admin', 'description')
        }),
        ('Context', {
            'fields': ('ip_address', 'user_agent', 'session_key')
        }),
        ('Additional Details', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
    )
    
    def short_description(self, obj):
        if len(obj.description) > 80:
            return obj.description[:80] + '...'
        return obj.description
    short_description.short_description = 'Description'
    
    def has_add_permission(self, request):
        return False  # Don't allow manual adding of history records
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing of history records
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('admin_user', 'target_admin')


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'admin_user', 'notification_type', 'is_read', 'short_message')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('message', 'admin_user__username')
    readonly_fields = ('created_at', 'read_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Notification Info', {
            'fields': ('admin_user', 'notification_type', 'message', 'link_url')
        }),
        ('Related Objects', {
            'fields': ('related_user', 'related_admin')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at', 'read_at')
        }),
    )
    
    def short_message(self, obj):
        if len(obj.message) > 60:
            return obj.message[:60] + '...'
        return obj.message
    short_message.short_description = 'Message'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('admin_user', 'related_user', 'related_admin')
