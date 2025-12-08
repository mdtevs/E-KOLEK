"""
Enhanced login security features for E-KOLEK
"""

import logging
from datetime import datetime, timedelta
from django.core.cache import cache
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from django.utils import timezone
from django.db import models
from django.conf import settings
import hashlib
import json
from eko.security_utils import get_client_ip, log_security_event


logger = logging.getLogger(__name__)


def get_login_attempt_model():
    """Lazy import to avoid circular import issues"""
    from .models import LoginAttempt
    return LoginAttempt


class UserLoginSecurity:
    """Enhanced login security manager"""
    
    @staticmethod
    def get_login_cache_key(identifier, attempt_type='login'):
        """Generate cache key for login attempts"""
        hashed = hashlib.md5(str(identifier).encode()).hexdigest()
        return f"{attempt_type}_attempts_{hashed}"
    
    @staticmethod
    def is_account_locked(username):
        """Check if account is temporarily locked"""
        cache_key = UserLoginSecurity.get_login_cache_key(username, 'account_lock')
        return cache.get(cache_key, False)
    
    @staticmethod
    def lock_account(username, duration_minutes=30):
        """Temporarily lock an account"""
        cache_key = UserLoginSecurity.get_login_cache_key(username, 'account_lock')
        cache.set(cache_key, True, timeout=duration_minutes * 60)
        
        log_security_event(
            'ACCOUNT_LOCKED',
            details=f'Account {username} locked for {duration_minutes} minutes'
        )
    
    @staticmethod
    def get_failed_attempts(username):
        """Get number of failed attempts for username"""
        cache_key = UserLoginSecurity.get_login_cache_key(username, 'failed')
        return cache.get(cache_key, 0)
    
    @staticmethod
    def increment_failed_attempts(username, ip_address, user_agent='', failure_reason=''):
        """Increment failed login attempts"""
        cache_key = UserLoginSecurity.get_login_cache_key(username, 'failed')
        attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, attempts, timeout=1800)  # 30 minutes
        
        # Log the attempt
        try:
            LoginAttempt = get_login_attempt_model()
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                success=False,
                user_agent=user_agent[:500],  # Limit length
                failure_reason=failure_reason
            )
        except Exception as e:
            logger.error(f"Failed to log login attempt: {e}")
        
        # Lock account after 5 failed attempts
        if attempts >= 5:
            UserLoginSecurity.lock_account(username, 30)
            log_security_event(
                'ACCOUNT_AUTO_LOCKED',
                details=f'Account {username} automatically locked after {attempts} failed attempts'
            )
        
        return attempts
    
    @staticmethod
    def clear_failed_attempts(username):
        """Clear failed attempts after successful login"""
        cache_key = UserLoginSecurity.get_login_cache_key(username, 'failed')
        cache.delete(cache_key)
    
    @staticmethod
    def log_successful_login(user, ip_address, user_agent=''):
        """Log successful login"""
        try:
            LoginAttempt = get_login_attempt_model()
            LoginAttempt.objects.create(
                username=user.username,
                ip_address=ip_address,
                success=True,
                user_agent=user_agent[:500]
            )
            
            # Update user's last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            log_security_event(
                'LOGIN_SUCCESS',
                user=user,
                ip_address=ip_address,
                details=f'User {user.username} logged in successfully'
            )
            
        except Exception as e:
            logger.error(f"Failed to log successful login: {e}")
    
    @staticmethod
    def get_suspicious_ips(hours=24):
        """Get IPs with suspicious login activity"""
        LoginAttempt = get_login_attempt_model()
        cutoff = timezone.now() - timedelta(hours=hours)
        return (LoginAttempt.objects
                .filter(timestamp__gte=cutoff, success=False)
                .values('ip_address')
                .annotate(failures=models.Count('id'))
                .filter(failures__gte=10)
                .order_by('-failures'))
    
    @staticmethod
    def is_ip_rate_limited(ip_address, limit=10, window_minutes=15):
        """Check if IP is rate limited"""
        cache_key = UserLoginSecurity.get_login_cache_key(ip_address, 'ip_rate')
        attempts = cache.get(cache_key, 0)
        
        if attempts >= limit:
            return True
        
        # Increment attempts
        cache.set(cache_key, attempts + 1, timeout=window_minutes * 60)
        return False


class SessionSecurity:
    """Enhanced session security manager"""
    
    @staticmethod
    def validate_session_security(request):
        """Validate session security constraints"""
        if not request.user.is_authenticated:
            return True
        
        # Check for session hijacking indicators
        session_ip = request.session.get('login_ip')
        current_ip = get_client_ip(request)
        
        if session_ip and session_ip != current_ip:
            log_security_event(
                'SESSION_IP_MISMATCH',
                user=request.user,
                ip_address=current_ip,
                details=f'Session IP: {session_ip}, Current IP: {current_ip}'
            )
            # For now, just log - in production you might want to logout
        
        # Check session age
        login_time = request.session.get('login_time')
        if login_time:
            login_datetime = datetime.fromisoformat(login_time)
            if (timezone.now() - login_datetime).total_seconds() > settings.SESSION_COOKIE_AGE:
                return False
        
        return True
    
    @staticmethod
    def setup_secure_session(request, user):
        """Setup secure session after login"""
        request.session['login_ip'] = get_client_ip(request)
        request.session['login_time'] = timezone.now().isoformat()
        request.session['user_id'] = str(user.id)  # Convert UUID to string
        request.session.cycle_key()  # Generate new session key


@receiver(user_logged_in)
def handle_successful_login(sender, request, user, **kwargs):
    """Handle successful login events"""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Clear failed attempts
    UserLoginSecurity.clear_failed_attempts(user.username)
    
    # Log successful login
    UserLoginSecurity.log_successful_login(user, ip_address, user_agent)
    
    # Setup secure session
    SessionSecurity.setup_secure_session(request, user)


@receiver(user_login_failed)
def handle_failed_login(sender, credentials, request, **kwargs):
    """Handle failed login events"""
    username = credentials.get('username', 'unknown')
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Check if IP is rate limited
    if UserLoginSecurity.is_ip_rate_limited(ip_address):
        log_security_event(
            'IP_RATE_LIMITED',
            ip_address=ip_address,
            details=f'IP {ip_address} rate limited'
        )
        return
    
    # Increment failed attempts
    attempts = UserLoginSecurity.increment_failed_attempts(
        username, ip_address, user_agent, 'Invalid credentials'
    )
    
    log_security_event(
        'LOGIN_FAILED',
        ip_address=ip_address,
        details=f'Failed login for {username} (attempt {attempts})'
    )


class PasswordStrengthValidator:
    """Enhanced password strength validation"""
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password meets security requirements"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter.")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter.")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number.")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character.")
        
        # Check for common patterns
        common_patterns = ['123', 'abc', 'password', 'admin', 'qwerty']
        if any(pattern in password.lower() for pattern in common_patterns):
            errors.append("Password contains common patterns and is not secure.")
        
        return errors
    
    @staticmethod
    def suggest_strong_password():
        """Generate a strong password suggestion"""
        import secrets
        import string
        
        # Generate a secure random password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        # Ensure it meets requirements
        while not PasswordStrengthValidator.validate_password_strength(password) == []:
            password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        return password
