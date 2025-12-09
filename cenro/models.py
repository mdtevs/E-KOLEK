from django.db import models
from django.utils import timezone
import uuid

# Models for CENRO app


# ---------- ADMIN USER ----------
class AdminUser(models.Model):
    """
    Admin user model for CENRO admin panel
    
    """
    ROLE_CHOICES = [
        ('super_admin', 'Super Administrator'),
        ('operations_manager', 'Operations Manager'),
        ('content_rewards_manager', 'Content & Rewards Manager'),
        ('security_analyst', 'Security & Reports Analyst'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True, help_text="Email address for notifications and credentials")
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='operations_manager')
    
    # Admin scope - which barangays can this admin manage
    assigned_barangays = models.ManyToManyField('accounts.Barangay', blank=True, help_text="Barangays this admin can manage")
    
    # Role-based permissions
    can_manage_users = models.BooleanField(default=False)
    can_manage_controls = models.BooleanField(default=False)
    can_manage_points = models.BooleanField(default=False)
    can_manage_rewards = models.BooleanField(default=False)
    can_manage_schedules = models.BooleanField(default=False)
    can_manage_security = models.BooleanField(default=False)
    can_manage_learning = models.BooleanField(default=False)
    can_manage_games = models.BooleanField(default=False)
    
    # View-only permissions
    can_view_all = models.BooleanField(default=False)  # For Security Analyst role
    
    # Admin approval workflow
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_admins')
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    
    # Security fields
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_date = models.DateTimeField(default=timezone.now)
    must_change_password = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    assigned_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        """Set permissions based on role"""
        if self.role == 'super_admin':
            # Super Admin: Full access to everything
            self.can_manage_users = True
            self.can_manage_controls = True
            self.can_manage_points = True
            self.can_manage_rewards = True
            self.can_manage_schedules = True
            self.can_manage_security = True
            self.can_manage_learning = True
            self.can_manage_games = True
            self.can_view_all = True
            
        elif self.role == 'operations_manager':
            # Operations Manager: Users, Points, Schedules
            self.can_manage_users = True
            self.can_manage_controls = False
            self.can_manage_points = True
            self.can_manage_rewards = False
            self.can_manage_schedules = True
            self.can_manage_security = False
            self.can_manage_learning = False
            self.can_manage_games = False
            self.can_view_all = False
            
        elif self.role == 'content_rewards_manager':
            # Content & Rewards Manager: Rewards, Learning, Games
            self.can_manage_users = False
            self.can_manage_controls = False
            self.can_manage_points = False
            self.can_manage_rewards = True
            self.can_manage_schedules = False
            self.can_manage_security = False
            self.can_manage_learning = True
            self.can_manage_games = True
            self.can_view_all = False
            
        elif self.role == 'security_analyst':
            # Security & Reports Analyst: Security management + view-only access
            self.can_manage_users = False
            self.can_manage_controls = False
            self.can_manage_points = False
            self.can_manage_rewards = False
            self.can_manage_schedules = False
            self.can_manage_security = True
            self.can_manage_learning = False
            self.can_manage_games = False
            self.can_view_all = True  # Can view all sections but not modify
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"
    
    def set_password(self, raw_password):
        """Set password using Django's password hashing"""
        from django.contrib.auth.hashers import make_password
        self.password_hash = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check password using Django's password verification"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password_hash)
    
    def is_account_locked(self):
        """Check if account is locked due to failed login attempts"""
        if self.account_locked_until and timezone.now() < self.account_locked_until:
            return True
        return False
    
    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration"""
        from datetime import timedelta
        self.account_locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save(update_fields=['account_locked_until'])
    
    def unlock_account(self):
        """Unlock account and reset failed login attempts"""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
    
    def increment_failed_login(self):
        """Increment failed login attempts and lock if threshold exceeded"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
            self.lock_account(duration_minutes=30)
        self.save(update_fields=['failed_login_attempts'])
    
    def reset_failed_login(self):
        """Reset failed login attempts on successful login"""
        if self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            self.save(update_fields=['failed_login_attempts'])
    
    def can_login(self):
        """Check if admin can login (approved, active, not locked)"""
        return (self.status == 'approved' and 
                self.is_active and 
                not self.is_account_locked())
    
    def approve_admin(self, approved_by_user):
        """Approve admin registration"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approval_date = timezone.now()
        self.rejection_reason = None
        self.save()
    
    def suspend_admin(self, suspended_by_user, reason):
        """Suspend admin account"""
        self.status = 'suspended'
        self.approved_by = suspended_by_user
        self.approval_date = timezone.now()
        self.rejection_reason = reason
        self.is_active = False
        self.save()
    
    def can_manage_barangay(self, barangay):
        """Check if admin can manage a specific barangay"""
        if self.role == 'super_admin':
            return True
        return self.assigned_barangays.filter(id=barangay.id).exists()
    
    def get_manageable_families(self):
        """Get families this admin can manage"""
        from accounts.models import Family
        if self.role == 'super_admin':
            return Family.objects.all()
        return Family.objects.filter(barangay__in=self.assigned_barangays.all())
    
    def get_manageable_users(self):
        """Get users this admin can manage"""
        from accounts.models import Users
        if self.role == 'super_admin':
            return Users.objects.all()
        return Users.objects.filter(family__barangay__in=self.assigned_barangays.all())


# ---------- ADMIN ACTION HISTORY ----------
class AdminActionHistory(models.Model):
    """
    Model to track all admin actions for audit trail
    Moved from accounts app to keep admin-related models together
    """
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('password_reset', 'Password Reset'),
        ('create_admin', 'Create Admin'),
        ('approve_admin', 'Approve Admin'),
        ('reject_admin', 'Reject Admin'),
        ('suspend_admin', 'Suspend Admin'),
        ('unsuspend_admin', 'Unsuspend Admin'),
        ('reactivate_admin', 'Reactivate Admin'),
        ('edit_barangays', 'Edit Barangays'),
        ('lock_admin', 'Lock Admin'),
        ('unlock_admin', 'Unlock Admin'),
        ('view_users', 'View Users'),
        ('manage_controls', 'Manage Controls'),
        ('security_action', 'Security Action'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who performed the action
    admin_user = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='actions_performed')
    
    # Who was affected (optional - could be null for general actions)
    target_admin = models.ForeignKey(AdminUser, on_delete=models.CASCADE, null=True, blank=True, related_name='actions_received')
    
    # Action details
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    details = models.JSONField(default=dict, blank=True)  # Store additional data
    
    # Context information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    session_key = models.CharField(max_length=255, null=True, blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Admin Action History'
        verbose_name_plural = 'Admin Action Histories'
        indexes = [
            models.Index(fields=['admin_user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['target_admin', '-timestamp']),
        ]
    
    def __str__(self):
        target_info = f" on {self.target_admin.username}" if self.target_admin else ""
        return f"{self.admin_user.username} - {self.get_action_display()}{target_info} at {self.timestamp}"
    
    def get_action_color(self):
        """Return color class for different action types"""
        color_map = {
            'login': 'text-green-600',
            'logout': 'text-gray-600',
            'password_change': 'text-blue-600',
            'password_reset': 'text-orange-600',
            'create_admin': 'text-green-600',
            'approve_admin': 'text-green-600',
            'reject_admin': 'text-red-600',
            'suspend_admin': 'text-yellow-600',
            'unsuspend_admin': 'text-green-600',
            'reactivate_admin': 'text-green-600',
            'edit_barangays': 'text-blue-600',
            'lock_admin': 'text-red-600',
            'unlock_admin': 'text-green-600',
            'security_action': 'text-purple-600',
        }
        return color_map.get(self.action, 'text-gray-600')
    
    def get_action_icon(self):
        """Return icon class for different action types"""
        icon_map = {
            'login': 'bx-log-in',
            'logout': 'bx-log-out',
            'password_change': 'bx-key',
            'password_reset': 'bx-reset',
            'create_admin': 'bx-user-plus',
            'approve_admin': 'bx-check-circle',
            'reject_admin': 'bx-x-circle',
            'suspend_admin': 'bx-pause-circle',
            'unsuspend_admin': 'bx-play-circle',
            'reactivate_admin': 'bx-refresh',
            'edit_barangays': 'bx-edit',
            'lock_admin': 'bx-lock',
            'unlock_admin': 'bx-lock-open',
            'security_action': 'bx-shield',
        }
        return icon_map.get(self.action, 'bx-info-circle')


# ---------- ADMIN NOTIFICATION ----------
class AdminNotification(models.Model):
    """
    Model for admin notifications - triggered by system events like new user registrations
    """
    NOTIFICATION_TYPES = [
        ('new_registration', 'New User Registration'),
        ('user_approved', 'User Approved'),
        ('user_rejected', 'User Rejected'),
        ('system_alert', 'System Alert'),
        ('admin_account_locked', 'Admin Account Locked'),
        ('admin_account_suspended', 'Admin Account Suspended'),
        ('admin_account_unlocked', 'Admin Account Unlocked'),
        ('admin_account_reactivated', 'Admin Account Reactivated'),
        ('barangay_assignment_changed', 'Barangay Assignment Changed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin_user = models.ForeignKey(
        AdminUser, 
        on_delete=models.CASCADE, 
        related_name='admin_notifications',
        null=True,
        blank=True,
        help_text="Specific admin this notification is for (null = all admins)"
    )
    notification_type = models.CharField(
        max_length=50, 
        choices=NOTIFICATION_TYPES,
        default='system_alert'
    )
    message = models.TextField(help_text="Notification message text")
    link_url = models.CharField(
        max_length=500, 
        blank=True,
        help_text="URL to navigate to when notification is clicked"
    )
    is_read = models.BooleanField(default=False)
    related_user = models.ForeignKey(
        'accounts.Users',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='admin_notifications',
        help_text="User related to this notification (e.g., newly registered user)"
    )
    related_admin = models.ForeignKey(
        AdminUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications_about_admin',
        help_text="Admin user this notification is about (for admin account events)"
    )
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin_user', 'is_read', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
        ]
    
    def __str__(self):
        admin_str = self.admin_user.username if self.admin_user else "All Admins"
        return f"{self.notification_type} for {admin_str} - {self.message[:50]}"
    
    def mark_as_read(self):
        """Mark notification as read with timestamp"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @classmethod
    def create_new_registration_notification(cls, user):
        """
        Create notification for new user registration
        Sends to all admins who can manage users in this user's barangay
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.warning(f"="*80)
        logger.warning(f"[NOTIFICATION] 🔔🔔🔔 CREATE_NEW_REGISTRATION_NOTIFICATION CALLED 🔔🔔🔔")
        logger.warning(f"[NOTIFICATION] User: {user.username}")
        logger.warning(f"="*80)
        
        # Get user's barangay
        user_barangay = user.family.barangay
        logger.info(f"[NOTIFICATION] User barangay: {user_barangay.name}")
        
        # Get all active admins with user management permission
        admins_with_permission = AdminUser.objects.filter(
            is_active=True,
            status='approved',
            can_manage_users=True
        )
        
        logger.info(f"[NOTIFICATION] Found {admins_with_permission.count()} admins with user management permission")
        
        message = f"New user registration: {user.full_name} from {user.family.family_name} family in {user.family.barangay.name}"
        link_url = "/adminuser/"  # Link to user management page (correct URL without cenro/ prefix)
        
        notifications = []
        for admin in admins_with_permission:
            # Check if admin can manage this barangay
            # Super Admins can see all, Operations Managers only see their assigned barangays
            can_manage = admin.role == 'super_admin' or admin.can_manage_barangay(user_barangay)
            logger.info(f"[NOTIFICATION] Admin: {admin.username} | Role: {admin.role} | Can manage: {can_manage}")
            
            if can_manage:
                notification = cls(
                    admin_user=admin,
                    notification_type='new_registration',
                    message=message,
                    link_url=link_url,
                    related_user=user
                )
                notifications.append(notification)
                logger.info(f"[NOTIFICATION] ✅ Added notification for admin: {admin.username}")
        
        # Bulk create all notifications (one per admin)
        if notifications:
            cls.objects.bulk_create(notifications)
            logger.info(f"[NOTIFICATION] ✅ Bulk created {len(notifications)} notifications")
        else:
            logger.warning(f"[NOTIFICATION] ⚠️ No notifications created - no matching admins found")
        
        return notifications
    
    @classmethod
    def create_admin_locked_notification(cls, locked_admin):
        """
        Create notification when an admin account is locked due to failed login attempts
        Sends to Super Admins and Security Analysts only
        """
        # Get Super Admins and Security Analysts (who can manage security)
        admins_to_notify = AdminUser.objects.filter(
            is_active=True,
            status='approved'
        ).filter(
            models.Q(role='super_admin') | models.Q(can_manage_security=True)
        ).exclude(id=locked_admin.id)  # Don't notify the locked admin
        
        message = f"Admin account locked: {locked_admin.full_name} ({locked_admin.username}) has been locked due to multiple failed login attempts"
        link_url = "/admin/management/"  # Link to admin management page
        
        notifications = []
        for admin in admins_to_notify:
            notification = cls(
                admin_user=admin,
                notification_type='admin_account_locked',
                message=message,
                link_url=link_url,
                related_admin=locked_admin
            )
            notifications.append(notification)
        
        # Bulk create all notifications
        if notifications:
            cls.objects.bulk_create(notifications)
        
        return notifications
    
    @classmethod
    def create_admin_suspended_notification(cls, suspended_admin, suspended_by, reason):
        """
        Create notification when an admin account is suspended
        Sends to Super Admins only (except the one who performed the suspension)
        """
        # Get all Super Admins except the one who suspended and the suspended admin
        admins_to_notify = AdminUser.objects.filter(
            is_active=True,
            status='approved',
            role='super_admin'
        ).exclude(id__in=[suspended_admin.id, suspended_by.id])
        
        message = f"Admin account suspended: {suspended_admin.full_name} ({suspended_admin.username}) has been suspended by {suspended_by.full_name}. Reason: {reason}"
        link_url = "/admin/management/"  # Link to admin management page
        
        notifications = []
        for admin in admins_to_notify:
            notification = cls(
                admin_user=admin,
                notification_type='admin_account_suspended',
                message=message,
                link_url=link_url,
                related_admin=suspended_admin
            )
            notifications.append(notification)
        
        # Bulk create all notifications
        if notifications:
            cls.objects.bulk_create(notifications)
        
        return notifications
    
    @classmethod
    def create_admin_unlocked_notification(cls, unlocked_admin, unlocked_by):
        """
        Create notification when an admin account is unlocked
        Sends to the affected admin and Super Admins
        """
        
        # Notify the unlocked admin
        notifications = []
        
        # Notification for the unlocked admin themselves
        unlock_message = f"Your admin account has been unlocked by {unlocked_by.full_name}. You can now log in again."
        notifications.append(cls(
            admin_user=unlocked_admin,
            notification_type='admin_account_unlocked',
            message=unlock_message,
            link_url="/cenro/admin/login/",
            related_admin=unlocked_admin
        ))
        
        # Notification for Super Admins (except the one who unlocked)
        super_admins = AdminUser.objects.filter(
            is_active=True,
            status='approved',
            role='super_admin'
        ).exclude(id__in=[unlocked_admin.id, unlocked_by.id])
        
        admin_message = f"Admin account unlocked: {unlocked_admin.full_name} ({unlocked_admin.username}) has been unlocked by {unlocked_by.full_name}"
        for admin in super_admins:
            notifications.append(cls(
                admin_user=admin,
                notification_type='admin_account_unlocked',
                message=admin_message,
                link_url="/admin/management/",
                related_admin=unlocked_admin
            ))
        
        # Bulk create all notifications
        if notifications:
            cls.objects.bulk_create(notifications)
        
        return notifications
    
    @classmethod
    def create_admin_reactivated_notification(cls, reactivated_admin, reactivated_by):
        """
        Create notification when a suspended admin account is reactivated
        Sends to the affected admin and Super Admins
        """
        notifications = []
        
        # Notification for the reactivated admin themselves
        reactivate_message = f"Your admin account has been reactivated by {reactivated_by.full_name}. You can now log in again."
        notifications.append(cls(
            admin_user=reactivated_admin,
            notification_type='admin_account_reactivated',
            message=reactivate_message,
            link_url="/cenro/admin/login/",
            related_admin=reactivated_admin
        ))
        
        # Notification for Super Admins (except the one who reactivated)
        super_admins = AdminUser.objects.filter(
            is_active=True,
            status='approved',
            role='super_admin'
        ).exclude(id__in=[reactivated_admin.id, reactivated_by.id])
        
        admin_message = f"Admin account reactivated: {reactivated_admin.full_name} ({reactivated_admin.username}) has been reactivated by {reactivated_by.full_name}"
        for admin in super_admins:
            notifications.append(cls(
                admin_user=admin,
                notification_type='admin_account_reactivated',
                message=admin_message,
                link_url="/admin/management/",
                related_admin=reactivated_admin
            ))
        
        # Bulk create all notifications
        if notifications:
            cls.objects.bulk_create(notifications)
        
        return notifications
    
    @classmethod
    def create_barangay_assignment_notification(cls, affected_admin, changed_by, barangay_info):
        """
        Create notification when an Operations Manager's barangay assignments are changed
        Sends to the affected Operations Manager and Super Admins
        """
        notifications = []
        
        # Notification for the affected Operations Manager
        manager_message = f"Your barangay assignments have been updated by {changed_by.full_name}. New assignments: {barangay_info}"
        notifications.append(cls(
            admin_user=affected_admin,
            notification_type='barangay_assignment_changed',
            message=manager_message,
            link_url="/adminuser/dashboard/",
            related_admin=affected_admin
        ))
        
        # Notification for Super Admins (except the one who made the change)
        super_admins = AdminUser.objects.filter(
            is_active=True,
            status='approved',
            role='super_admin'
        ).exclude(id__in=[affected_admin.id, changed_by.id])
        
        admin_message = f"Barangay assignments updated for {affected_admin.full_name} ({affected_admin.username}) by {changed_by.full_name}: {barangay_info}"
        for admin in super_admins:
            notifications.append(cls(
                admin_user=admin,
                notification_type='barangay_assignment_changed',
                message=admin_message,
                link_url="/adminuser/manage/",
                related_admin=affected_admin
            ))
        
        # Bulk create all notifications
        if notifications:
            cls.objects.bulk_create(notifications)
        
        return notifications


# ---------- TERMS AND CONDITIONS ----------
class TermsAndConditions(models.Model):
    """
    Model for managing Terms and Conditions
    Supports both manual text entry and file upload (PDF/DOC)
    Maintains English and Tagalog versions
    """
    LANGUAGE_CHOICES = [
        ('english', 'English'),
        ('tagalog', 'Tagalog'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    language = models.CharField(
        max_length=10, 
        choices=LANGUAGE_CHOICES,
        help_text="Language of the terms and conditions"
    )
    title = models.CharField(
        max_length=255,
        help_text="Title of the terms document"
    )
    version = models.CharField(
        max_length=50,
        help_text="Version number (e.g., 1.0, 2.1)"
    )
    content = models.TextField(
        help_text="Full text content of the terms and conditions"
    )
    file = models.FileField(
        upload_to='terms_documents/',
        null=True,
        blank=True,
        help_text="Optional: Upload PDF or DOC file"
    )
    
    # Status and metadata
    is_active = models.BooleanField(
        default=False,
        help_text="Only one version per language can be active at a time"
    )
    created_by = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='terms_created'
    )
    updated_by = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='terms_updated'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Terms and Conditions'
        verbose_name_plural = 'Terms and Conditions'
        indexes = [
            models.Index(fields=['language', 'is_active']),
            models.Index(fields=['-created_at']),
        ]
        # Ensure only one active version per language
        constraints = [
            models.UniqueConstraint(
                fields=['language', 'is_active'],
                condition=models.Q(is_active=True),
                name='unique_active_terms_per_language'
            )
        ]
    
    def __str__(self):
        active_status = "Active" if self.is_active else "Inactive"
        return f"{self.get_language_display()} - {self.title} v{self.version} ({active_status})"
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure only one active version per language
        """
        if self.is_active:
            # Deactivate all other versions for this language
            TermsAndConditions.objects.filter(
                language=self.language,
                is_active=True
            ).exclude(id=self.id).update(is_active=False)
        
        super().save(*args, **kwargs)
    
    def get_file_extension(self):
        """Get file extension if file exists"""
        if self.file:
            import os
            return os.path.splitext(self.file.name)[1].lower()
        return None
    
    def extract_content_from_file(self):
        """
        Extract text content from uploaded file (PDF or DOC)
        This is called when a file is uploaded to auto-fill the content field
        """
        if not self.file:
            return None
        
        file_ext = self.get_file_extension()
        
        try:
            if file_ext == '.pdf':
                return self._extract_from_pdf()
            elif file_ext in ['.doc', '.docx']:
                return self._extract_from_docx()
            else:
                return None
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error extracting content from file: {str(e)}")
            return None
    
    def _extract_from_pdf(self):
        """Extract text from PDF file"""
        try:
            import PyPDF2
            import io
            
            # Open the file from storage or memory
            if hasattr(self.file, 'read'):
                # File is already open
                file_content = self.file.read()
                self.file.seek(0)  # Reset file pointer
            else:
                # File is stored, open it
                from django.core.files.storage import default_storage
                with default_storage.open(self.file.name, 'rb') as f:
                    file_content = f.read()
            
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_content = []
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
            
            return '\n\n'.join(text_content)
        except ImportError:
            return "PyPDF2 not installed. Please install it to extract PDF content."
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"
    
    def _extract_from_docx(self):
        """Extract text from DOCX file"""
        try:
            import docx
            import io
            
            # Open the file from storage or memory
            if hasattr(self.file, 'read'):
                # File is already open
                file_content = self.file.read()
                self.file.seek(0)  # Reset file pointer
            else:
                # File is stored, open it
                from django.core.files.storage import default_storage
                with default_storage.open(self.file.name, 'rb') as f:
                    file_content = f.read()
            
            doc_file = io.BytesIO(file_content)
            doc = docx.Document(doc_file)
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            return '\n\n'.join(text_content)
        except ImportError:
            return "python-docx not installed. Please install it to extract DOCX content."
        except Exception as e:
            return f"Error extracting DOCX: {str(e)}"
    
    @classmethod
    def get_active_terms(cls, language='english'):
        """Get the active terms for a specific language"""
        try:
            return cls.objects.get(language=language, is_active=True)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_both_active_terms(cls):
        """Get both active English and Tagalog terms"""
        return {
            'english': cls.get_active_terms('english'),
            'tagalog': cls.get_active_terms('tagalog')
        }
