from django.contrib import admin
from .models import Barangay, Users, PointsTransaction, Reward, Redemption, GarbageSchedule, Family, LoginAttempt
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta

@admin.register(Barangay)
class BarangayAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'family_code', 'family_name', 'barangay', 'address', 'city',
        'representative_name', 'representative_phone', 'total_members', 
        'total_family_points', 'status', 'created_at'
    )
    list_filter = ('status', 'barangay', 'city', 'created_at')
    search_fields = ('family_code', 'family_name', 'representative_name', 'representative_phone', 'address')
    readonly_fields = ('family_code', 'total_members', 'total_family_points')
    
    fieldsets = (
        ('Family Information', {
            'fields': ('family_code', 'family_name', 'barangay', 'address', 'city')
        }),
        ('Representative', {
            'fields': ('representative_name', 'representative_phone')
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approval_date', 'rejection_reason')
        }),
        ('Statistics', {
            'fields': ('total_members', 'total_family_points'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('barangay', 'approved_by')


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'username', 'full_name', 'phone', 'get_family_name', 
        'get_barangay', 'get_family_code', 'is_family_representative',
        'total_points', 'status', 'is_active', 'created_at'
    )
    list_filter = ('status', 'is_active', 'is_family_representative', 'family__barangay', 'family__status', 'gender')
    search_fields = ('username', 'full_name', 'phone', 'family__family_name', 'family__family_code')
    readonly_fields = ('family',)
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('username', 'full_name', 'phone', 'date_of_birth', 'gender')
        }),
        ('Family', {
            'fields': ('family', 'is_family_representative')
        }),
        ('Points & Activity', {
            'fields': ('total_points',)
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_staff', 'status', 'approved_by', 'approval_date', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )

    def get_family_name(self, obj):
        return obj.family.family_name
    get_family_name.short_description = 'Family Name'

    def get_barangay(self, obj):
        return obj.family.barangay.name
    get_barangay.short_description = 'Barangay'

    def get_family_code(self, obj):
        return obj.family.family_code
    get_family_code.short_description = 'Family Code'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('family', 'family__barangay')


@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'transaction_type', 'points_amount', 'description', 'transaction_date', 'processed_by')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('user__username', 'description')


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'points_required', 'stock', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'category__name')


@admin.register(Redemption)
class RedemptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'reward', 'points_used', 'requested_by', 'approved_by', 'redemption_date', 'claim_date')
    list_filter = ('redemption_date', 'claim_date')
    search_fields = ('user__username', 'reward__name')


@admin.register(GarbageSchedule)
class GarbageScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'barangay', 'day', 'start_time', 'end_time', 'is_active')
    list_filter = ('day', 'barangay', 'is_active')
    search_fields = ('barangay__name',)


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'username', 'ip_address', 'success_status', 'failure_reason', 'user_agent_short')
    list_filter = ('success', 'timestamp', 'failure_reason')
    search_fields = ('username', 'ip_address', 'failure_reason')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp', 'username', 'ip_address', 'success', 'user_agent', 'failure_reason')
    
    def success_status(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓ Success</span>')
        else:
            return format_html('<span style="color: red;">✗ Failed</span>')
    success_status.short_description = 'Status'
    
    def user_agent_short(self, obj):
        if len(obj.user_agent) > 50:
            return obj.user_agent[:50] + '...'
        return obj.user_agent
    user_agent_short.short_description = 'User Agent'
    
    def has_add_permission(self, request):
        return False  # Don't allow manual adding of login attempts
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing of login attempts
    
    fieldsets = (
        ('Login Information', {
            'fields': ('timestamp', 'username', 'success', 'failure_reason')
        }),
        ('Client Information', {
            'fields': ('ip_address', 'user_agent')
        }),
    )
    
    def get_queryset(self, request):
        # Only show recent attempts (last 30 days) by default
        qs = super().get_queryset(request)
        cutoff = timezone.now() - timedelta(days=30)
        return qs.filter(timestamp__gte=cutoff)
