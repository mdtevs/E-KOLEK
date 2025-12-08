"""
Admin interface for mobile login app
Manages biometric devices and login attempts
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import BiometricDevice, BiometricLoginAttempt


@admin.register(BiometricDevice)
class BiometricDeviceAdmin(admin.ModelAdmin):
    """Admin interface for biometric device management"""
    
    list_display = ['device_name', 'user_link', 'device_type', 'status_badge', 
                    'is_trusted', 'failed_attempts', 'last_used_at', 'registered_at']
    list_filter = ['device_type', 'is_active', 'is_trusted', 'registered_at']
    search_fields = ['device_name', 'device_id', 'user__username', 'user__phone']
    readonly_fields = ['id', 'registered_at', 'last_used_at', 'last_verified_at', 
                      'registration_ip', 'last_ip', 'last_challenge', 'challenge_expires_at']
    
    fieldsets = (
        ('Device Information', {
            'fields': ('id', 'user', 'device_id', 'device_name', 'device_type', 
                      'device_model', 'os_version', 'app_version')
        }),
        ('Security', {
            'fields': ('credential_id', 'public_key', 'device_fingerprint', 
                      'last_challenge', 'challenge_expires_at')
        }),
        ('Status', {
            'fields': ('is_active', 'is_trusted', 'failed_attempts', 'max_failed_attempts', 
                      'expires_at')
        }),
        ('Timestamps & IP', {
            'fields': ('registered_at', 'last_used_at', 'last_verified_at', 
                      'registration_ip', 'last_ip')
        }),
    )
    
    def user_link(self, obj):
        """Display clickable user link"""
        if obj.user:
            return format_html(
                '<a href="/admin/accounts/users/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return '-'
    user_link.short_description = 'User'
    
    def status_badge(self, obj):
        """Display device status with color badge"""
        if not obj.is_active:
            return format_html('<span style="color: red;">❌ Inactive</span>')
        elif obj.is_locked():
            return format_html('<span style="color: orange;">🔒 Locked</span>')
        elif obj.is_expired():
            return format_html('<span style="color: orange;">⏰ Expired</span>')
        else:
            return format_html('<span style="color: green;">✅ Active</span>')
    status_badge.short_description = 'Status'
    
    actions = ['activate_devices', 'deactivate_devices', 'reset_failed_attempts']
    
    def activate_devices(self, request, queryset):
        """Activate selected devices"""
        count = queryset.update(is_active=True, failed_attempts=0)
        self.message_user(request, f'{count} device(s) activated successfully.')
    activate_devices.short_description = 'Activate selected devices'
    
    def deactivate_devices(self, request, queryset):
        """Deactivate selected devices"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} device(s) deactivated successfully.')
    deactivate_devices.short_description = 'Deactivate selected devices'
    
    def reset_failed_attempts(self, request, queryset):
        """Reset failed attempts counter"""
        count = queryset.update(failed_attempts=0)
        self.message_user(request, f'Reset failed attempts for {count} device(s).')
    reset_failed_attempts.short_description = 'Reset failed attempts'


@admin.register(BiometricLoginAttempt)
class BiometricLoginAttemptAdmin(admin.ModelAdmin):
    """Admin interface for biometric login attempt auditing"""
    
    list_display = ['attempted_at', 'user_link', 'device_link', 'success_badge', 
                    'failure_reason', 'ip_address']
    list_filter = ['success', 'attempted_at']
    search_fields = ['user__username', 'user__phone', 'device__device_name', 
                    'attempted_device_id', 'ip_address', 'failure_reason']
    readonly_fields = ['id', 'user', 'device', 'success', 'failure_reason', 
                      'attempted_device_id', 'ip_address', 'user_agent', 'attempted_at']
    date_hierarchy = 'attempted_at'
    
    def has_add_permission(self, request):
        """Prevent manual creation of login attempts"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent modification of login attempts"""
        return False
    
    def user_link(self, obj):
        """Display clickable user link"""
        if obj.user:
            return format_html(
                '<a href="/admin/accounts/users/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return 'Unknown'
    user_link.short_description = 'User'
    
    def device_link(self, obj):
        """Display clickable device link"""
        if obj.device:
            return format_html(
                '<a href="/admin/mobilelogin/biometricdevice/{}/change/">{}</a>',
                obj.device.id,
                obj.device.device_name
            )
        return 'Unknown Device'
    device_link.short_description = 'Device'
    
    def success_badge(self, obj):
        """Display success/failure badge"""
        if obj.success:
            return format_html('<span style="color: green;">✅ Success</span>')
        else:
            return format_html('<span style="color: red;">❌ Failed</span>')
    success_badge.short_description = 'Result'

