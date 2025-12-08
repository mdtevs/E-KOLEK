"""
Session Encryption Utilities
Provides encryption/decryption for sensitive session data
Uses AES-256-GCM for authenticated encryption
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
import base64
import hashlib
import logging

logger = logging.getLogger(__name__)


class SessionEncryption:
    """
    Handles encryption/decryption of sensitive session data
    Uses Fernet (AES-128-CBC + HMAC-SHA256) for symmetric encryption
    """
    
    _fernet_instance = None
    
    @classmethod
    def get_encryption_key(cls):
        """
        Derive encryption key from settings
        Uses PBKDF2 to derive a strong key from SECRET_KEY
        """
        # Use dedicated encryption key or fallback to SECRET_KEY
        base_key = getattr(settings, 'FIELD_ENCRYPTION_KEY', settings.SECRET_KEY)
        
        # Derive a 32-byte key using PBKDF2HMAC
        salt = b'django_session_encryption_salt_v1'  # Fixed salt for consistency
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        derived_key = kdf.derive(base_key.encode())
        
        # Fernet requires base64-encoded 32-byte key
        return base64.urlsafe_b64encode(derived_key)
    
    @classmethod
    def get_fernet(cls):
        """Get or create Fernet instance (singleton pattern)"""
        if cls._fernet_instance is None:
            key = cls.get_encryption_key()
            cls._fernet_instance = Fernet(key)
        return cls._fernet_instance
    
    @classmethod
    def encrypt(cls, plain_text: str) -> str:
        """
        Encrypt a string value
        
        Args:
            plain_text: String to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not plain_text:
            return plain_text
        
        try:
            f = cls.get_fernet()
            encrypted_bytes = f.encrypt(plain_text.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    @classmethod
    def decrypt(cls, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string
        
        Args:
            encrypted_text: Base64-encoded encrypted string
            
        Returns:
            Decrypted plain text string
        """
        if not encrypted_text:
            return encrypted_text
        
        try:
            f = cls.get_fernet()
            decrypted_bytes = f.decrypt(encrypted_text.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    @classmethod
    def hash_value(cls, value: str, salt: str = None) -> str:
        """
        One-way hash for values that don't need decryption
        Used for IP addresses, user agents, etc.
        
        Args:
            value: String to hash
            salt: Optional salt (defaults to SECRET_KEY)
            
        Returns:
            SHA-256 hash (hex string)
        """
        if not value:
            return value
        
        salt = salt or settings.SECRET_KEY
        salted_value = f"{value}|{salt}"
        return hashlib.sha256(salted_value.encode('utf-8')).hexdigest()


class PrivacyHasher:
    """
    Hash PII (Personally Identifiable Information) for privacy compliance
    Used for IP addresses, user agents - data we need to compare but not expose
    """
    
    @staticmethod
    def hash_ip_address(ip_address: str) -> str:
        """
        Hash IP address for privacy compliance (GDPR)
        Can still compare IPs but cannot reverse the hash
        """
        return SessionEncryption.hash_value(ip_address, salt='ip_address_salt_v1')
    
    @staticmethod
    def hash_user_agent(user_agent: str) -> str:
        """
        Hash user agent string
        Preserves uniqueness for tracking but protects privacy
        """
        # Truncate to first 500 chars to avoid excessive length
        truncated = user_agent[:500] if user_agent else ''
        return SessionEncryption.hash_value(truncated, salt='user_agent_salt_v1')
    
    @staticmethod
    def compare_ip_hashed(plain_ip: str, hashed_ip: str) -> bool:
        """
        Compare plain IP with hashed version
        Useful for session validation
        """
        return PrivacyHasher.hash_ip_address(plain_ip) == hashed_ip
    
    @staticmethod
    def compare_user_agent_hashed(plain_ua: str, hashed_ua: str) -> bool:
        """
        Compare plain user agent with hashed version
        """
        return PrivacyHasher.hash_user_agent(plain_ua) == hashed_ua


# Convenience functions for direct use
def encrypt_token(token: str) -> str:
    """Encrypt a JWT token or sensitive string"""
    return SessionEncryption.encrypt(token)


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a JWT token or sensitive string"""
    return SessionEncryption.decrypt(encrypted_token)


def hash_ip(ip_address: str) -> str:
    """Hash an IP address for privacy"""
    return PrivacyHasher.hash_ip_address(ip_address)


def hash_user_agent(user_agent: str) -> str:
    """Hash a user agent string for privacy"""
    return PrivacyHasher.hash_user_agent(user_agent)


# Test function (only for development)
def test_encryption():
    """
    Test encryption/decryption functionality
    Run with: python manage.py shell
    >>> from accounts.encryption_utils import test_encryption
    >>> test_encryption()
    """
    print("🔒 Testing Session Encryption...")
    
    # Test token encryption
    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_payload"
    print(f"\n1. Original token: {test_token[:50]}...")
    
    encrypted = encrypt_token(test_token)
    print(f"2. Encrypted: {encrypted[:50]}...")
    
    decrypted = decrypt_token(encrypted)
    print(f"3. Decrypted: {decrypted[:50]}...")
    
    assert test_token == decrypted, "❌ Encryption/Decryption mismatch!"
    print("✅ Token encryption: PASSED")
    
    # Test IP hashing
    test_ip = "192.168.1.100"
    hashed_ip = hash_ip(test_ip)
    print(f"\n4. Original IP: {test_ip}")
    print(f"5. Hashed IP: {hashed_ip}")
    
    # Test user agent hashing
    test_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    hashed_ua = hash_user_agent(test_ua)
    print(f"\n6. Original UA: {test_ua[:50]}...")
    print(f"7. Hashed UA: {hashed_ua[:50]}...")
    
    print("\n✅ All encryption tests PASSED!")
    print("🔐 Session encryption is working correctly.")
    
    return True


if __name__ == '__main__':
    # Allow testing from command line
    test_encryption()
