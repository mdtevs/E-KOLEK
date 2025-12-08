"""
Models for mobile login app
Handles biometric device registration and authentication
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import Users


class BiometricDevice(models.Model):
    """
    Stores registered biometric-enabled devices for users.
    Each device has a unique identifier and stores encrypted biometric credentials.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='biometric_devices')
    
    # Device identification
    device_id = models.CharField(max_length=255, unique=True, db_index=True, 
                                  help_text="Unique device identifier from mobile app")
    device_name = models.CharField(max_length=255, help_text="User-friendly device name (e.g., 'My iPhone 13')")
    device_type = models.CharField(max_length=50, help_text="Device type (ios/android)")
    device_model = models.CharField(max_length=255, blank=True, help_text="Device model/brand")
    os_version = models.CharField(max_length=50, blank=True, help_text="Operating system version")
    app_version = models.CharField(max_length=50, blank=True, help_text="App version")
    
    # Biometric credentials (encrypted storage)
    public_key = models.TextField(help_text="Device public key for biometric verification")
    credential_id = models.CharField(max_length=500, unique=True, db_index=True,
                                     help_text="Unique credential identifier for this biometric registration")
    
    # Security and validation
    device_fingerprint = models.CharField(max_length=255, help_text="Device fingerprint hash for additional security")
    last_challenge = models.CharField(max_length=255, blank=True, null=True,
                                      help_text="Last authentication challenge sent to device")
    challenge_expires_at = models.DateTimeField(blank=True, null=True,
                                                help_text="When the current challenge expires")
    
    # Status tracking
    is_active = models.BooleanField(default=True, help_text="Whether this device is currently active")
    is_trusted = models.BooleanField(default=False, 
                                     help_text="Trusted devices skip additional verification")
    failed_attempts = models.IntegerField(default=0, help_text="Failed authentication attempts counter")
    max_failed_attempts = models.IntegerField(default=5, help_text="Max failed attempts before device lock")
    
    # Timestamps
    registered_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(blank=True, null=True)
    last_verified_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True, 
                                      help_text="Optional expiration date for device registration")
    
    # Metadata
    registration_ip = models.GenericIPAddressField(blank=True, null=True)
    last_ip = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        db_table = 'biometric_devices'
        ordering = ['-last_used_at', '-registered_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_id', 'is_active']),
            models.Index(fields=['credential_id']),
        ]
        verbose_name = 'Biometric Device'
        verbose_name_plural = 'Biometric Devices'
    
    def __str__(self):
        return f"{self.device_name} ({self.user.username})"
    
    def is_locked(self):
        """Check if device is locked due to failed attempts"""
        return self.failed_attempts >= self.max_failed_attempts
    
    def is_expired(self):
        """Check if device registration has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def increment_failed_attempts(self):
        """Increment failed authentication attempts"""
        self.failed_attempts += 1
        if self.failed_attempts >= self.max_failed_attempts:
            self.is_active = False
        self.save(update_fields=['failed_attempts', 'is_active'])
    
    def reset_failed_attempts(self):
        """Reset failed attempts counter on successful authentication"""
        self.failed_attempts = 0
        self.save(update_fields=['failed_attempts'])
    
    def update_last_used(self, ip_address=None):
        """Update last used timestamp and IP"""
        self.last_used_at = timezone.now()
        if ip_address:
            self.last_ip = ip_address
        self.save(update_fields=['last_used_at', 'last_ip'])
    
    def deactivate(self):
        """Deactivate this device"""
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    def generate_challenge(self):
        """Generate a new authentication challenge"""
        import secrets
        challenge = secrets.token_urlsafe(32)
        self.last_challenge = challenge
        self.challenge_expires_at = timezone.now() + timezone.timedelta(minutes=5)
        self.save(update_fields=['last_challenge', 'challenge_expires_at'])
        return challenge
    
    def verify_challenge(self, challenge):
        """Verify that the provided challenge matches and hasn't expired"""
        if not self.last_challenge or not self.challenge_expires_at:
            return False
        
        if timezone.now() > self.challenge_expires_at:
            return False
        
        return self.last_challenge == challenge
    
    def clear_challenge(self):
        """Clear the current challenge after use"""
        self.last_challenge = None
        self.challenge_expires_at = None
        self.save(update_fields=['last_challenge', 'challenge_expires_at'])


class BiometricLoginAttempt(models.Model):
    """
    Audit log for biometric login attempts
    Tracks both successful and failed authentication attempts
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(BiometricDevice, on_delete=models.CASCADE, 
                               related_name='login_attempts', null=True, blank=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='biometric_login_attempts')
    
    # Attempt details
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=255, blank=True)
    attempted_device_id = models.CharField(max_length=255, blank=True, help_text="Device ID used in attempt")
    
    # Request metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamp
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'biometric_login_attempts'
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['user', '-attempted_at']),
            models.Index(fields=['device', '-attempted_at']),
            models.Index(fields=['success', '-attempted_at']),
        ]
        verbose_name = 'Biometric Login Attempt'
        verbose_name_plural = 'Biometric Login Attempts'
    
    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"{status} - {self.user.username} at {self.attempted_at}"
