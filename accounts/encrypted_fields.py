"""
Custom Encrypted Model Fields for Django
Uses Fernet (AES-128-CBC + HMAC-SHA256) symmetric encryption

These fields transparently encrypt/decrypt data:
- Data is encrypted before saving to database
- Data is decrypted when loading from database
- Application code works with plain text (transparent encryption)
"""

from django.db import models
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class EncryptedTextField(models.TextField):
    """
    TextField that automatically encrypts/decrypts data
    
    Usage:
        class MyModel(models.Model):
            secret_data = EncryptedTextField()
    
    The field works like a normal TextField but data is encrypted in database.
    """
    
    description = "Encrypted text field using Fernet (AES-128-CBC + HMAC-SHA256)"
    
    def __init__(self, *args, **kwargs):
        """Initialize with TextField properties"""
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        """
        Called when loading data from database
        Decrypts the encrypted value
        """
        if value is None:
            return value
        
        try:
            # Import here to avoid circular imports
            from accounts.encryption_utils import decrypt_token
            return decrypt_token(value)
        except Exception as e:
            # If decryption fails, log error and return as-is
            # This allows migration compatibility (plain text -> encrypted transition)
            logger.warning(f"Decryption failed for EncryptedTextField: {e}")
            return value
    
    def to_python(self, value):
        """
        Called during deserialization and cleaning
        Converts value to Python type
        """
        if isinstance(value, str) or value is None:
            return value
        return str(value)
    
    def get_prep_value(self, value):
        """
        Called before saving to database
        Encrypts the plain text value
        """
        if value is None or value == '':
            return value
        
        try:
            # Import here to avoid circular imports
            from accounts.encryption_utils import encrypt_token
            return encrypt_token(str(value))
        except Exception as e:
            logger.error(f"Encryption failed for EncryptedTextField: {e}")
            raise ValidationError(f"Encryption failed: {e}")
    
    def deconstruct(self):
        """
        Required for migrations
        Returns information about the field for migration serialization
        """
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs


class EncryptedCharField(models.CharField):
    """
    CharField that automatically encrypts/decrypts data
    
    IMPORTANT: max_length should be set to accommodate encrypted text,
    which is approximately 4x the length of plain text.
    
    Usage:
        class MyModel(models.Model):
            secret_code = EncryptedCharField(max_length=500)
            # If plain text is max 100 chars, use max_length=500 for encrypted
    """
    
    description = "Encrypted char field using Fernet (AES-128-CBC + HMAC-SHA256)"
    
    def __init__(self, *args, **kwargs):
        """
        Initialize with CharField properties
        Warn if max_length might be too small
        """
        max_length = kwargs.get('max_length')
        if max_length and max_length < 200:
            logger.warning(
                f"EncryptedCharField max_length={max_length} might be too small. "
                f"Encrypted text is ~4x longer than plain text. "
                f"Consider using max_length >= 200."
            )
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        """
        Called when loading data from database
        Decrypts the encrypted value
        """
        if value is None:
            return value
        
        try:
            from accounts.encryption_utils import decrypt_token
            return decrypt_token(value)
        except Exception as e:
            logger.warning(f"Decryption failed for EncryptedCharField: {e}")
            return value
    
    def to_python(self, value):
        """
        Called during deserialization and cleaning
        Converts value to Python type
        """
        if isinstance(value, str) or value is None:
            return value
        return str(value)
    
    def get_prep_value(self, value):
        """
        Called before saving to database
        Encrypts the plain text value and checks length
        """
        if value is None or value == '':
            return value
        
        try:
            from accounts.encryption_utils import encrypt_token
            encrypted = encrypt_token(str(value))
            
            # Check if encrypted value exceeds max_length
            if hasattr(self, 'max_length') and self.max_length:
                if len(encrypted) > self.max_length:
                    raise ValidationError(
                        f"Encrypted value length ({len(encrypted)}) exceeds "
                        f"max_length ({self.max_length}). "
                        f"Original value length: {len(str(value))}. "
                        f"Consider increasing max_length to at least {len(encrypted) + 50}."
                    )
            
            return encrypted
        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.error(f"Encryption failed for EncryptedCharField: {e}")
            raise ValidationError(f"Encryption failed: {e}")
    
    def deconstruct(self):
        """
        Required for migrations
        Returns information about the field for migration serialization
        """
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs


# Utility functions for manual encryption/decryption
# Use these if you need to encrypt/decrypt outside of model fields

def encrypt_field_value(value: str) -> str:
    """
    Manually encrypt a value (same as field encryption)
    
    Usage:
        encrypted_token = encrypt_field_value("my_secret_token")
    """
    from accounts.encryption_utils import encrypt_token
    return encrypt_token(value)


def decrypt_field_value(encrypted_value: str) -> str:
    """
    Manually decrypt a value (same as field decryption)
    
    Usage:
        plain_token = decrypt_field_value("gAAAAAB...")
    """
    from accounts.encryption_utils import decrypt_token
    return decrypt_token(encrypted_value)


# Helper function to check if a value is encrypted
def is_encrypted(value: str) -> bool:
    """
    Check if a string value appears to be encrypted (Fernet format)
    
    Fernet encrypted values start with "gAAAAA" in base64
    
    Returns:
        True if value appears to be encrypted
        False otherwise
    """
    if not value or not isinstance(value, str):
        return False
    
    # Fernet encrypted values start with "gAAAAA" when base64 encoded
    # This is because Fernet prepends version byte (0x80) which encodes to "gA"
    return value.startswith('gAAAAA') and len(value) > 50


# Example usage and testing
if __name__ == '__main__':
    print("EncryptedTextField and EncryptedCharField are ready to use!")
    print("\nUsage in models:")
    print("""
    from accounts.encrypted_fields import EncryptedTextField, EncryptedCharField
    
    class MyModel(models.Model):
        # For long text (no length limit)
        secret_token = EncryptedTextField()
        
        # For short text (with max_length)
        secret_code = EncryptedCharField(max_length=500)
        
        # Data is automatically encrypted on save
        # Data is automatically decrypted on load
    """)
